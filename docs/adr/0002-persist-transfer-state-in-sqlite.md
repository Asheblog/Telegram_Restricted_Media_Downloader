# Persist transfer state in SQLite

Transfer Tasks, Transfer Items, and their events are persisted in SQLite. YAML remains suitable for user configuration, but runtime transfer state needs durable querying, retry, audit, and WebUI updates without requiring an external database service.
