# ADR-0003: 远程监听时强制 WebUI 认证

**决策日期**: 2025-06 | **最后更新**: 2026-07-07 | **状态**: ✅ 已采纳

---

## Context

WebUI 可以创建 Telegram 转存任务、修改配置、管理监听规则。当 `TRMD_WEB_HOST` 绑定到非 localhost 地址（如 `0.0.0.0`）时：

- WebUI 暴露在网络上，任何人都能访问
- 无认证的 WebUI 意味着攻击者可以：创建转存任务消耗带宽/存储、修改 Telegram API 配置、读取会话信息
- ttyd 方案有随机密码保护，但 WebUI 替换后需要更明确的认证机制

## Decision

- 使用 HTTP Basic Auth 保护 WebUI
- 凭据通过环境变量 `TRMD_WEB_USERNAME` 和 `TRMD_WEB_PASSWORD` 注入
- 当 `TRMD_WEB_HOST` 非 localhost 时，**强制要求**两个凭据都设置，缺少则拒绝启动
- 凭据是部署配置的一部分，由运维人员显式设置，程序绝不生成或日志输出

## Consequences

- ✅ WebUI 远程访问有基础安全保护
- ✅ 明确的安全门禁：不设置密码 = 无法远程启动
- ✅ 部署简单：环境变量即可，无需额外证书或 OAuth 配置
- ⚠️ Basic Auth 通过 HTTP 传输时凭据为 Base64 编码（非加密），建议配合反向代理启用 HTTPS
- ⚠️ 用户名/密码在 docker-compose.yml 中明文存储，需控制文件权限
