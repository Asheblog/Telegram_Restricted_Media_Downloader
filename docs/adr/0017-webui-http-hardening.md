# ADR-0017: WebUI HTTP 层安全加固（渗透测试 F-01 ~ F-07 修复）

**决策日期**: 2026-09 | **最后更新**: 2026-09-30 | **状态**: ✅ 已采纳

---

## Context

2026-09-30 的授权渗透测试（报告 2026-09-30-PT-TRMD-001，目标 `tgbot.evo.iops.pp.ua`）在
`openresty → 手写 Python http.server` 这套 WebUI 上确认了 7 项问题：

| 编号 | 级别 | 问题 |
| ---- | ---- | ---- |
| F-01 | Medium | `POST /api/auth/login` 收到非对象 / 非法 JSON 时未捕获异常逃逸到 `socketserver` → nginx 502 或 TCP 连接重置，并把 stderr 堆栈灌进日志 |
| F-02 | Low | HSTS 只出现在端口 80 的明文 301 上，HTTPS 响应缺失 → 按 RFC 6797 §7.2 浏览器忽略，策略从未生效 |
| F-03 | Low | 缺失 `X-Frame-Options` / CSP / `X-Content-Type-Options` / `Referrer-Policy` → 登录页可被 iframe 嵌套（点击劫持） |
| F-04 | Low | `trmd_session` 有 `HttpOnly; SameSite=Lax` 但缺 `Secure` |
| F-05 | Low | 登录端点无速率限制 / 锁定 / 反自动化（180 组喷洒 0 拦截） |
| F-06 | Info | `POST /api/auth/logout` 未授权可达（200），且无 CSRF 防护 → 跨站登出 |
| F-07 | Info | `404 not_found` / `401 auth_required` 差分构成路由预言机；`OPTIONS`/`HEAD` 直接回吐 Python http.server 指纹 |

约束：修复必须在**应用层**完成（本仓库不含 nginx 配置），且不能破坏两类既有场景——
本地 `127.0.0.1` 明文开发登录，以及反向代理后统一暴露的远程部署。

## Decision

### 1. 统一异常边界（F-01）

- `Handler._run(route)` 包住每个 HTTP 方法的路由；`WebUiApiError` → 结构化 4xx，
  其余异常 → `500 {"error_code": "internal_error"}` 且不把异常文本回给客户端。
- `_read_json()` 成为唯一 JSON 入口：`Content-Length` 非法 → 400；超过
  `MAX_JSON_BODY_BYTES`（8 MiB，读之前判断）→ 413；非法 JSON / 非 UTF-8 → 400
  `invalid_json_body`；默认要求 JSON 对象，只有转发监听备份导入
  （`POST /api/watches/forward/import`，历史格式支持纯数组）显式传
  `expect_object=False`。
- 响应写出全部走 `_safe_write` / `_begin_response`，客户端半死连接只关闭连接，
  不再产生 stderr 堆栈。

### 2. 响应头（F-02 / F-03）

- `Handler.end_headers` 给**所有**响应（含 401/404/5xx 与 stdlib 错误）追加：
  `X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、
  `Content-Security-Policy: frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'`、
  `Referrer-Policy: no-referrer`、`Permissions-Policy: geolocation=(), camera=(), microphone=()`。
  CSP 刻意不设 `default-src` / `script-src`：桌面端、移动端与登录页都把脚本与样式内联在 HTML 里。
- HSTS 仅在「确认走 HTTPS」时下发：`X-Forwarded-Proto: https` 或直连 TLS；
  非 loopback 监听（`requires_auth`）+ 反代跳头视为生产姿态也下发。
  明文响应不放 HSTS（RFC 6797 §7.2 浏览器本就忽略，避免误报与噪音）。

### 3. 会话 Cookie（F-04）

`Set-Cookie` 的 `Secure` 由 `security.cookie_secure_required()` 决定，顺序为：

1. `TRMD_WEB_COOKIE_SECURE` 显式开关（`1/true/on…` 或 `0/false/off…`）；
2. `X-Forwarded-Proto: https` → 加；`http` → 不加（信任反代的显式声明）；
3. 直连 TLS → 加；
4. 绑在非 loopback 地址（按 ADR-0003 属生产部署）→ 加；
5. 否则看是否带反代跳头（`X-Forwarded-For` / `X-Real-IP` / `Forwarded` / `X-Forwarded-Host`）→ 加。

本地 `127.0.0.1` 明文直连不加 `Secure`，否则浏览器会丢弃 Cookie、登录直接坏掉。
登出用的清除 Cookie 使用同一判定。

### 4. 鉴权边界与 CSRF（F-06 / F-07）

- 公开白名单精确到「方法 + 路径」，只剩 `POST /api/auth/login`。
  `GET /api/auth/login`、`GET/POST /api/auth/logout` 等未授权访问一律 `401 auth_required`，
  404/401 差分预言机消失。
- `POST /api/auth/logout` 移入鉴权门之后：必须有有效会话，未授权返回 401（不再是 200）。
- 所有状态变更方法（POST/PUT/PATCH/DELETE）在鉴权前做同源校验：
  带 `Origin` / `Referer` 且与 `Host`（或 `X-Forwarded-Host`）不同源 → `403 cross_origin_forbidden`
  （默认端口 80/443 归一化比较）。不带这两个头的非浏览器客户端（curl、脚本、测试）放行。
  两种刻意的宽松处理，避免把正常登录 403 掉：
  - `Host` 被反代改写成回环 / 内网地址（`proxy_pass` 且未 `proxy_set_header Host $host`
    时 nginx 的默认行为）时无法判断真实站点 → 放行；
  - `Origin: null`（沙箱 iframe）按跨站处理。

  会话 Cookie 的 `SameSite=Lax` 仍是第一道防线：跨站表单 POST 根本带不上会话。
  特殊反代或排障可用 `TRMD_WEB_CSRF_ORIGIN_CHECK=off` 关闭该校验。

### 5. 登录限流（F-05）

`security.LoginThrottle`：按「客户端 IP + 用户名」双维度统计**失败**尝试，
默认 5 次 / 60s 窗口，超阈值进入锁定窗口（60s 起，重复触发翻倍，上限 15min，
静默超过上限后 strikes 复位），返回 `429 too_many_attempts` + `Retry-After`，
并写 `diagnostic.warning` 告警。

两条刻意设计：

- **只统计失败尝试**：口令正确时先放行、再清零计数。攻击者无法靠打满失败窗口
  把管理员锁在门外，即不把反爆破做成可用性攻击。
- **不信任 `X-Forwarded-For` 做限流键**：反代是否覆写该头不由本程序控制，
  信任它等于给攻击者「换个头就换桶」的绕过口子。反代部署下所有请求共享同一 IP 桶，
  由「正确口令直通」兜住可用性。

限流是进程内的（重启清零）；多副本或需要跨进程配额时由外层网关 / WAF 承担。

### 6. 指纹与错误页（F-07）

- `Server: trmd-webui`（去掉 `BaseHTTP/0.6 Python/3.x`）。
- 重写 `send_error`：stdlib 的 HTML 错误页换成 JSON，`501` 不回显调用方自选方法名，
  非法请求行也只得到 JSON。
- 新增 `do_OPTIONS` / `do_HEAD` → `405` + `Allow: GET, POST, PUT, PATCH, DELETE`，
  不再走 stdlib 的 `501 Unsupported method`。

### 7. 配置面

新增环境变量（`module/core/enums.py::ENVIRON`）：

| 变量 | 默认 | 作用 |
| ---- | ---- | ---- |
| `TRMD_WEB_COOKIE_SECURE` | 未设（自动判定） | 强制 / 关闭会话 Cookie `Secure` |
| `TRMD_WEB_CSRF_ORIGIN_CHECK` | `on` | `off` 关闭 `Origin`/`Referer` 同源校验 |
| `TRMD_WEB_LOGIN_RATELIMIT` | `on` | `off` 关闭登录限流 |
| `TRMD_WEB_LOGIN_MAX_FAILURES` | `5` | 窗口内允许的失败次数 |
| `TRMD_WEB_LOGIN_WINDOW_SECONDS` | `60` | 失败计数窗口 |
| `TRMD_WEB_LOGIN_LOCKOUT_SECONDS` | `60` | 首次锁定窗口 |
| `TRMD_WEB_LOGIN_MAX_LOCKOUT_SECONDS` | `900` | 退避锁定上限 |

## Consequences

- ✅ F-01 ~ F-07 全部有了代码级修复与回归测试
  （`unit_tests/webui_http_hardening_case.py`）。
- ⚠️ **nginx 侧仍需运维落地**（本仓库不含 nginx 配置，见 `docs/ops/webui-nginx-hardening.md`）：
  TLS vhost `add_header Strict-Transport-Security ... always;`、
  `proxy_set_header X-Forwarded-Proto $scheme;`（让应用能精确判定 HTTPS）、
  默认 server `return 444`（未知 Host 兜底）、`proxy_intercept_errors on`（5xx 统一页面）。
- ⚠️ 明文 HTTP 的非 loopback 部署会拿到 `Secure` Cookie 而被浏览器丢弃：
  应启用 HTTPS，或显式设 `TRMD_WEB_COOKIE_SECURE=0`。两种情况的取舍写进启动日志与文档。
- ⚠️ 同源校验只挡浏览器发起的跨站请求（`Origin`/`Referer`），不是密钥级 CSRF Token；
  会话 Cookie 仍是 `SameSite=Lax`，二者叠加覆盖登出 CSRF 与跨站表单 POST。
- ⚠️ 404/401 在**已认证**状态下仍然不同形（已认证用户本就知道路由是否存在），
  未授权面已完全统一。
