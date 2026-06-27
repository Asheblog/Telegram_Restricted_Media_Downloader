# Automate local runtime maintenance

TRMD keeps transfer runtime state in SQLite and writes local application logs. Long-running WebUI deployments should not require operators to periodically prune files or run SQLite maintenance by hand.

SQLite remains the runtime state store. `TransferStore` owns read-performance indexes, WAL connection pragmas, periodic WAL checkpointing, `PRAGMA optimize`, and threshold-based `VACUUM` so callers keep using the same store interface. File logs rotate daily and old rotated files are removed after three days.

This is a direct replacement for the previous single large log file and manual SQLite cleanup expectation. No migration is required, and persisted Transfer Tasks, Transfer Items, events, download success records, and live watches are not deleted by this maintenance.
