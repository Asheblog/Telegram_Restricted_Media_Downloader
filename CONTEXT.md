# Telegram Restricted Media Transfer

This context describes TRMD as a tool for transferring Telegram content that the user is allowed to access, including content that cannot be forwarded natively.

## Language

**Restricted Content Transfer**:
A transfer that gets Telegram content from a source conversation to a target conversation even when Telegram native forwarding is blocked. It may use native forwarding when allowed, but falls back to downloading and re-sending the content.
_Avoid_: Forward bypass, restricted forward, mirror

**PikPak Target**:
The Telegram conversation with the official PikPak bot that receives transferred media so PikPak can ingest it.
_Avoid_: PikPak API, cloud drive target

**Transfer Task**:
A persisted user request to move one or more source messages to a target conversation.
_Avoid_: Download task, forward job

**Transfer Item**:
One source message or media item inside a Transfer Task.
_Avoid_: File task, message job

**Download Success Record**:
A durable record that a source conversation message has already been downloaded successfully, scoped by the source conversation and message identity. Later transfer requests can use it to avoid downloading the same source media again.
_Avoid_: Cache hit, finished file

**Target Profile**:
A named set of target-specific transfer defaults, such as sending media to PikPak as documents and deleting local files after success.
_Avoid_: Preset, mode

**WebUI Credentials**:
Environment-supplied Basic Auth credentials for the visual WebUI. They are required when the server listens on a non-localhost address and are never generated or logged by the application.
_Avoid_: Random ttyd password, public WebUI
