# ADR-0003: 远程监听时强制 WebUI 认证

**决策日期**: 2025-06 | **最后更新**: 2026-07-14 | **状态**: ✅ 已采纳

---

## Context

WebUI 可以创建 Telegram 转存任务、修改配置、管理监听规则。当 `TRMD_WEB_HOST` 绑定到非 localhost 地址（如 `0.0.0.0`）时：

- WebUI 暴露在网络上，任何人都能访问
- 无认证的 WebUI 意味着攻击者可以：创建转存任务消耗带宽/存储、修改 Telegram API 配置、读取会话信息
- ttyd 方案有随机密码保护，但 WebUI 替换后需要更明确的认证机制

## Decision

- 使用 WebUI 站内登录页保护 WebUI，登录成功后签发 HttpOnly session cookie
- Session token 采用签名 Cookie：`expiry.nonce.hmac`，HMAC 密钥由 `TRMD_WEB_USERNAME`/`TRMD_WEB_PASSWORD` 派生；服务端不保存 session 表，进程或容器重启后在过期前仍可校验
- 勾选「记住我」时 Cookie `Max-Age` 为 30 天；修改登录密码会使旧签名失效
- 站内登录凭据通过环境变量 `TRMD_WEB_USERNAME` 和 `TRMD_WEB_PASSWORD` 注入
- 当 `TRMD_WEB_HOST` 非 localhost 时，**强制要求**两个凭据都设置，缺少则拒绝启动
- 凭据是部署配置的一部分，由运维人员显式设置，程序绝不生成或日志输出
- 401 API 响应返回 JSON `auth_required`，不得发送 `WWW-Authenticate` challenge，避免浏览器弹出原生登录框
- 遗留 `Authorization: Basic ...` 请求头不再被视为有效登录

## Consequences

- ✅ WebUI 远程访问有基础安全保护
- ✅ 明确的安全门禁：不设置密码 = 无法远程启动
- ✅ 登录体验统一到 WebUI 页面，不再出现浏览器原生登录弹窗
- ✅ 部署简单：环境变量即可，无需额外 OAuth 配置
- ✅ 「记住我」在重启后仍生效，且不依赖落盘 session 文件或 Docker volume
- ⚠️ 登出仅清除浏览器 Cookie；持有旧 cookie 的客户端在过期前仍可通过校验（改密码可立即失效）
- ⚠️ 通过 HTTP 传输时登录凭据仍可能被窃听，建议配合反向代理启用 HTTPS
- ⚠️ 用户名/密码在 docker-compose.yml 中明文存储，需控制文件权限
