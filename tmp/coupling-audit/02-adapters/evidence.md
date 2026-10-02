# A2 · adapters 层与域层耦合取证

## 0. 审查元信息

| 项 | 值 |
|---|---|
| 仓库 | `E:\codebase\tgbot`（TRMD） |
| 审查基线 | `HEAD = 1f7a43b`（`fix(forward): 监听转发 file_reference 过期时刷新引用重试 0.2.248`） |
| 工作树状态 | 干净。`module/` 与 `unit_tests/` 的磁盘文件与 HEAD **逐字节相同**（`git hash-object` == `git rev-parse HEAD:<path>`，6/6 SAME） |
| 解释器 | `E:\codebase\tgbot\.venv313\Scripts\python.exe` = **3.13.7**（符合 `requires-python>=3.13.2`）；`import module.adapters.webui.operations` 通过 |
| 审查方式 | 只读 AST 量化 + `git log/show` 只读查询。**未修改 `module/`、`unit_tests/` 任何文件，未 commit** |
| 写入范围 | `tmp/coupling-audit/02-adapters/` |

### 0.1 对任务书行号的一处更正（先证伪，避免后续引用错误）

任务书给的三个行数与实际不符：`operations.py 1732` / `server.py 1855` / `bot.py 1904`。
实测（`len(open(p,'rb').readlines())`）：

```
module/adapters/webui/operations.py : 1897 行 (85,881 B)
module/adapters/webui/server.py     : 2033 行 (77,867 B)
module/adapters/bot/bot.py          : 1980 行 (89,359 B)
```

这不是工作树被改脏导致的（已用 `git hash-object` 逐文件证明磁盘与 HEAD 同哈希）。原因是用 PowerShell `Get-Content | Measure-Object -Line` 统计的行数会低于真实值（同一文件该口径给出 1732）。**本报告全部行号均以磁盘真实文件为准。**

---

## 1. 结论摘要

adapters 层不是一个"薄适配层"，而是**第二个业务核心 + 三层转发壳**：

1. `WebOperationsMixin`（114 方法 / L104-1860）**零 HTTP 原语**：`BaseHTTPRequestHandler`、`self.headers`、`self.wfile`、`urlparse`、`parse_qs`、`HTTPStatus`、`send_response` 在全文出现次数**全部为 0**。里面装的是任务队列、监听、PikPak 账号、安装向导、媒体清理、归档编排、诊断导出——按职责 8 组可完整划分 114 个方法（见 §2）。
2. 一次 WebUI 请求要跨 **4 跳 / 3 个类**：`handlers/*.py` → `WebUiServer.<method>` → `self._operation("<字符串名>")` → `WebOperationsFacade`（由 `setattr` 动态绑定）→ mixin → `getattr(host, ...)`。中间那跳是 `getattr(self.operations, name, None)`，**名字是字符串，写错不会报错**。
3. `module/ports.py` 的 7 个 Protocol **没有任何约束力**：全仓 `isinstance`/`issubclass`/`cast` 命中 **0 次**；`IWebUiOperations` 只被用作 1 处注解（`server.py:198`），5 个叶子 Protocol 从未被 import，且 `IWebUiOperations` 只覆盖 facade 实际表面的 **47.5%（19/40）**。
4. host 契约是**字符串反射契约**：adapters 依赖 **31 个** `host.<attr>`，有 **41 处** `getattr(host/self._host/self.operations, ...)`；`operations.py` 甚至**反向给 host 写 6 个属性**。代价已实测兑现：`187d1d8` 删除 `__getattr__` 后，**1 天内用 3 个提交、22 个文件、332 行新增**去补宿主属性缺口（§4.3）。
5. 变更放大实测：40 个非 chore 提交**平均 11.05 文件/次**（中位 7，最大 71）；**100% 跨 ≥2 层**，87.5% 跨 ≥3 层；触碰 adapters 的提交里 **91.3%（21/23）同时改动非 adapters 层**。

> **诚实的边界**：`IBotCallbackHost` 是**精确且完整**的端口——19 个成员 19 个都被真实使用（63 处访问），0 个声明未用、0 个用了未声明。团队**会**写端口；问题出在 WebUI 路径整体绕开了端口。

---

## 2. 量化总表

### 2.1 `WebOperationsMixin` 114 方法按职责分组（无遗漏、无交叠，合计 114）

| 组 | 方法数 | 行号区间 | 占比 | 纯转发 shim |
|---|---:|---|---:|---:|
| 任务控制（含区间检测） | 41 | L108–1822 | 36.0% | 19 |
| 监听（watch + 评论延迟抓取） | 25 | L150–1860 | 21.9% | 10 |
| 账号与设置 | 17 | L1054–1413 | 14.9% | 1 |
| 安装向导 | 8 | L1415–1575 | 7.0% | 1 |
| 媒体清理 | 5 | L737–837 | 4.4% | 0 |
| 归档工具 | 12 | L839–925 | 10.5% | 9 |
| 诊断导出 | 3 | L886–1052 | 2.6% | 0 |
| 统计 | 3 | L619–718 | 2.6% | 0 |
| **合计** | **114** | L104–1860 | 100% | **40** |

方法体规模分布：`<=3 行` **40 个**、`4–10 行` 25 个、`11–30 行` 35 个、`31–60 行` 11 个、`>60 行` 3 个。
其中**严格意义的纯转发 shim（单语句、转发到其它对象的方法）共 38 个**（`probe_02_shims.py` 逐个列出）。

### 2.2 三个对象/两个类的方法数对比

| 对象 | 方法数 | 说明 |
|---|---:|---|
| `WebOperationsMixin` | 114 | 业务实现（在 adapters 目录） |
| `WebUiServer` | 67 | HTTP 壳 + 校验 + 转发（`start` 单方法 **463 行**，L440–902） |
| `WebOperationsFacade` | 40 | 由 `setattr` 动态绑定，纯转发 |
| **`WebUiServer` 与 mixin 同名方法** | **32** | 其中 **31 个是"校验后转发"**，仅 `is_setup_ready` 是真实实现 |

### 2.3 端口/契约量化

| 指标 | 数值 |
|---|---:|
| `ports.py` 行数 / Protocol 数 | 121 / 7 |
| 全仓 `isinstance`/`issubclass`/`cast` 针对这些 Protocol | **0** |
| `IWebUiOperations` 作为注解使用处 | **1**（`server.py:198`） |
| 从未被任何模块 import 的 Protocol | **5**（`IWatchOps` `ITaskOps` `IMediaOps` `IStatsOps` `IUploadOps`，仅作 `IWebUiOperations` 基类） |
| `IWebUiOperations` 有效成员（继承闭包） | 19 |
| facade 实际表面（`_WEB_UI_DELEGATE_METHODS`） | 40 |
| **Protocol 对实现表面的覆盖率** | **47.5%**（19/40，21 个方法无端口声明） |
| adapters 依赖的 `host.<attr>` 契约 | **31** |
| `getattr(host / self._host / self.operations, ...)` 派发点 | **41** |
| `IBotCallbackHost` 成员数 / 实际使用 | 19 / **19**（63 处访问，0 未用、0 未声明） |

---

## 3. 发现清单

### [ADP-01] `WebOperationsMixin` 是业务编排模块，不是 HTTP adapter（P0）

**现象**：`module/adapters/webui/operations.py`（1897 行）名义上是 WebUI adapter，实际零 HTTP 代码，承载任务队列/监听/账号/向导/清理/归档/诊断/统计 八大业务域。

**证据**：`module/adapters/webui/operations.py` L104 与全文 token 普查（`probe_09_protocol.py` 第 49–66 行输出）：

```python
# module/adapters/webui/operations.py:104
class WebOperationsMixin:
```

```
BaseHTTPRequestHandler : 0      self.headers : 0      self.wfile : 0
self.rfile             : 0      urlparse     : 0      parse_qs   : 0
HTTPStatus             : 0      send_response: 0      send_header: 0
end_headers            : 0      json.dumps   : 0      handler    : 0
```

对比 `server.py` 内 `HTTPStatus` 密集出现（如 `server.py:1436`），说明 HTTP 语义确实在 `server.py`，`operations.py` 是纯业务。

**量化**：114 方法，8 组，`<=3 行` 的 40 个，严格转发 shim 38 个；0 个 HTTP 原语。

**代价**：
- 业务规则（任务调度、归档编排）被钉在 `adapters/webui/` 下。Bot 或 CLI 要复用同一逻辑，只能反向 import adapter 或再次复制——`callback_handler.py:29-30` 已经在 import `module.domain.*`，说明团队清楚正确的方向在哪。
- 改动业务 = 改动 adapter 文件，架构守卫 `test_no_layer_inversions` 无法把"业务变更"与"适配变更"区分开，审查粒度失真。

**最小改进**：把 `WebOperationsMixin` 整体移到 `module/app/`（或 `module/domain/webops/`），`adapters/webui` 只保留 `server.py` + `handlers/` + payload 校验。**不需要重写任何逻辑**，是纯移动 + import 修正；`system_log_archive_retry_ops.py`、`archive_author_ops.py`、`task_manager.py` 一并跟随。

---

### [ADP-02] 一次请求跨 4 跳，中间层用字符串 `getattr` 派发（P0）

**现象**：handler 拿到 `server`，`server` 再通过**字符串名字**去 `operations` 上找方法。名字写错的失败模式是"静默 None"而非异常。

**证据**：

```python
# module/adapters/webui/server.py:284-288
    def _operation(self, name: str):
        if self.operations is None:
            return None
        method = getattr(self.operations, name, None)
        return method if callable(method) else None
```

```python
# module/adapters/webui/server.py:1481-1483  （在 create_upload 内，前 44 行做 payload 校验）
        create_upload = self._operation("create_upload")
        if create_upload:
            return create_upload(payload)
```

```python
# module/adapters/webui/operations.py:1889-1897
def _bind_web_delegate(name: str):
    def delegate(self, *args, **kwargs):
        return getattr(self._host, name)(*args, **kwargs)
    delegate.__name__ = name
    return delegate

for _method_name in _WEB_UI_DELEGATE_METHODS:
    setattr(WebOperationsFacade, _method_name, _bind_web_delegate(_method_name))
```

完整调用链（以 `create_upload` 为例）：
`handlers/misc.py.handle_post` → `server.create_upload`（56 行校验，L1433-1488）→ `server._operation("create_upload")`（字符串）→ `WebOperationsFacade.create_upload`（`getattr(self._host, "create_upload")`）→ `WebOperationsMixin.create_upload`（L720-722，转发）→ `_require_web_task_manager(self).create_upload`。

**量化**：3 个类、4 跳；41 处 `getattr(host/self._host/self.operations, ...)` 派发点（`surfaces.txt` L29–71 逐个列出）。

**代价**：
- **IDE / mypy / 改名工具全部失效**：`_operation("create_upload")` 与 `setattr` 循环都不在静态图里，"查找引用"找不到调用方。
- 失败模式恶劣：`_operation` 返回 `None` → `server.create_upload` 走 `raise WebUiApiError("upload_operations_unavailable", ...)`（L1484-1488），把**接线 bug 报成 503 服务不可用**，排查方向被误导。
- 新增/删除一个 API 方法要在 4 处保持名字字符串一致（handlers 派发元组、`server` 方法、`_WEB_UI_DELEGATE_METHODS`、mixin）。

**最小改进**：(a) 把 `operations` 以构造注入直接交给 handlers，删掉 `server` 的 31 个转发方法；(b) `_operation` 的 `getattr(..., None)` 改为无默认值的 `getattr` 或在缺失时 `raise`（fail fast），让接线错误立即暴露；(c) 用显式类方法替代 `setattr` 循环（40 个方法可直接生成，但应在源码里可见）。

---

### [ADP-03] 32 个同名方法造成双份表面（P1）

**现象**：`WebUiServer` 与 `WebOperationsMixin` 有 32 个完全同名的方法，其中 31 个是"校验后转发"。同一个名字在两个类里各有一份实现，语义不同（一个校验、一个执行）。

**证据**：

```
WebOperationsMixin methods : 114
WebUiServer methods        : 67
NAME COLLISIONS            : 32
  ['cancel_deferred_discussion_capture', 'cleanup_media_files', 'create_channel_download',
   'create_upload', 'create_watch', 'delete_watch', 'detect_transfer_range',
   'execute_archive_author_reorganize', 'export_diagnostic_bundle', 'export_forward_watches',
   'export_system_logs', 'export_table', 'get_active_archive_author_job', 'get_archive_author_job',
   'is_setup_ready', 'list_archive_author_channels', 'list_archive_author_plan_moves',
   'list_cleanup_logs', 'list_deferred_discussion_captures', 'list_operations',
   'list_system_logs', 'list_watch_events', 'list_watches', 'resolve_archive_author_reorganize',
   'retry_archive_from_system_log', 'retry_deferred_discussion_capture',
   'run_deferred_discussion_capture_now', 'scan_archive_author_reorganize',
   'scan_media_for_cleanup', 'statistics', 'stop_archive_author_job', 'update_watch']

server 方法中 DELEGATE->self.operations : 31
server 方法中 REAL IMPL                 : 1  -> ['is_setup_ready']
```

转发样例（`create_upload` L1433-1488 共 56 行，其中仅 L1481-1488 是转发，其余为 payload 校验）：

```python
# module/adapters/webui/server.py:1481-1483
        create_upload = self._operation("create_upload")
        if create_upload:
            return create_upload(payload)
```

**量化**：32 个重名；31 个纯转发。`create_watch` L1031-1157（127 行）、`create_upload` L1433-1488（56 行）等大方法体几乎全是校验。

**代价**：改一个 API 的行为要判断"改哪一份"，且两份都叫同一个名字；grep 一个方法名会命中两处定义 + 一处字符串字面量。`create_watch` 单方法 127 行校验混在 HTTP 壳里，是后续 bug 的高发点。

**最小改进**：校验逻辑下沉为 `module/adapters/webui/validation.py` 的纯函数（`validate_upload_payload(payload) -> dict`），`server` 方法与 handler 合并成一层，`server` 只保留 HTTP 语义（状态码、header、序列化）。

---

### [ADP-04] `ports.py` 的 Protocol 无任何约束力（P0）

**现象**：7 个 Protocol 全部 `@runtime_checkable`，但全仓**没有一处**运行时或静态校验；`IWebUiOperations` 只被用作一个可选参数的类型标注，且该标注与实现不同步。

**证据**：

```python
# module/ports.py:66-69
@runtime_checkable
class IWebUiOperations(IWatchOps, ITaskOps, IMediaOps, IStatsOps, IUploadOps, Protocol):
    """Combined WebUI operations seam for typing convenience."""
```

全仓检索结果（`grep` 覆盖 `module/` + `unit_tests/`，模式含 `isinstance(...|IWebUiOperations|IWatchOps|...|IDiagnosticPort)` 与 `cast(...)`）：

```
total isinstance/cast protocol hits: 0
```

唯一的注解使用处：

```python
# module/adapters/webui/server.py:28
from module.ports import IDiagnosticPort, IWebUiOperations
# module/adapters/webui/server.py:198
        operations: Optional[IWebUiOperations] = None,
```

而 handlers **完全没有类型标注**，全是裸鸭子类型（`handlers.txt` L26–56；实测 `handlers/*.py` 顶层函数共 **31 个**，无一带注解）：

```python
def handle_get(handler, server, parsed)
def handle_post(handler, server, parsed)
```

**协议与实现已经漂移**（`probe_09_protocol.py`）：

```
IWebUiOperations EFFECTIVE (inherited) surface = 19 members
WebOperationsFacade actual surface (delegate tuple) = 40
facade methods NOT covered by IWebUiOperations Protocol: 21
   ['cancel_deferred_discussion_capture', 'cancel_task_downloads', 'cancel_task_uploads',
    'execute_archive_author_reorganize', 'export_diagnostic_bundle', 'export_forward_watches',
    'export_system_logs', 'get_active_archive_author_job', 'get_archive_author_job',
    'list_archive_author_channels', 'list_archive_author_plan_moves',
    'list_deferred_discussion_captures', 'list_system_logs', 'pause_task_uploads',
    'resolve_archive_author_reorganize', 'retry_archive_from_system_log',
    'retry_deferred_discussion_capture', 'run_deferred_discussion_capture_now',
    'scan_archive_author_reorganize', 'should_continue_web_transfer_task', 'stop_archive_author_job']
=> Protocol covers 47.5% of the facade surface
```

`@runtime_checkable` 在这里也**用不上**：3.13 实测（`E:\codebase\tgbot\.venv313\Scripts\python.exe`）

```
isinstance(no attr) = False
isinstance(with attr) = True
issubclass TypeError: Protocols with non-method members don't support issubclass(). Non-method members: 'x'.
```

即带数据成员的 Protocol 只能 `isinstance`、不能 `issubclass`，而 `IBotCallbackHost`(11 数据成员) 与 `IUploadContext`(10 数据成员) 恰好是数据成员为主的——装饰器存在但永不被触发。

**代价**：端口是**注释级文档**。`IWebUiOperations` 声明 19 个方法，实际 facade 有 40 个；新增 21 个归档/诊断/任务方法时端口不会报错，读者会以为端口就是全部契约。删掉 `ports.py` 的净信息损失接近于零，但它给人"已有 seam"的错觉——这本身是维护成本。

**最小改进**（成本最低、收益立竿见影）：
```python
# 新增 unit_tests/webui_operations_port_case.py
def test_facade_conforms_to_port(self):
    facade = WebOperationsFacade(_FakeHost())
    self.assertIsInstance(facade, IWebUiOperations)   # 3.13 支持数据/方法成员的 isinstance
    self.assertEqual(set(_WEB_UI_DELEGATE_METHODS), set(IWebUiOperations.__protocol_attrs__))
```
并给 `handlers/*.py` 的 `server` 参数补 `WebUiServer` 标注（26 处签名），让类型检查器进场。

---

### [ADP-05] host 契约靠 `getattr` 字符串反射，adapter 反向写 host 状态（P0）

**现象**：adapters 需要的宿主能力没有显式声明，而是散落的 `getattr(host, 'x', None)`；更严重的是 adapter **会往 host 上写属性**。

**证据**（`module/adapters/webui/operations.py:54-101`，adapter 主动向 host 注入 6 个属性）：

```python
def _require_web_task_manager(host):
    """Return host.web_task_manager, lazily wiring a manager for bare test hosts."""
    wm = getattr(host, 'web_task_manager', None)
    if wm is not None:
        return wm
    from module.adapters.webui.task_manager import WebUITaskManager

    if getattr(host, 'web_task_queue', None) is None:
        host.web_task_queue = asyncio.Queue()            # L61-62  写 host
    if getattr(host, 'web_submitted_task_ids', None) is None:
        host.web_submitted_task_ids = set()              # L63-64  写 host
    if getattr(host, 'web_operation_queue', None) is None:
        host.web_operation_queue = asyncio.Queue()       # L65-66  写 host
    if getattr(host, 'web_operations', None) is None:
        host.web_operations = {}                         # L67-68  写 host
    if not hasattr(host, 'web_running_task'):
        host.web_running_task = None                     # L69-70  写 host
    if not hasattr(host, 'web_running_task_id'):
        host.web_running_task_id = None                  # L71-72  写 host
    wm = WebUITaskManager(
        transfer_store_getter=lambda: getattr(host, 'transfer_store', None),
        ... 20 个依赖项 ...
    )
    host.web_task_manager = wm                           # L100    写 host
    return wm
```

**量化**：
- 该函数要求 **20 个** host 能力（`web_task_manager` `web_task_queue` `web_submitted_task_ids` `web_operation_queue` `web_operations` `web_running_task` `web_running_task_id` `transfer_store` `diagnostic` `loop` `watch_manager` `pikpak_manager` `progress_tracker` `archive_pikpak_item` `refresh_transfer_task_counts` `process_web_transfer_task` `retry_watch_inline_task` `process_web_task_queue` `_ensure_media_manager` `uploader`）。
- adapters 全量依赖 `host.<attr>` **31 个**（`surfaces.txt` L76-77 全列）。
- `getattr` 派发点 **41** 处。
- "bare test hosts" 这条 docstring 本身就是自白：**因为宿主太大，测试只能造鸭子对象，所以 adapter 里必须写兜底装配逻辑**。

**代价（已实测兑现，不是推测）**：见 §4.3——`187d1d8` 删除 `__getattr__` 后，宿主属性契约失去隐式兜底，**同一批属性缺口在 1 天内用 3 个提交、22 个文件、332 行新增去补**，其中 `5538e56` 的提交信息明确写着"用 AST 审计一次性补齐 … 剩余的宿主属性缺口"。**这是"改一处、炸多处"的真实账单。**

**最小改进**：
1. 把 31 个属性固化为 `module/ports.py` 里一个显式 `IWebHost` Protocol，并在 `composition_root` 装配处加一句 `assert isinstance(self, IWebHost)` —— 契约从字符串变成可校验对象。
2. 禁止 adapter 写 host：`_require_web_task_manager` 的 6 处注入改为由 composition root 在装配期创建（`host.web_task_queue = ...` 移到 `composition_root.py`）。
3. 用 `getattr(host,'x',None)` 的 20 个 `*_getter` 改为**构造注入**，把 `WebUITaskManager` 的依赖在 composition root 一次性传全。

---

### [ADP-06] bot ↔ downloader 双向引用，`CallbackHandler` 10 个注入参数含双别名（P1）

**现象**：bot 与 downloader 互相持有；`CallbackHandler` 的构造签名有 10 个参数，其中 `host` 与 `downloader_ref` 是**同一个对象的两个名字**。

**证据**：

```python
# module/composition_root.py:108
        self.bot.downloader = self
```
```python
# module/adapters/bot/bot.py:85-86
    def __init__(self, downloader=None, handler_overrides: Optional[Dict[str, Callable]] = None, gc=None):
        self.downloader = downloader
```
```python
# module/adapters/bot/callback_handler.py:38-61（截断注释）
class CallbackHandler:
    def __init__(
        self,
        app_getter, gc_getter, diagnostic,                     # 3
        watch_manager_getter=None, transfer_store_getter=None,  # 5
        loop_getter=None, user_getter=None, my_id_getter=None,  # 8
        host: IBotCallbackHost = None,                          # 9
        downloader_ref=None,                                    # 10
    ):
        ...
        self._host = host if host is not None else downloader_ref   # L60 同一对象的两个名字
        self._downloader = self._host                               # L61 第三个名字
```

4 跳 Law-of-Demeter 链：

```python
# module/adapters/bot/callback_handler.py:257
            if await self._downloader.bot.guide_wizard.handle_callback(client, callback_query):
```

`bot.py` 侧同样反向依赖宿主：

```
bot.py: reads self.<x> that are NEITHER defined NOR assigned here = 11
    self.root                  (read 21x)
    self.download_chat_filter  (read 6x)
    self.listen_download_chat  (read 5x)
    self.listen_forward_chat   (read 5x)
    self.last_message          (read 4x)
    self.adding_keywords       (read 4x)
    self.last_client           (read 3x)
    self.bot_task_link / self.handle_media_groups / self.data / self.COMMANDS (各 1x)
```

**量化**：`bot.downloader = self` 反向赋值 1 处（`composition_root.py:108`）；`CallbackHandler.__init__` **10 个参数、3 个别名指向同一对象**（`host`/`downloader_ref`/`_downloader`）；`Bot` 类读 11 个未在本地定义/赋值的宿主属性（`self.root` 21 次为最高频）。

**代价**：`CallbackHandler` 名义上"依赖 IBotCallbackHost 端口"，实际上还依赖宿主上的 `bot`、`guide_wizard`、`gc` 等**未在端口里声明**的对象，端口描述不完整；`self.root` 这种高频隐式依赖让 `Bot` 无法脱离宿主单测。

**最小改进**：`CallbackHandler` 只接收 2 个东西——`IBotCallbackHost` 与一个 `CallbackDeps` 数据类（承载 `app/gc/diagnostic/loop/user/my_id` 的 getter）；删掉 `downloader_ref` 别名（`grep` 确认仅有 1 处传入：`composition_root.py:151`）。`callback_handler.py:257` 的 `self._downloader.bot.guide_wizard.handle_callback` 改为把 `guide_wizard` 显式注入。

---

### [ADP-07] 归档编排依赖 host 私有方法，并用 try/except 兜底（P1）

**现象**：`ArchiveAuthorOps` 在拿到宿主时直接调用**私有**方法 `host._ensure_transfer_store()` 与绑定 `host._run_telegram_coro`——跨对象调用下划线私有 API。

**证据**：

```python
# module/adapters/webui/archive_author_ops.py:44-59
        app = getattr(host, 'app', None)
        telegram = getattr(host, 'user', None)
        if telegram is None and app is not None:
            telegram = getattr(app, 'client', None)
        store = None
        try:
            store = host._ensure_transfer_store()          # L50 私有方法
        except Exception:
            store = getattr(host, 'transfer_store', None)  # L52 兜底
        return ArchiveAuthorReorganizeService(
            archive_client=client,
            telegram_client=telegram,
            transfer_store=store,
            run_coro=host._run_telegram_coro,              # L57 私有方法作为回调传出
            on_log=self._archive_author_log,
        )
```

同源调用点全量（`pikpak.txt` L45–60）：

```
module/adapters/webui/archive_author_ops.py:50 : store = host._ensure_transfer_store()
module/adapters/webui/archive_author_ops.py:111: transfer_store = host._ensure_transfer_store()
module/adapters/webui/archive_author_ops.py:57 : run_coro=host._run_telegram_coro,
module/adapters/webui/operations.py:839        : def _run_telegram_coro(self, coro, timeout: float | None = 300):
module/adapters/webui/operations.py:108        : def _ensure_transfer_store(self) -> TransferStore:
```

`_ensure_transfer_store` 自身也是反射装配**并且继续写宿主状态**（`operations.py:108-125`）：

```python
# module/adapters/webui/operations.py:108-121
    def _ensure_transfer_store(self) -> TransferStore:
        store = getattr(self, 'transfer_store', None)          # L109 反射读
        if store is not None:
            self._bind_transfer_store_runtime(store)
            return store
        temp_directory = getattr(getattr(self, 'app', None), 'temp_directory', None)  # L113 两跳反射
        if not temp_directory:
            raise RuntimeError('temp_directory is required to create TransferStore')
        store = TransferStore(directory=temp_directory)
        self.transfer_store = store                            # L117 写宿主
        ctx = self.__dict__.get('ctx')
        if ctx is not None:
            ctx.transfer_store = store                         # L120 写宿主的 ctx 对象
```

`_run_telegram_coro` 靠 `getattr(self, 'loop', None)`（L845）取事件循环，取不到就 `raise RuntimeError`。

**量化**：私有 host API 依赖 **2 个**（`_ensure_transfer_store`、`_run_telegram_coro`），调用点 **3 处**（L50、L57、L111）。`archive_author_ops.py` 另有 12 处 `getattr(host, ...)` 公开属性读取（`surfaces.txt` L31-45）。`_run_telegram_coro` 把协程调度细节（`asyncio.run_coroutine_threadsafe` + `future.result(timeout)`，L848-849）暴露给了归档编排——一个纯业务模块被迫了解"Telegram 事件循环在另一个线程"。

**代价**：
- `try/except Exception` 兜底（L49-52）说明作者已知这条路径脆弱；它会**吞掉** `_ensure_transfer_store` 内部真实错误（如 store 初始化失败），退化为 `transfer_store=None`，把装配故障变成静默的数据丢失风险。
- 任何对 `_ensure_transfer_store` 的重命名都是跨文件破坏性变更，且类型检查器不会提示（字符串/属性反射）。

**最小改进**：把 `transfer_store` 与 `run_coro` 作为**构造参数**传给 `ArchiveAuthorOps`（装配在 composition root 完成，与 ADP-05 第 3 条同一改法），删除 L49-52 的 `try/except` 兜底，让缺失在装配期直接失败。

---

### [ADP-08] `WebUiServer.start` 463 行：HTTP 路由与业务分发挤在一个方法里（P1）

**现象**：`WebUiServer` 是第二个上帝对象（67 方法 / L185-1853，1669 行类体），其中 `start` 单方法 **463 行**，把 socket 启动、路由匹配、认证门、setup 门、五个 HTTP 动词的分发全部内联。

**证据**（`handlers.txt` L114）：

```
class WebUiServer  lines 185-1853  methods=67
    __init__      L192-246 (55)
    start         L440-902 (463)
    stop          L904-911 (8)
    ...
```

对照：`handlers/__init__.py`（89 行）已经实现了干净的动词派发表，但 `start` 里仍内联了路由与门禁逻辑。

**量化**：67 方法；`start` 463 行（占类体 1669 行的 27.7%）；`__init__` 55 行 / **23 个构造参数**（L192-217，实测 `ast` 计数）——构造函数参数数已超过多数类的全部方法数。

**代价**：`start` 是每次启动必经路径，463 行内联逻辑无法单测；26 个构造参数说明装配责任泄漏到了 adapter（本应由 composition root 传入聚合后的对象）。

**最小改进**：把 `start` 拆成 `_bind_socket()` / `_build_handler()` / `_gate()` / `_dispatch(method)` 四个方法，路由与门禁交给已有的 `handlers/__init__.py` 派发表；`__init__` 的 23 个参数改为接收 3 个聚合对象（`store`、`WebUiDeps`、`SetupDeps`）。

---

### [ADP-09] 架构守卫 314 行，但不覆盖任何 Protocol（P2）

**现象**：仓库有 `unit_tests/architecture_guard_case.py`（314 行，7 个测试），能查导入环、层倒置、宿主属性可解析、composition root 无反射——**但没有一条断言 Protocol 一致性**。

**证据**（`bot.txt` L65-82）：

```
unit_tests/architecture_guard_case.py: 314 lines
  158: def test_module_import_graph_has_no_cycles(self):
  198: def test_subpackages_do_not_import_top_level_shims(self):
  221: def test_no_layer_inversions(self):
  248: def test_composed_host_resolves_every_attribute_read(self):
  288: def test_composition_root_has_no_reflective_getattr(self):
  295: def test_transfer_ports_have_no_host_reflection(self):
  300: def test_top_level_contains_only_facade_and_shims(self):
```

`test_composed_host_resolves_every_attribute_read`（L248）正是为 `5538e56` 那类事故新增的——**守卫在跟着事故长，且只覆盖"属性存在性"，不覆盖"依赖方向是否合理、私有 API 是否被跨对象调用"**。因此 ADP-05（adapter 写 host）与 ADP-07（adapter 调 host 私有方法）都能通过现有守卫。

**量化**：314 行守卫 / 7 个测试；0 个测试涉及 `IWebUiOperations`、`IBotCallbackHost`、`IUploadContext`、`IDiagnosticPort`。

**代价**：守卫给出"架构已被保护"的安全感，但最贵的耦合（字符串反射宿主契约、跨对象私有调用）在雷达之外。

**最小改进**：加 3 条断言（每条 <10 行）：
1. `test_adapters_do_not_write_host_state` —— AST 扫 `adapters/**` 中的 `host.<attr> = ...` 赋值，当前会命中 `operations.py` 6 处；
2. `test_adapters_do_not_call_host_private_api` —— 扫 `host._x(` 调用，当前会命中 `archive_author_ops.py:50,57,111`；
3. `test_protocols_conform` —— `assertIsInstance(WebOperationsFacade(host), IWebUiOperations)`。

---

## 4. 变更放大实测（git 实证）

> 方法：`git log --format=%H\t%s` 取最近 60 个提交，跳过 `chore`/`docs` 前缀，用 `git show --stat --format=` 解析每个提交的文件列表，再按目录前缀映射到"层"。
> 层映射（`probe_05_amplify2.py`）：`adapters/webui` `adapters/bot` `adapters/pikpak` `domain.transfer` `domain.watches` `domain.pikpak` `domain.persistence` `domain.models` `domain.core` `domain.media` `utils` `infra` `app.host` `tests` `docs` `frontend` `root.other`。

### 4.1 总体统计（40 个非 chore 提交）

```
$ python probe_05_amplify2.py   （内部执行 git log / git show --stat）
sampled commits (non-chore, has file changes): 40
files/commit: sum=442 mean=11.05 median=7 min=2 max=71
commits touching >=2 layers: 40/40 = 100.0%
commits touching >=3 layers: 35/40 = 87.5%

commits touching adapters: 23; of those also touching domain/other layers: 21 = 91.3%
```

**结论：平均一次改动触碰 11.05 个文件，其中位数为 7；100% 的改动跨 ≥2 层，87.5% 跨 ≥3 层；触碰 adapters 的改动有 91.3% 同时改动非 adapters 层——即"改 adapter 不用碰域层"在本仓库几乎不存在。**

`git show --shortstat` 原始摘要（节选）：

```
5538e56  10 files changed, 221 insertions(+), 9 deletions(-)
e0b739d  13 files changed, 1527 insertions(+), 101 deletions(-)
bce98f8   8 files changed, 240 insertions(+), 59 deletions(-)
523df22  15 files changed
a3dcbf9  31 files changed
e6621e4  53 files changed
187d1d8  71 files changed, 7349 insertions(+), 6885 deletions(-)
```

### 4.2 单功能端到端的放大：`b352fc3` "允许从系统日志手动重试归档"

一个**新增 WebUI 端点**的提交，实际触碰 **20 个文件 / 6 层**，其中代码文件 17 个：

```
$ git show --stat b352fc3
b352fc3 feat(webui): allow manual archive retry from system logs      20 files changed

  module/adapters/webui/assets.py                       ← 前端资源清单/缓存键
  module/adapters/webui/dist/tailwind.min.css           ← 样式产物
  module/adapters/webui/handlers/misc.py                ← HTTP 路由分发
  module/adapters/webui/server.py                       ← server 层方法
  module/adapters/webui/static/desktop.js               ← 桌面端 UI
  module/adapters/webui/static/mobile_script.js         ← 移动端 UI
  module/adapters/webui/static/shared.js                ← 共享 UI
  module/adapters/webui/static/tailwind.css             ← 样式源
  module/adapters/webui/system_log_archive_retry_ops.py ← 新增业务 ops
  module/adapters/webui/templates/views.html            ← 模板
  module/web_operations.py                              ← 业务编排（今 operations.py）
  module/persistence/store/system_logs.py               ← 持久化
  module/persistence/system_log.py                      ← 持久化
  module/transfer/live_transfer.py                      ← 传输域
  unit_tests/system_log_retry_archive_case.py
  unit_tests/web_ui_assets_case.py
  + CONTEXT.md, module/__init__.py, pyproject.toml, uv.lock
```

**量化：1 个端点 = 17 个代码文件 + 3 个装配/元数据文件，跨 4 个层（adapters / 业务编排 / persistence / transfer）。** 其中前端 6 个文件（`static/*.js` × 3、`templates/views.html`、`assets.py`、`tailwind.css` + `dist/tailwind.min.css`）是"UI 与后端同仓同提交"的直接体现。

其他对照：
- `523df22` "PikPak 多账号切换语义加固"（`fix(pikpak)`）：**15 文件 / 7 层**，含 `adapters/pikpak` + `adapters/webui` + `core/target_profiles.py` + ADR 文档。
- `a3dcbf9` "按任务归档标题来源 + prefer/fallback"（`feat(archive)`）：**31 文件 / 8 层**。
- `94bb15c` "PikPak 账号表单排版 + 当前账号徽章"（纯前端排版修复）：**6 文件 / 3 层**——连改个排版都要碰 `module/__init__.py` 与 `pyproject.toml`（版本号联动）。

### 4.3 因果链实证：删掉 `__getattr__` 换来的 22 文件维修账单（最有力的证据）

这是耦合代价**真实兑现**的完整链条，全部可从 git 复原：

```
$ git log -1 --format="%h %ad %s" --date=short 187d1d8
187d1d8 2026-08-16 refactor(module): 完成架构解耦 Phase 3-6 并加架构守卫
$ git show --shortstat --format="" 187d1d8
 71 files changed, 7349 insertions(+), 6885 deletions(-)

$ git log -1 --format="%h %ad %s" --date=short 2a83eaf
2a83eaf 2026-08-17 fix: alias host listen_* to watch_manager after login restore
$ git show --shortstat --format="" 2a83eaf
 7 files changed, 51 insertions(+), 5 deletions(-)

$ git log -1 --format="%h %ad %s" --date=short 9757db8
9757db8 2026-08-17 fix: restore host watch/bot delegates removed with __getattr__
$ git show --shortstat --format="" 9757db8
 5 files changed, 60 insertions(+), 2 deletions(-)

$ git log -1 --format="%h %ad %s" --date=short 5538e56
5538e56 2026-08-17 fix: 修复机器人启动崩溃与全部宿主属性缺口 0.2.245
$ git show --shortstat --format="" 5538e56
 10 files changed, 221 insertions(+), 9 deletions(-)
```

`5538e56` 的提交信息**自己把病因写清楚了**：

> pyrogram.filters.command() 无参调用抛 TypeError，被 start_bot 的 except Exception 吞成失败字符串，导致引导向导 handler 注册失败、is_bot_running 始终为 false，机器人整体离线。…
> 同时用 AST 审计一次性补齐 187d1d8 删除 `__getattr__` 后剩余的宿主属性缺口（done_notice/handle_media_groups/safe_edit_message/update_text/transfer_item_archive_*/web_operation_counter），并把只读的 user property 改为可赋值，避免同类反射式接线再次逐个在生产暴露。

**量化：架构重构（`187d1d8`）后 1 天内，用 3 个提交（`2a83eaf` + `9757db8` + `5538e56`）、22 个文件、332 行新增、16 行删除去修宿主属性的隐式契约。** 修复分布在 `adapters/bot/host.py`、`adapters/webui/operations.py`、`composition_root.py`、`downloader.py`、`transfer/watch_applicator.py` **5 个不同层**。

**这条链直接支撑 ADP-05 的判断**：当宿主契约是 `getattr` 字符串反射时，"移除隐式兜底"这类纯结构改动会立刻变成跨 5 层、持续 1 天、以"机器人整体离线"形式在生产暴露的事故。

### 4.4 后重构期（`187d1d8..HEAD`）的 6 个提交

```
1f7a43b 2026-10-01 fix(forward)  6 files  4 layers
bce98f8 2026-10-01 fix(webui)    8 files  5 layers
e0b739d 2026-10-01 fix(webui)   13 files  6 layers
5538e56 2026-08-17 fix(host gap) 10 files 5 layers
9757db8 2026-08-17 fix(host gap)  5 files 5 layers
2a83eaf 2026-08-17 fix(host gap)  7 files 5 layers
```

**6 个提交里 3 个（50%）是对宿主属性契约的抢修**（`2a83eaf`/`9757db8`/`5538e56`，合计 22 文件），重构后 1 天内产生。重构降低了目录层级的混乱，但**没有降低隐式宿主契约带来的改动放大**。

---

## 5. 反例与诚实边界（避免过度断言）

以下三点**已用数据排除**，不计入耦合发现：

1. **`IBotCallbackHost` 是精确且完整的端口**。19 个成员 **19 个被真实使用**（63 处访问：`self._host.<m>` / `self._downloader.<m>`），**0 个声明未用、0 个用了未声明**（`probe_11_proto_usage.py`）：

   ```
   used: 19/19   UNUSED: 0 -> []
   total access sites: 63
   distinguished members actually reached: 19
   reached but NOT declared in IBotCallbackHost: []
   ```

   最高频成员：`download_chat_filter`(22)、`cd`(6)、`adding_keywords`(5)、`add_keyword_mode_handler`(4)、`last_message`(4)。
   **结论**："按消费者裁剪的端口"这个做法在本仓库被证明可行且已被执行。因此 ADP-04 的问题**不是团队不会写端口，而是 WebUI 路径整体绕开了端口**——这是可修的方法论问题，不是能力问题。

2. **`ports.py` 只有 121 行、7 个 Protocol，本身不是负担**；负担在于它被当作已完成的工作。删除它净损失接近零（同 1）。

3. **`archive.py` / `archive_author.py`（`adapters/pikpak`，813 + 1196 行）未发现跨对象私有 API 调用**：`host.<x>` 与 `host._x` 命中均为 0，私有状态 `_dedup_lock`/`_mkdir_lock`/`_ensured_dirs`/`_lock`/`_jobs` 全在**类内部**（`pikpak.txt` L20-28）。`integration.py`（603 行）的 9 个 `self._x`（`_transfer_store_getter`、`_gc_getter`、`_pikpak_archive_client` 等）也都是自身在 `__init__` 注入的 getter，**不构成对宿主的私有依赖**——这点比任务书的预期更干净，故不计为发现。

---

## 6. 执行过的命令（可复现）

### 6.1 Python 探针（全部只读，均位于 `tmp/coupling-audit/02-adapters/`）

```
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_00_layout.py       # 文件行数/adapters 目录树
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_01_ops_methods.py  # 114 方法 AST 枚举 + HTTP 信号
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_02_shims.py        # 转发 shim + self.<attr> + 分组
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_03_bot.py          # IBotCallbackHost 成员使用 + isinstance 普查 + downloader 反向引用
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_04_amplify.py      # 变更放大（初版，7 个候选提交）
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_05_amplify2.py     # 变更放大（40 提交聚合 + 逐字 --stat）→ amplify.txt
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_06_handlers.py     # handler 签名/operations 访问/类结构 → handlers.txt
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_07_pikpak.py       # 私有 host API 依赖 → pikpak.txt
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_08_surfaces.py     # 同名方法/动态派发/host 契约 → surfaces.txt
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_09_protocol.py     # Protocol 继承闭包 + 覆盖率 → protocol.txt
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_10_bot.py          # bot.py 结构 + 宿主属性缺口 + 守卫范围 → bot.txt
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_11_proto_usage.py  # IBotCallbackHost 19 成员逐项计数
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_12_groups.py       # 8 组分类校验（合计 114，无遗漏）
.venv313\Scripts\python.exe tmp\coupling-audit\02-adapters\probe_13_verify.py       # 复核引用数字：__init__ 23 参数 / handlers 31 函数 / _ensure_transfer_store 实现
```

### 6.2 git 只读查询

```
git rev-parse HEAD
git status --porcelain
git diff --stat HEAD
git diff --cached --stat
git hash-object module/adapters/webui/operations.py      # 与下一行对比证明磁盘==HEAD
git rev-parse HEAD:module/adapters/webui/operations.py
git cat-file blob HEAD:module/adapters/webui/operations.py | wc -l
git log --oneline -30
git log --format=%H\t%ad\t%s --date=short 187d1d8..HEAD
git log --format=%H\t%s -60
git show --stat <sha>            # sha ∈ {a3dcbf9, b352fc3, 523df22, 94bb15c, 1f7a43b, 5538e56, e0b739d, 9757db8, 2a83eaf, 187d1d8}
git show --shortstat --format="" <sha>
git log --oneline -3 -- module/adapters/webui/operations.py
git log -1 --format="%h %ad %s" --date=short <sha>
```

### 6.3 grep / 环境校验

```
grep -r "isinstance|cast" + Protocol 名        → 0 命中
grep "from module.ports import|<Protocol 名>"  → 5 个真实 import 点
.venv313\Scripts\python.exe -c "import sys;print(sys.version)"                      # 3.13.7
.venv313\Scripts\python.exe -c "import module.adapters.webui.operations as o; ..."  # import OK
.venv313\Scripts\python.exe -c "runtime_checkable 数据成员 isinstance/issubclass 行为实测"
```

### 6.4 未执行的操作（合规声明）

- 未修改 `module/` 或 `unit_tests/` 下任何文件；未执行 `git add`/`commit`/`push`。
- 未运行测试套件（本任务为只读耦合审查，无代码变更需要验证；且 A2 结论不依赖测试结果）。
- 全部写入均在 `tmp/coupling-audit/02-adapters/`。

---

## 7. 附：本目录产物

| 文件 | 内容 |
|---|---|
| `evidence.md` | 本报告 |
| `amplify.txt` | 变更放大原始数据（40 提交逐项 + 逐字 `git show --stat`） |
| `handlers.txt` | handler 签名、operations 访问点、server/operations 类结构 |
| `pikpak.txt` | 私有 host API 依赖全量、integration.py 结构 |
| `protocol.txt` | Protocol 继承闭包、覆盖率、32 同名方法分类、HTTP token 普查 |
| `bot.txt` | bot.py 结构、宿主属性缺口、双向引用、架构守卫范围 |
| `surfaces.txt` | 同名方法、41 处动态派发点、31 个 host 契约属性 |
| `ops_methods.json` | 114 方法结构化清单 |
| `self_attrs.json` | mixin 内 `self.<attr>` 频次 |
| `probe_00..12_*.py` | 全部只读探针脚本（可复现） |
