# Spec: arch/deepen-modules

## Goal

Deepen kitchen-sink modules into deep modules (small interface, large implementation). Behaviour and public APIs must stay identical.

## Requirements

1. **P1 WebOps** — DONE
   - Extract Archive Author orchestration (job spawn/resume/stop/list/plan) out of `WebOperationsMixin` into a dedicated ops module; Mixin delegates.
   - Web task pause/resume/delete/submit/retry control: prefer `WebUITaskManager`; remove dead duplicate fallbacks from Mixin where manager is always wired; move remaining transfer-IO helpers used only for task control into the manager if still on Mixin.
2. **P2 TransferStore** — DONE
   - Split implementation by aggregate into internal modules under `module/persistence/`; keep `TransferStore` as the public facade with the same method signatures.
3. **P3 WebUiServer** — DONE
   - Split HTTP handlers by API domain into modules; `WebUiServer` remains the HTTP shell; no REST path/JSON field changes.
4. **P4 Facade** — DONE
   - Thin `TelegramRestrictedMediaDownloader` / bot host by delegating remaining business to existing services; update CONTEXT + CONTEXT-MAP.
   - Outcome: facade already mostly mixins + `composition_root` + service delegation; remaining body is download-task orchestration / Bot UX glue (no heroic move). Docs updated.

## Non-goals

- Line-count hard caps; pure package renames; changing Docker/assets generation; frontend rewrite; new domain terminology unless a service name enters ubiquitous language.

## Test seams

Existing unit tests under `unit_tests/` for archive_author, web_task_*, transfer_store_*, webui_*, downloader_transfer_*.
