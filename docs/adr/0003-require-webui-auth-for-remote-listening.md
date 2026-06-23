# Require WebUI auth for remote listening

The visual WebUI uses HTTP Basic Auth from `TRMD_WEB_USERNAME` and `TRMD_WEB_PASSWORD`. Credentials are explicit deployment configuration, not randomly generated runtime output. When `TRMD_WEB_HOST` binds to a non-localhost address, the server refuses to start unless both credentials are set, because the WebUI can create Telegram transfer tasks and must not be exposed unauthenticated.
