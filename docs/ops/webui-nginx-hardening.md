# WebUI 反向代理加固（openresty / nginx）

> 适用版本：v0.2.246+（应用层修复见 [ADR-0017](../adr/0017-webui-http-hardening.md)）
> 背景：2026-09-30 授权渗透测试报告 `2026-09-30-PT-TRMD-001` 的 F-02 / F-07 有一半落在
> nginx 层——TLS vhost 未下发 HSTS、未知 Host 回落到默认站点、5xx 未统一拦截。
> 应用层已能下发安全头，但**证书终止、明文跳转与 vhost 兜底只能在 nginx 做**。

## 1. 推荐配置

```nginx
# ---------- ① 未知 Host 兜底：不暴露默认站点 ----------
server {
    listen      80  default_server;
    listen      [::]:80 default_server;
    listen      443 ssl default_server;      # 需为该 vhost 准备证书；无证书时删掉本行
    server_name _;
    return 444;                              # 直接断开，不再返回 nginx 默认 404 页
}

# ---------- ② 明文入口：只做跳转 ----------
server {
    listen      80;
    server_name tgbot.example.com;
    return 301 https://$host$request_uri;
}

# ---------- ③ TLS 入口：真正的加固点 ----------
server {
    listen      443 ssl;
    http2       on;
    server_name tgbot.example.com;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # HSTS 必须在 HTTPS 响应上下发；always 保证 4xx/5xx 也带。
    # 明文端口上的 HSTS 会被浏览器忽略（RFC 6797 §7.2），不要指望它生效。
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 应用层已下发同名头；这里再兜一层，覆盖 nginx 自身生成的响应（502 / 504 / 444 之外的错误页）。
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Content-Security-Policy "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'" always;
    add_header Referrer-Policy "no-referrer" always;

    client_max_body_size 8m;                 # 与 server.MAX_JSON_BODY_BYTES 对齐

    location / {
        proxy_pass         http://127.0.0.1:2921;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;   # 应用据此判定 HTTPS → HSTS + Secure Cookie
        proxy_set_header   X-Forwarded-Host  $http_host; # 含端口，供应用的跨站来源校验比对

        proxy_intercept_errors on;                    # 后端 5xx 统一走 nginx 错误页
        error_page 502 503 504 /50x.html;
    }

    location = /50x.html { root /usr/share/nginx/html; internal; }
}
```

要点：

- `proxy_set_header X-Forwarded-Proto $scheme;` 是应用层 HTTPS 判定的**首选信号**：
  有了它，HSTS 与 `Secure` Cookie 的判定不再依赖「非 loopback 监听」这种间接推断。
- `proxy_set_header Host $host;`（以及可选的 `X-Forwarded-Host $http_host`）决定应用的跨站来源校验能否
  正确判断「本站」。`proxy_pass` 缺省时 nginx 会把 `Host` 写成上游地址（如 `127.0.0.1:2921`）；
  应用检测到回环 / 内网 `Host` 时会放行而不是 403（避免把正常登录打死），但这会削弱同源校验。
  `$host` 不含端口，而浏览器在外部端口非 80/443 时 `Origin` 带端口——应用对「Host 无端口」
  的情况只比主机名，所以 `Host $host` 即可；若要用端口严格比对，转发 `X-Forwarded-Host $http_host`
  （含端口）。若你的反代只能用内网域名当 Host，可显式设 `TRMD_WEB_CSRF_ORIGIN_CHECK=off`。
- 应用只采信来自回环 / 私网对端的 `X-Forwarded-*`：nginx 与应用在同一主机或同一容器网络时天然满足；
  若反代部署在公网地址上，请改用 nginx 层 `add_header` 兜 HSTS（模板已含），Cookie `Secure`
  仍由非 loopback 监听判定拿到。
- `add_header` 默认继承规则：子级（`location`）一旦自己写了 `add_header`，
  父级的全部失效。上面 `location /` 不写 `add_header`，因此继承 server 级。
- 应用与 nginx 会下发同名安全头（值一致，重复无害）。若要求响应里只留一份，
  在 `location` 内加 `proxy_hide_header X-Frame-Options;` 等隐藏上游同名头。
- 若 WebUI 直接对外（不经反代）且非 loopback，应用会默认给 Cookie 加 `Secure`；
  明文 HTTP 部署必须显式设 `TRMD_WEB_COOKIE_SECURE=0`，否则浏览器会丢弃会话 Cookie。

## 2. 验证清单

```bash
HOST=tgbot.example.com

# F-02：HTTPS 响应必须带 HSTS（含 API 与错误响应）
curl -sS -D - -o /dev/null https://$HOST/                | grep -i strict-transport-security
curl -sS -D - -o /dev/null https://$HOST/api/auth/login  | grep -i strict-transport-security

# F-03：防嵌套 / 防嗅探
curl -sS -D - -o /dev/null https://$HOST/ | grep -iE 'x-frame-options|content-security-policy|x-content-type-options'

# F-04：登录 Cookie 带 Secure（配合正确口令；不要在真实环境喷洒弱口令）
curl -sS -D - -o /dev/null -X POST -H 'Content-Type: application/json' \
  --data-binary '{"username":"admin","password":"<正确口令>"}' \
  https://$HOST/api/auth/login | grep -i set-cookie

# F-07：未知 Host 不再回落默认站点
curl -sS -o /dev/null -w '%{http_code}\n' -H 'Host: unknown.invalid' https://$HOST/

# F-01：畸形 JSON 必须是 400，不是 502
curl -sS -o - -w '\nHTTP %{http_code}\n' -X POST -H 'Content-Type: application/json' \
  --data-binary '[]' https://$HOST/api/auth/login

# F-07：不再回吐 Python http.server 指纹
curl -sS -D - -o /dev/null -X OPTIONS https://$HOST/api/auth/login | grep -i '^server'

# 限流：连续失败应出现 429 + Retry-After（默认 5 次 / 60s 起，指数退避）
for i in $(seq 1 7); do
  curl -sS -o /dev/null -w "$i -> %{http_code}\n" -X POST -H 'Content-Type: application/json' \
    --data-binary '{"username":"admin","password":"wrong"}' https://$HOST/api/auth/login
done
```

> 验证限流请在授权范围内进行，并在结束后确认正常口令仍可登录（限流只拦失败尝试）。
