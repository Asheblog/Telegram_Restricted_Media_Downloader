# Telegram Restricted Media Transfer

This context describes TRMD as a tool for transferring Telegram content that the user is allowed to access, including content that cannot be forwarded natively.

## Language

**Restricted Content Transfer**:
A transfer that gets Telegram content from a source conversation to a target conversation even when Telegram native forwarding is blocked. It may use native forwarding when allowed, but falls back to downloading and re-sending the content.
_Avoid_: Forward bypass, restricted forward, mirror

**PikPak Target**:
The Telegram conversation with the official PikPak bot that receives transferred media so PikPak can ingest it.
_Avoid_: PikPak API, cloud drive target

**PikPak Archive**:
A target-side organization step that places media received by the PikPak Target into a durable PikPak folder after the transfer reaches PikPak.
_Avoid_: Local download folder, bot chat folder

**Transfer Task**:
A persisted user request to move one or more source messages to a target conversation.
_Avoid_: Download task, forward job

**Transfer Item**:
One source message or media item inside a Transfer Task.
_Avoid_: File task, message job

**Transfer Progress**:
The set of Transfer Items in a Transfer Task that have reached a final outcome and can be skipped when the same Transfer Task continues later.
_Avoid_: Chapter cursor, runtime offset

**Download Success Record**:
A durable record that a source conversation message has already been downloaded successfully, scoped by the source conversation and message identity. Later transfer requests can use it to avoid downloading the same source media again.
_Avoid_: Cache hit, finished file

**Source Channel Folder**:
A filesystem-safe folder name derived from the source Telegram conversation so transferred media from the same source can be grouped together.
_Avoid_: Target folder, chat title cache

**Target Profile**:
A named set of target-specific transfer defaults, such as sending media to PikPak as documents and deleting local files after success.
_Avoid_: Preset, mode

**Target Size Limit**:
A target-specific maximum media size for a Transfer Item. Transfer Items above this limit are rejected before expensive transfer work for that target begins.
_Avoid_: Upload cap, file size check

**Live Transfer Watch**:
A sustained rule that watches a source Telegram conversation for new messages and triggers a transfer or forwarding action when matching messages arrive.
_Avoid_: Listen job, bot listener

**Discussion Reply Inclusion**:
An optional transfer behavior that includes Telegram discussion replies attached to a source message in the same transfer or forwarding action.
_Avoid_: Comment scraping, reply mirroring

**WebUI Credentials**:
Environment-supplied Basic Auth credentials for the visual WebUI. They are required when the server listens on a non-localhost address and are never generated or logged by the application.
_Avoid_: Random ttyd password, public WebUI
