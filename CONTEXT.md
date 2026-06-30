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
A target-side organization step that ensures the Source Channel Folder exists and places media received by the PikPak Target into that durable PikPak folder after the transfer reaches PikPak. When enabled for a PikPak Target, the archive must complete before the Transfer Item is treated as successful.
_Avoid_: Local download folder, bot chat folder

**PikPak Ingest Folder**:
The PikPak folder where the PikPak Target initially stores media before a PikPak Archive moves it into a Source Channel Folder.
_Avoid_: Archive root, source channel folder

**PikPak Ingest Confirmation**:
A reply from the PikPak Target showing that PikPak has accepted and saved a transferred media item. Telegram delivery to the PikPak Target is not enough to make a transfer successful.
_Avoid_: Forward success, copy success

**Transfer Task**:
A persisted user request to move one or more source messages to a target conversation.
_Avoid_: Download task, forward job

**Transfer Item**:
One source message or media item inside a Transfer Task.
_Avoid_: File task, message job

**Transfer Progress**:
The set of Transfer Items in a Transfer Task that have reached a final outcome and can be skipped when the same Transfer Task continues later.
_Avoid_: Chapter cursor, runtime offset

**Live Transfer Status**:
A user-visible progress message for an active Restricted Content Transfer, especially when a Live Transfer Watch falls back to downloading and uploading media. It shows download, upload, target-send, and failure phases while the work is still running.
_Avoid_: Container log, final notice, PikPak confirmation

**Transfer Task Pause**:
A user-requested stop point for a Transfer Task that prevents the next Transfer Item from starting while preserving already completed Transfer Progress.
_Avoid_: Cancel task, delete task, kill transfer

**Failed Item Retry**:
A user-requested continuation of a Transfer Task that makes failed Transfer Items eligible to run again while keeping successful and skipped Transfer Items as completed Transfer Progress.
_Avoid_: Restart task, rerun all, clear history

**Automatic Transfer Range**:
A Transfer Task range inferred from the earliest and latest source conversation messages that the current account can access when the user provides a source conversation link without explicit message IDs.
_Avoid_: Auto dump, guessed range

**Download Success Record**:
A durable record that a source conversation message has already been downloaded successfully, scoped by the source conversation and message identity. Later transfer requests can use it to avoid downloading the same source media again.
_Avoid_: Cache hit, finished file

**Downloaded Media Filename**:
A filesystem-safe filename for downloaded media and PikPak Archive targets. When the source Telegram message has a caption, text, or web preview title, that readable Source Message Title is preferred over Telegram media IDs or generated English filenames; the source message ID remains in the filename to avoid collisions.
_Avoid_: Temp cache name, random media ID

**Source Channel Folder**:
A filesystem-safe folder name derived from the source Telegram conversation so transferred media from the same source can be grouped together.
_Avoid_: Target folder, chat title cache

**Target Profile**:
A named set of target-specific transfer defaults, such as sending media to PikPak as documents and deleting local files after success.
_Avoid_: Preset, mode

**Target Size Limit**:
A target-specific maximum media size for a Transfer Item. Transfer Items above this limit are skipped before expensive transfer work for that target begins because the selected target cannot accept them; this is not a transfer failure.
_Avoid_: Upload cap, file size check, upload failure

**Live Transfer Watch**:
A sustained rule that watches a source Telegram conversation for new messages and triggers a transfer or forwarding action when matching messages arrive.
_Avoid_: Listen job, bot listener

**Discussion Reply Inclusion**:
An optional transfer behavior that includes Telegram discussion replies attached to a source message in the same transfer or forwarding action.
_Avoid_: Comment scraping, reply mirroring

**WebUI Credentials**:
Environment-supplied Basic Auth credentials for the visual WebUI. They are required when the server listens on a non-localhost address and are never generated or logged by the application.
_Avoid_: Random ttyd password, public WebUI
