# A1 — 门面 / host 上帝对象耦合取证（TRMD）

- 仓库：`E:\codebase\tgbot`
- 解释器：`E:\codebase\tgbot\.venv313\Scripts\python.exe`（Python 3.13.7）
  - ⚠️ `.venv\Scripts\python.exe` 是 3.14.0a5，`import module` 会在 `yaml/_yaml` C 扩展处 0xC0000005 崩溃；本报告所有脚本均用 `.venv313` 运行。
- 只读声明：`module/` 与 `unit_tests/` 未做任何修改，无 git commit。全部脚本与输出仅在 `tmp/coupling-audit/01-host/`。
- 判定口径：
  - **已证实耦合** = 有行号 + 可复现命令（脚本输出或实测异常）。
  - **风格偏好** 一律不写。凡「结构已成立但当前未触发」的，单独标注。
  - 时序耦合（`TransferContext.transfer_store` 构造时为 `None`）由 A4 负责，本报告仅在 H-04 提及 `composition_root.py:193` 一行，不展开。

范围文件行数（`python -c` 实测）：

| 文件 | 行数 |
|---|---|
| `module/composition_root.py` | 629 |
| `module/downloader.py` | 1970 |
| `module/adapters/webui/operations.py` | 1897 |
| `module/adapters/bot/host.py` | 417 |
| `module/transfer/runner.py` | 1564 |
| `module/transfer/live_transfer.py` | 1681 |

> 任务书写 `downloader.py` 1862 行，实测 1970 行（`LF=1970`，无 CRLF），以实测为准。

---

## H-01（最严重）`LiveTransferService` 用 `__getattr__` 透明代理宿主：33 个名字 / 125 处读点，其中 5 个是宿主私有方法

**现象**
`LiveTransferService` 没有任何声明的宿主接口。未在自己类里定义的 `self.X` 全部落到 `__getattr__`，直接转发给 facade 实例。

**证据**

`module/transfer/live_transfer.py:85-92`
```python
class LiveTransferService:
    """Listen/forward transfer behaviour extracted from the downloader facade."""

    def __init__(self, host):
        object.__setattr__(self, '_host', host)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, '_host'), name)
```

被代理的实际调用点（服务内部写法与宿主真实定义）：

`module/transfer/live_transfer.py:226` / `:1100`
```python
            self._log_system_chain(
                category='transfer',
                stage='download_start',
```
→ 实际执行的是 `module/downloader.py:761-764`
```python
    def _log_system_chain(self, **kwargs) -> None:
        tracer = getattr(self, 'system_log', None)
        if tracer is not None:
            tracer.log(**kwargs)
```

`module/transfer/live_transfer.py:1094`
```python
                    self._record_watch_event(
                        watch_id, origin_chat_id,
```
→ `module/downloader.py:715-729`（facade 私有方法）

`module/transfer/live_transfer.py:1110`
```python
            await self.create_download_task(message_ids=message.link, single_link=True)
```
→ `module/downloader.py:1615-1773`（facade 上的 159 行实现，非服务自己的方法）

**量化**（`final_numbers.py` / `implicit_host.py`）

| 项 | 数值 |
|---|---|
| `LiveTransferService` 自身类成员 | 27 |
| `self.<attr>` 读取（去重 / 总点） | 49 / 152 |
| **经 `__getattr__` 转发到宿主（去重 / 总点）** | **33 / 125** |
| 其中宿主**私有**方法（`_` 前缀） | **5 / 39** |
| 这 5 个私有方法 | `_log_system_chain`(26)、`_record_watch_event`(6)、`_watch_media_types_override`(3)、`_message_chain_context`(3)、`_forward_success_event_message`(1) |

即：**该服务 82% 的 `self.<attr>` 读点（125/152）不指向自己，而指向宿主**；其中 39 处依赖的是宿主的**私有**名字。

**为什么是耦合**
服务依赖的不是接口，而是「宿主类恰好有个同名属性」。`LiveTransferService` 无法脱离 facade 形状的对象被实例化，也无法被静态工具判定依赖集。

**具体代价**
1. 把 `downloader._log_system_chain` 改名 → 26 处调用点**零静态报错**；运行时抛 `AttributeError`，且报错信息指向的是**宿主类**，不是服务。实测（`repro_host_contract.py` 段 [C]）：
   ```text
   svc2.gcc (not defined by service) : HOST-gcc
   svc2.gc (absent on both)          : 'HostWithTypo' object has no attribute 'gc'
   -> the AttributeError names the HOST class, not LiveTransferService.
   ```
2. 任何 `hasattr(service, X)` / `getattr(service, X, default)` 探测都会「意外成功」（只要宿主有 X），实测 `svc.gc` 返回 `'HOST-GC'`、`svc.create_download_task()` 返回 `'HOST-CREATE'`。
3. 测试必须构造 facade 形状的宿主；`live_transfer_wire_case.py` 需手工塞 10 个属性（`test_assembly_cost.py` 输出）。

**最小改进建议**
按仓内已有的 `TransferPorts` 端口风格（`module/transfer/context.py`，构造点 `composition_root.py:430-468`）加一个 `LiveTransferPorts` dataclass，只含这 5 个私有方法 + 高频的 `gc/app/log/user`；`LiveTransferService.__init__(self, host, ports)`，`__getattr__` 保留作为过渡，但把上述 33 个名字逐个改成显式端口字段。改完后 `grep "self._log_system_chain" module/transfer/live_transfer.py` 应返回 0。

---

## H-02 `WebTransferRunner._resolve_method` 的 `is not` 判定对普通方法恒为真 → 兜底分支是死代码，同一语义在 runner 与 host 各有一份

**现象**
`runner.py:80-86` 用「实例属性对象是否 `is not` 类属性对象」判断宿主是否被 monkeypatch。对普通实例方法，每次 `getattr(instance, name)` 都会新建 bound method，与类上的 function **永不相等**，所以条件恒真，L85-86 永远不执行。

**证据**

`module/transfer/runner.py:80-86`
```python
    def _resolve_method(self, name: str):
        host_type = type(self._host)
        instance_method = getattr(self._host, name)
        class_method = getattr(host_type, name, None)
        if instance_method is not class_method:
            return instance_method
        return getattr(self, name)
```

实测（`repro_resolve_method.py`）
```text
[1] bound method identity
    h.m is h.m                    : False
    h.m is type(h).m              : False
    => runner.py:84 condition "is not" is True
[2] _resolve_method picks host impl, not runner-local impl
    resolves to                   : HOST-IMPLEMENTATION
[3] host whose class lacks the attr -> AttributeError, local fallback NOT used
    AttributeError                : 'BareHost' object has no attribute 'should_continue_web_transfer_task'
    runner DOES define its own    : WebTransferRunner.should_continue_web_transfer_task
    runner local impl result      : False
[4] staticmethod is the only shape where the branch can take lines 85-86
    h.static_marker is type(h).static_marker : True
```

「宿主优先、本地兜底」的双实现方法（`dual_impl.py`，4 个带完整本地实现）：
- `should_continue_web_transfer_task` `runner.py:95-104`（探 `host.web_task_manager`，否则读 `transfer_store`）
- `should_continue_web_transfer_item` `runner.py:106-115`
- `should_start_next_web_transfer_item` `runner.py:117-128`
- `settle_web_task_pause_request` `runner.py:130-150`

其中 3 个名字**同时**存在于 `WebTransferRunner` 与宿主（`dual_impl.py` 输出 `[probed on host AND locally implemented by runner] 3`）。

**量化**
- 宿主探针点：`runner.py` 9 个函数、28 处 `getattr/hasattr/callable(host...)`（`metrics.py`）。
- 探到的宿主属性名：10 个（`dual_impl.py`）。
- 双实现/双语义方法：4 个（上列）；其中与宿主同名的 3 个。

**为什么是耦合**
同一份「任务是否可继续」的判定逻辑存在两份实现，选哪一份不取决于设计，而取决于 `getattr` 的语义细节。三处 `should_continue_*` 的判定依据已分歧：`web_task_manager`（`operations.py:318-319` → task_manager）／`transfer_store.get_task`（`runner.py:99-104`）／`transfer_store.get_item` 状态（`runner.py:111-115`）。

**具体代价**
- 只改宿主侧实现（例如把某个 `PAUSED` 边界条件收紧），`runner.py` 的本地副本不会同步 → 两条路径行为不同，且没有任何测试会同时覆盖两条。
- 删掉宿主侧实现不会走本地兜底，而是 `AttributeError`（实测 [3]）→「兜底」这一保障实际上是假的。
- 只有 `staticmethod` 形状的属性才可能命中 `return getattr(self, name)`（实测 [4]），说明这段代码的意图与行为不一致。

**最小改进建议**
两选一，都要小：
(a) 删掉 `runner.py:95-150` 的 4 个本地实现，把 `should_continue_*` 收进 `WebTransferHost` Protocol 作为必需方法（宿主已全部具备），`_resolve_method` 退化为 `getattr(self._host, name)`；
(b) 保留兜底，但把判定改成显式 `override = self._host.__dict__.get(name)` 并给 4 个兜底各写一个直接单测，让两条路径都进 CI。

---

## H-03 同一个 `WebUITaskManager` 有两处接线，两处不一致（27 项 vs 21 项，6 项只在主路径存在）

**现象**
`composition_root.py:156-184` 在主装配路径构造 `WebUITaskManager`；`adapters/webui/operations.py:73-99` 在 `_require_web_task_manager(host)` 兜底路径里**又构造一遍**，依赖清单不同。

**证据**

主路径 `module/composition_root.py:156-184`（截取）
```python
        self.web_task_manager = WebUITaskManager(
            transfer_store_getter=self._transfer_store,
            diagnostic=self.diagnostic,
            loop_getter=self._loop,
            ...
            list_watches_getter=self.list_watches,
            persisted_watches_getter=self.watch_manager.persisted_watches,
            set_live_watch_status_getter=self.watch_manager.set_live_watch_status,
            watch_payload_from_record_getter=self.watch_manager.watch_payload_from_record,
            ...
            should_continue_web_transfer_task_getter=None,
        )
```

兜底路径 `module/adapters/webui/operations.py:73-99`（截取）
```python
    wm = WebUITaskManager(
        transfer_store_getter=lambda: getattr(host, 'transfer_store', None),
        diagnostic=getattr(host, 'diagnostic', None),
        loop_getter=lambda: getattr(host, 'loop', None),
        ...
        uploader_getter=lambda: getattr(host, 'uploader', None),
    )
    host.web_task_manager = wm
    return wm
```

**量化**（`wiring_matrix.py`）

| 项 | 数值 |
|---|---|
| `WebUITaskManager.__init__` 参数 | 31 |
| `composition_root.py:156` 接线 | 27 |
| `operations.py:73` 兜底接线 | 21 |
| 两处都接 | 21 |
| **只在主路径接（兜底为 `None`）** | **6**：`listener_restart_callback`、`list_watches_getter`、`persisted_watches_getter`、`set_live_watch_status_getter`、`watch_payload_from_record_getter`、`should_continue_web_transfer_task_getter` |
| 两处都不接 | 4：`is_web_transfer_task_schedulable_kwargs`、`cancel_task_uploads_getter`、`pause_task_uploads_getter`、`cancel_task_downloads_getter` |

后 4 个中，3 个是**可选 override**（`task_manager.py:336-365` 都有可用默认实现，`if callable(override)` 后走默认），不构成缺陷；`is_web_transfer_task_schedulable_kwargs` 默认 `{}` 且从不接线，是死参数（`task_manager.py:65`）。

**为什么是耦合**
同一对象两个构造点、两套依赖清单，二者靠「参数默认值都是 `None`」保持不报错 → 装配错误不会在启动时暴露。

**具体代价**
1. 走兜底路径（宿主没有 `web_task_manager` 时，例如 `_require_web_task_manager(self)` 被 `WebOperationsMixin` 的 17 个转发方法触发，`operations.py:315-386`）构造出的 manager 里 `_list_watches` / `_persisted_watches` / `_set_live_watch_status` / `_watch_payload_from_record` / `_should_continue_web_transfer_task` / `_listener_restart` 全是 `None` → 对应功能静默退化或 `TypeError: 'NoneType' object is not callable`，**只能运行时发现**。
2. 给 `WebUITaskManager` 加一个 getter 必须记得改 2 处；漏改兜底那处不会有任何提示（本次已实测到 6 处漏项）。
3. `operations.py:60-72` 还额外对 host 做 6 次 `if getattr(host,...) is None: host.X = ...` 的惰性补写，与 `composition_root.py:88-94` 的初始化重复。

**最小改进建议**
抽出模块级单一装配函数（放 `adapters/webui/task_manager.py` 或 `composition_root.py`）：
```python
def build_web_task_manager(host) -> WebUITaskManager: ...   # 27 项，唯一来源
```
`TrmdCompositionRoot.__init__` 与 `_require_web_task_manager` 都调它；`_require_web_task_manager` 从 40 行缩到 4 行。同时删掉 `operations.py:60-72` 的惰性补写。

---

## H-04 `_require_*` 重复完整构造 + `_create_standalone_transfer_engine` 重复 25 个端口接线，兜底一律用静默 `noop`

**现象**
每个被兜底重建的协作者都有两份构造代码，且兜底版本用 `lambda`/`_noop` 填充缺失依赖，失败不报错。

**证据**

`module/composition_root.py:234-258`（兜底，25 行）
```python
    def _require_watch_manager(self):
        if getattr(self, "watch_manager", None) is None:
            self.watch_manager = LiveWatchManager(
                listen_download_chat=getattr(self, "listen_download_chat", {}),
                listen_forward_chat=getattr(self, "listen_forward_chat", {}),
                web_pending_watches=getattr(self, "web_pending_watches", {}),
                web_watch_handler_clients=getattr(
                    self, "web_watch_handler_clients", {}
                ),
                transfer_store_getter=self._transfer_store,
                operation_submitter=getattr(
                    self,
                    "submit_web_operation",
                    lambda ot, p: {
                        "id": f"{ot}-0",
                        "status": TransferStatus.PENDING,
                    },
                ),
```
对应主路径 `module/composition_root.py:95-101`
```python
        self.watch_manager = LiveWatchManager(
            transfer_store_getter=self._transfer_store,
            operation_submitter=self.submit_web_operation,
            user_getter=self._runtime_user,
            app_getter=self._app,
            diagnostic=self.diagnostic,
        )
```

同类：`_require_pikpak_manager` `L263-282`（vs 主路径 `L114-124`，9 个 kwarg，兜底把 `refresh_counts` 换成内联 lambda `L272-276`）；`_require_progress_tracker` `L284-318`（vs 主路径 `L125-140`，14 个 kwarg，兜底把 5 个回调替换为 `lambda wu: None` / `lambda **kw: False` / `lambda **kw: None` `L295-309`）。

`module/composition_root.py:430-468`（`_build_transfer_ports`）与 `:492-617`（`_create_standalone_transfer_engine` 内部）各写一遍 `TransferPorts`：

| 端口组 | `_build_transfer_ports` 字段数 | standalone 字段数 | 字段名一致 |
|---|---|---|---|
| paths | 3 | 3 | ✔ |
| progress | 8 | 8 | ✔ |
| target | 4 | 4 | ✔ |
| storage | 3 | 3 | ✔ |
| runtime | 7 | 7 | ✔ |
| **合计** | **25** | **25** | **✔ 全同** |

`_create_standalone_transfer_engine` 每个字段都写成 `getattr(self, "X", _noop)`（126 行）。

**量化**
- `_require_*`：3 个、共 80 行兜底构造（`L234-258`=25、`L263-282`=20、`L284-318`=35）。
- 端口字段：25 个，在两处按同名重写（`extra_metrics.py` 段 [M1] `same_fields=True`）。
- `_create_standalone_transfer_engine` 内 `getattr(self, X, <noop>)` 兜底：全部 25 个字段。

**为什么是耦合**
调用方（`downloader.pikpak_target` `L519-521`、`LiveTransferService._watch_manager` `live_transfer.py:94-99`、`transfer_engine` property `L484-490`）无法知道拿到的是「装配好的实例」还是「静默降级实例」，两者的**类型相同、行为不同**。

**具体代价**
1. 给 `TransferProgressTracker` 或 `LiveWatchManager` 加一个依赖 → 必须改 2 处；漏改兜底那处不报错，表现为「归档没发生」「窗口没释放」这类无声故障（`L296-309` 全是 `lambda wu: None`）。
2. `TransferPorts` 加字段同理；漏改 standalone 版本则该端口是 `_noop`，而 `TransferEngine` 会照常运行。
3. 单测里通过 `__new__` 构造的 facade 走的正是这类降级路径 → 单测覆盖的行为与生产装配的行为可能不同（`test_assembly_cost.py` 实测 92 个 `__new__` 骨架）。
4. `composition_root.py:193` `transfer_store=self.transfer_store` 在构造时是 `None`（时序耦合，A4 负责，此处仅引用不展开）。

**最小改进建议**
1) 把三处构造各抽一个私有工厂并让 `_require_*` 复用（`_build_watch_manager()` / `_build_progress_tracker()` / `_build_pikpak_manager()`），`__init__` 与 `_require_*` 都调它 → 每个协作者只剩 1 份依赖清单。
2) `_create_standalone_transfer_engine` 改成 `ports=self._build_transfer_ports()`，只在**端口对象层面**做 `getattr` 兜底，消除 25 字段的第二份清单。
3) 兜底 lambda 改成显式 `_UnavailablePort` 具名类（调用即 `log.warning` 并返回类型正确的空值），让降级可见。

---

## H-05 `composition_root.py` 的 17 个 `*args/**kwargs` 透传 shim 抹掉真实签名

**现象**
17 个 shim 的签名统一是 `(self, *args, **kwargs)`，真实签名在 `TransferProgressTracker` 上。

**证据**

`module/composition_root.py:320-369`（全部 17 个，节选）
```python
    def on_transfer_file_ready(self, *args, **kwargs):
        return self._require_progress_tracker().on_transfer_file_ready(*args, **kwargs)

    def record_transfer_download_success(self, *args, **kwargs):
        return self._require_progress_tracker().record_transfer_download_success(*args, **kwargs)

    def transfer_percent(self, *args, **kwargs):
        return self._require_progress_tracker().transfer_percent(*args, **kwargs)
```

实测签名对比（`repro_host_contract.py` 段 [D]）
```text
record_transfer_download_success   shim(self, *args, **kwargs)
                                   real(self, with_upload: Optional[dict], message, file_path: str) -> None
transfer_percent                   shim(self, *args, **kwargs)
                                   real(current: int, total: int) -> str
```

**量化**：17 个 shim（`final_numbers.py`），全部落在 `L320-369` 的 50 行区间内。

**为什么是耦合**
shim 把 facade 变成 `TransferProgressTracker` 的**无类型镜像**：调用方写在 facade 上，实现对在 tracker 上，契约被抹平。

**具体代价**
- `TransferProgressTracker.record_transfer_download_success` 若加一个必填参数，facade 与调用点全部照旧通过静态检查，运行时才 `TypeError`（错误栈落在 tracker 内部，看起来像 tracker 的 bug）。
- IDE 跳转 / `inspect.signature` / `WebTransferHost` 这类 Protocol 在 facade 上看到的都是 `(*args, **kwargs)`。
- 与 H-04 叠加：`_require_progress_tracker()` 可能返回用 `lambda wu: None` 降级装配的实例，签名错配与降级叠加后定位成本翻倍。

**最小改进建议**
用真实签名重写这 17 个（可从 `TransferProgressTracker` 直接复制），或**直接删掉**这 17 个 shim，把调用方改成 `self.progress_tracker.X(...)`（`_progress_tracker()` getter `L371-372` 已存在，删除后调用点数量不变）。

---

## H-06 一个对象三个名字：别名共享 + 反向注入；且 `Bot.downloader` 有两条注入通道，只用了一条

**现象**
`TrmdCompositionRoot.__init__` 末尾把一个对象的属性平铺到自己和 `bot` 上，并把自身反向注入 `bot`。

**证据**

`module/composition_root.py:102-112`
```python
        # Host + Bot must share watch_manager dicts. Missing host aliases crash after
        # WebUI login when restore_live_transfer_watches reads self.listen_forward_chat.
        self.listen_download_chat = self.watch_manager.listen_download_chat
        self.listen_forward_chat = self.watch_manager.listen_forward_chat
        self.bot.listen_download_chat = self.watch_manager.listen_download_chat
        self.bot.listen_forward_chat = self.watch_manager.listen_forward_chat
        self.bot.downloader = self
        # Album dedupe state lives on Bot; live_transfer mutates it through the host.
        self.handle_media_groups = self.bot.handle_media_groups
        self.web_pending_watches = self.watch_manager.web_pending_watches
        self.web_watch_handler_clients = self.watch_manager.web_watch_handler_clients
```

`module/composition_root.py:141-152`
```python
        self.callback_handler = CallbackHandler(
            ...
            host=self,
            downloader_ref=self,
        )
```
`module/adapters/bot/callback_handler.py:60-61`
```python
        self._host = host if host is not None else downloader_ref
        self._downloader = self._host
```
`_downloader` 在 `callback_handler.py` 中被使用 **65 次**；`_host` 仅 2 次（`:60`、`:61`）。

`Bot` 的两条注入通道：
- 形参：`module/adapters/bot/bot.py:85-86` `def __init__(self, downloader=None, ...)` / `self.downloader = downloader`
- 事后赋值：`module/composition_root.py:108` `self.bot.downloader = self`
- 主装配 `composition_root.py:52-60` 构造 `Bot(` **没有**传 `downloader=`，只靠 L108。
- 读取方：`module/adapters/bot/bot.py:554-555`
  ```python
        dl = getattr(self, 'downloader', None)
        if not dl or not hasattr(dl, 'scan_media_for_cleanup'):
  ```
  与 `module/adapters/bot/guide_wizard.py:121-124`
  ```python
    def _host(self):
        if self._host_getter:
            return self._host_getter()
        return getattr(self._bot, "downloader", None)
  ```

**量化**
- facade 上来自协作者的平铺别名：5 个（`listen_download_chat`、`listen_forward_chat`、`web_pending_watches`、`web_watch_handler_clients`、`handle_media_groups`），`extra_metrics.py` 段 [M3] 显示 `WebOperationsMixin` 里 `watch_manager` 直接访问 10 次。
- 别名读取点：`listen_download_chat`/`listen_forward_chat` 全仓 37 处（`ports.py` 2、`live_transfer.py` 7、`live_watch.py` 15、`watch_applicator.py` 6、`composition_root.py` 7），其中 `operations.py:1610`/`:1621` 直接读 facade 别名。
- `bot.downloader`：写入 1 处（`composition_root.py:108`），构造形参 1 处，读取 2 处（`bot.py:554`、`guide_wizard.py:124`）。

**为什么是耦合**
同一份状态（4 个 dict + 1 个 set）同时挂在 `watch_manager`、facade、`bot` 三处；`bot.downloader` 是一个隐式的、可缺失的返回引用。

**具体代价**（含实测）
1. `_require_watch_manager` 兜底（`composition_root.py:234-258`）只重建 `self.watch_manager`，**不会补上 facade 别名**。实测（`extra_metrics.py` 段 [P2]）：
   ```text
   before: has listen_download_chat : False
   host.watch_manager is manager    : True
   after : has listen_download_chat : False
   manager dict is host dict        : False
   -> WebOperationsMixin L1610 reads `self.listen_download_chat` directly:
      AttributeError: 'TrmdCompositionRoot' object has no attribute 'listen_download_chat'
   ```
   即 `L102-103` 注释里担心的崩溃路径在兜底分支下**仍然存在**。
2. 任何在 `composition_root.py:108` 之前发生的 `bot.downloader` 读取都拿到 `None`，并且 `bot.py:555` 会把「未接线」和「不支持」合并成一句静默降级提示「⚠️ 媒体管理功能暂不可用。」（`bot.py:556-561`）。
3. 传同一个 self 两次（`host=self, downloader_ref=self`）使 `CallbackHandler` 的必需依赖集不可读；`_downloader` 65 次访问里大量是对**无关模块**的状态访问（如 `self._downloader.bot.guide_wizard`，`callback_handler.py:257`）。

**最小改进建议**
1. 删掉 `host=self, downloader_ref=self` 中的 `downloader_ref`，`CallbackHandler.__init__` 只留一个 `host`，把 `_downloader` 全量改名 `_host`（机械替换，65 处）。
2. 把 5 个别名改成 property，彻底消灭第二份字典，例如：
   ```python
   @property
   def listen_download_chat(self): return self.watch_manager.listen_download_chat
   ```
   （`operations.py:1610`/`:1621`、`callback_handler.py:547-551/567-571` 无需改动。）
3. `Bot.__init__` 删掉 `downloader=None` 形参，改为必填 `downloader`，删掉 `composition_root.py:108`。

---

## H-07 `download_complete_callback`：12 个参数在两个文件手工重排；`@DownloadTask.on_complete` 只包在 facade 上，engine 实现是裸的

**现象**
facade 的 `download_complete_callback` 是把 12 个参数按位置转给 `TransferEngine`；副作用装饰器挂在 facade 的 wrapper 上，engine 的公开实现没有装饰器。

**证据**

`module/downloader.py:1591-1611`
```python
    @DownloadTask.on_complete
    def download_complete_callback(
            self,
            sever_file_size,
            temp_file_path,
            link,
            message,
            file_name,
            retry_count,
            file_id,
            format_file_size,
            task_id,
            with_upload,
            diy_download_type,
            _future
    ):
        return self.transfer_engine.download_complete_callback(
            sever_file_size, temp_file_path, link, message, file_name,
            retry_count, file_id, format_file_size, task_id,
            with_upload, diy_download_type, _future
        )
```

`module/transfer/engine.py:601-615`（同 12 个参数的**同一顺序**）
```python
    def download_complete_callback(
        self,
        sever_file_size,
        temp_file_path,
        link,
        message,
        file_name,
        retry_count,
        file_id,
        format_file_size,
        task_id,
        with_upload,
        diy_download_type,
        _future
    ):
```

装饰器实现在 `module/domain/transfer_state/models.py:86-112`（`res = func(self, *args, **kwargs)` → `DownloadTask.add_file_name` / `COMPLETE_LINK` / `done_notice`）。

实测（`inspect`）：
```text
facade  is wrapped by @wraps?: True  file: module\domain\transfer_state\models.py line: 87
engine  is wrapped by @wraps?: False file: module\transfer\engine.py line: 601
same param names/order: True
```

**量化**：12 个位置参数在 2 个文件逐字重复；facade 侧 1 个 wrapper，engine 侧 0 个装饰器。

**为什么是耦合**
「参数清单」和「副作用归属」分散在两个文件：清单靠人肉保持同步，副作用挂在**转发方**而不是**实现方**。

**具体代价**
1. 12 个参数的顺序/名字在任一侧改动都不会被静态发现；facade 是位置转发，错位只会变成运行时的静默取值错误（例如 `task_id` 拿到 `format_file_size`）。
2. **结构已成立、尚未触发**：`TransferEngine.download_complete_callback` 是公开方法，直接调用它会**跳过** `DownloadTask.add_file_name` / `COMPLETE_LINK` / `done_notice`。当前仓内无直接调用（`grep -n "transfer_engine.download_complete_callback" module` 仅 `downloader.py:1607`；单测走的是 facade 版，`unit_tests/downloader_transfer_record_case.py:412`），因此这是风险而非现存 bug。

**最小改进建议**
把 `@DownloadTask.on_complete` 从 `downloader.py:1591` 移到 `engine.py:601`（副作用跟随实现），facade 的这 11 行 shim 直接删除，调用方（`downloader.py:1457`、`:1526`）改用 `self.transfer_engine.download_complete_callback(...)`。

---

## H-08 `self.__dict__.get(...)` 12 处绕过类属性与静态检查

**现象**
懒加载与可选依赖探测用 `self.__dict__.get('x')` 而不是 `getattr(self,'x',None)`；语义上「只看实例字典、不看类属性」，与类级默认值冲突。

**证据**（`extra_metrics.py` 段 [M4]）

`module/adapters/webui/operations.py:1635-1640`
```python
    def _ensure_watch_applicator(self) -> LiveWatchApplicator:
        applicator = self.__dict__.get('_watch_applicator')
        if applicator is None:
            applicator = LiveWatchApplicator(host=self)
            self._watch_applicator = applicator
        return applicator
```
`module/downloader.py:176-181`
```python
    def _ensure_live_transfer(self) -> LiveTransferService:
        service = self.__dict__.get('live_transfer')
        if service is None:
            service = LiveTransferService(host=self)
            self.live_transfer = service
        return service
```
其余 10 处：`operations.py:118`(`ctx`)、`:170`/`:410`(`comment_delay_scheduler`)、`:309`(`_web_operations_facade`)、`:738`(`app`)、`:739`(`transfer_store`)、`:743`(`media_manager`)、`:852`(`_archive_author_ops_impl`)、`:920`(`_system_log_archive_retry_ops_impl`)、`:1122`(`ctx`)。

**量化**：`operations.py` 11 处 + `downloader.py` 1 处 = 12 处。

**为什么是耦合**
facade 的状态来源有两条通道（实例字典 vs 类属性），而 `self.__dict__.get` 只认前者；`WebOperationsMixin.web_operation_counter: int = 0`（`operations.py:106`）这类类级默认值在 `self.__dict__.get('web_operation_counter')` 下会 `None`。

**具体代价**
- 「这个属性到底有没有默认值」不可 grep：`getattr` 搜索能命中，`__dict__.get` 搜索命中的是一堆字符串键。
- 若把 `live_transfer` 改成类级默认（例如类属性 `live_transfer = None`）以消除 AttributeError，`__dict__.get` 会忽略它 → 每次调用都新建一个 `LiveTransferService` 并覆盖实例属性（状态丢失）。
- 与 H-01 叠加：`LiveTransferService.__getattr__` 会把 `_host.__dict__` 里不存在但类上存在的名字查出来，两个「字典/属性」语义在同一对象上混用。

**最小改进建议**
统一改成 `getattr(self, '<name>', None)`（仓内已有此惯用法，如 `composition_root.py:210-232`、`operations.py:108-113`），或直接在类上声明 `_watch_applicator = None` / `live_transfer = None` 并删掉 `__dict__.get`。

---

## H-09 「上帝对象」的可测性代价：92 个 `__new__` 骨架、76 个手工塞入的 facade 属性

**现象**
仓内没有任何一个可用的窄接口；单测必须用 `object.__new__(...)` 绕过 `__init__`，再手工把 facade 的十来个属性一个个塞进去，然后才能测一个方法。

**证据**（`test_assembly_cost.py`）

```text
facade skeletons created with __new__ in unit_tests: 92
    47  unit_tests/transfer_store_webui_case.py
    17  unit_tests/downloader_transfer_record_case.py
     9  unit_tests/web_task_delete_case.py
     3  unit_tests/live_transfer_wire_case.py
     ...
distinct facade attributes hand-assigned by tests: 76
largest single-skeleton assemblies:
    44  unit_tests/transfer_store_webui_case.py :: downloader -> ['app', 'archive_pikpak_item', 'build_download_upload_meta', ..., 'web_watch_handler_clients']
    28  unit_tests/downloader_transfer_record_case.py :: downloader -> ['_scheduled_bot_progress_updates', 'app', ..., 'web_task_queue']
    18  unit_tests/web_task_delete_case.py :: downloader -> ['app', ..., 'web_task_queue']
```

代表片段 `unit_tests/downloader_transfer_record_case.py:29-51`
```python
                downloader = TelegramRestrictedMediaDownloader.__new__(TelegramRestrictedMediaDownloader)
                downloader.transfer_store = None
                downloader.gc = SimpleNamespace(upload_delete=False)
                downloader.local_storage_guard = LocalStorageGuard(...)
                downloader.download_upload_window = SimpleNamespace(acquire=lambda: None)
                downloader.app = SimpleNamespace(...)
                downloader.event = SimpleNamespace(wait=lambda: None, clear=lambda: None, set=lambda: None)
                downloader.pb = SimpleNamespace(progress=SimpleNamespace(add_task=lambda *args, **kwargs: 1))
                downloader.loop = asyncio.get_running_loop()
                downloader.queue = SimpleNamespace(put_nowait=lambda task: None, task_done=lambda: None)
```

**量化**：92 个骨架；76 个不同属性；单骨架最多 44 个属性；涉及 12 个测试文件。

**为什么是耦合**
测试被迫复刻宿主的**内部状态布局**——这正是「无法通过接口替换协作对象」的度量表现。

**具体代价**
- 每个新测试的平均前置成本是「手工复刻 7-44 个属性」（`test_assembly_cost.py` 的 `largest single-skeleton assemblies` 列表）。
- facade 属性改名会同时打破 12 个测试文件，且错误只在运行时出现（`SimpleNamespace` 没有静态校验）。
- 单测走的是 `__new__` 骨架，即 `__init__` 的 199 个 kwarg 装配从未被任何测试覆盖（`final_numbers.py`：`keyword args total: 199`；`unit_tests/` 中 `TrmdCompositionRoot()` 与 `TelegramRestrictedMediaDownloader()` 的出现次数均为 **0**，唯一完整构造点是 `main.py:13` `trmd = TelegramRestrictedMediaDownloader()`）。

**最小改进建议**
先只做最常用的一步：把单测反复手工塞的 7 个字段收成一个 `TransferRuntimeState` dataclass（`app`、`gc`、`loop`、`pb`、`queue`、`event`、`transfer_store`），facade 上放一个 `runtime` 属性；单测变成 `object.__new__(F)` + `f.runtime = TransferRuntimeState(...)`。无需改生产逻辑，即可把 92 个骨架的复刻字段数从 7-44 降到 1。

---

## H-10 `WebTransferHost` 只被当类型注解，从未被当作运行时校验使用；且只覆盖「名字存在」

**现象**
`runner.py:40-73` 的 `@runtime_checkable class WebTransferHost(Protocol)` 声明 15 个方法 + 6 个数据属性，但**全仓没有一处 `isinstance` 校验**，契约只被当作类型注解使用。

**证据**

`module/transfer/runner.py:39-48`
```python
@runtime_checkable
class WebTransferHost(Protocol):
    """Host dependencies for web transfer task execution."""
    app: object
    gc: object
    loop: asyncio.AbstractEventLoop
    transfer_store: object
    uploader: object
    transfer_engine: object
```
唯一使用点 `module/transfer/runner.py:77`
```python
    def __init__(self, host: WebTransferHost):
```

`grep -n "WebTransferHost" module/` 结果：只有 `runner.py:41`（定义）与 `runner.py:77`（注解），无 `isinstance`。

**量化**（`big_methods.py` + `final_numbers.py`）

| 协议成员在 facade 上的实现形态 | 个数 | 代表 |
|---|---|---|
| 1 行透传（passthrough） | 7 | `should_continue_web_transfer_task`（`operations.py:318-319`）、`should_continue_web_transfer_item`（`operations.py:321-323`）、`forward`（`downloader.py:769-770`）、`refresh_transfer_task_counts`（`downloader.py:383-384`）、`find_resumable_transfer_item`（`downloader.py:386-391`）、`skip_transfer_item_for_target_limit`（`downloader.py:582-598`）、`parse_web_transfer_link`（`downloader.py:619-620`） |
| 2 行胶水 | 1 | `build_transfer_upload_meta`（`downloader.py:448-476`） |
| 真实实现（5 个多语句 + 1 个被 `@DownloadTask.on_create_task` 装饰） | 6 | `wait_for_telegram_flood`、`check_type`、`runtime_message_filter`、`skip_transfer_item_for_media_type`、`skip_missing_web_transfer_range_message`、`create_download_task` |
| property | 1 | `pikpak_target`（`downloader.py:519-521`） |
| **合计** | **15** | 8 / 15 = 53% 是 1-2 行透传或胶水 |

另外，协议声明了 6 个数据属性（`app`/`gc`/`loop`/`transfer_store`/`uploader`/`transfer_engine`），它们只能由 `__init__` 提供；`object.__new__` 骨架下 5 个缺失（`transfer_engine` 因为 facade 上有同名 property `L484-490` 而存在）。

实测（`repro_host_contract.py` 段 [A]/[B]）：
```text
isinstance(bare, WebTransferHost) : False      # 缺 5 个数据属性
missing on bare instance: ['uploader', 'gc', 'transfer_store', 'loop', 'app']
```

**为什么是耦合**
`runtime_checkable` 的 `isinstance` 只检查**成员名是否存在**，不检查签名；而这个 host 的 15 个方法里有 8 个是 `*args/**kwargs` 透传或 2 行胶水（H-05 同源）。协议因此不约束签名，只约束名字。

**具体代价**
- **协议本来能当装配自检用，但全仓一次都没调用。** 实测 `isinstance(object.__new__(Facade), WebTransferHost)` 返回 `False` —— 原因正是协议声明的 6 个数据属性中 `app`/`gc`/`loop`/`transfer_store`/`uploader` 尚未由 `__init__` 写入（`transfer_engine` 因 facade 有同名 property 而存在）。也就是说这一行本来就能拦住「`__new__` 骨架 / 装配中断」的宿主；但 `grep -n "WebTransferHost" module/` 只有 `runner.py:41`（定义）与 `runner.py:77`（注解），`isinstance` 从未出现。→ 该保护完全未被使用。
- 加/改协议方法的参数不会触发任何错误（透传 shim 吸收一切）。
- 协议的实际价值目前 ≈ 文档 + 一个未被调用的检查点。

**最小改进建议**
不要删协议，做两件小事：(1) 在 `WebTransferRunner.__init__` 里把它变成真的前置条件
```python
if not isinstance(host, WebTransferHost):
    raise RuntimeError(f'WebTransferHost not wired: {host!r}')
```
(2) 把 H-05 的 8 个透传/胶水成员改成真实签名，让协议具备可校验的签名面。

---

## H-11 双向耦合：facade ⇄ 服务的乒乓调用链

**现象**
facade 把方法转给服务，服务又通过 H-01 的代理调回 facade；同一业务动作跨越两个类多次。

**证据**

`module/downloader.py:766-770`
```python
    async def _run_pikpak_archive_after_forward(self, *args, **kwargs):
        return await self._ensure_live_transfer()._run_pikpak_archive_after_forward(*args, **kwargs)

    async def forward(self, *args, **kwargs):
        return await self._ensure_live_transfer().forward(*args, **kwargs)
```
`module/transfer/live_transfer.py:771`（服务内）→ 实际调回 facade `downloader.py:748-749`
```python
    def _forward_success_event_message(self, message, media_group=None) -> str:
        return f'转发成功：{self._watch_forward_media_label(message, media_group)}'
```
`module/transfer/live_transfer.py:1110` → facade `downloader.py:1615` `create_download_task` → facade `downloader.py:1646` `self.__add_task(...)` → facade `downloader.py:1526` `self.download_complete_callback` → `engine.py:601`。

**量化**
- facade 上「纯转发到懒加载服务」的方法：`self._ensure_live_transfer()` 8 个方法、`self._ensure_transfer_runner()` 8 个方法、`self._require_pikpak_manager()` 8 个方法（`final_numbers.py`，共 24 个 / 89 个方法 ≈ 27%）。
- 反向：服务 → facade 125 个读点（H-01）。
- 服务对 facade **私有**方法的依赖：5 个名字 / 39 个点（H-01）。

**为什么是耦合**
依赖方向不是单向的：facade 依赖服务的接口，服务依赖 facade 的私有实现细节。任何一方的内部改动都可能穿透到另一方。

**具体代价**
- 追踪 `forward` 一个动作的完整路径要读 2 个文件至少 4 次跳转，且中间经过 `__getattr__`（栈里看不到）。
- `LiveTransferService` 无法单独测试（必须造 facade 形状宿主）；`_invoke` 的 monkeypatch 分支（`live_transfer.py:101-118`，探 `host.__dict__`）也是因为这个而存在。

**最小改进建议**
只单向化：按 H-01 把服务→宿主的 33 个名字改成显式端口。facade→服务的 24 个转发 shim 方向单一、可 grep，可保留。

---

## 度量否证的假设（明确不作为发现）

1. **三个 mixin 之间零同名冲突。** `mro_collisions.py` 实测：
   ```text
   total colliding names: 0
   [0] module.downloader.TelegramRestrictedMediaDownloader
   [1] module.composition_root.TrmdCompositionRoot
   [2] module.adapters.webui.operations.WebOperationsMixin
   [3] module.adapters.bot.host.BotHostMixin
   [4] builtins.object
   ```
   `BotHostMixin` 里 `user` 出现两次（`host.py:104-114`、`116-118`）是 `@property` + `@user.setter`，不是覆盖。

2. **`__add_task` 与 `resume_download` / `create_download_task` 不是近似重复。** 任务提示「1590 行附近 `download_complete_callback` 与 `__add_task` 的重复逻辑」在度量上不成立。`method_similarity.py`（有序 token difflib）：
   ```text
   __add_task   L1325-1577 src_lines= 253 ordered_tokens= 268
   resume_download L1111-1271 src_lines= 161 ordered_tokens= 192
   create_download_task L1615-1773 src_lines= 159 ordered_tokens= 55
   __add_task vs resume_download        ratio=0.126 longest_common_run=6 tokens
   __add_task vs create_download_task   ratio=0.050 longest_common_run=2 tokens
   ```
   最长公共片段 ≤ 6 token，谈不上「同一逻辑两份实现」。该处真实问题只有 H-07（12 参数手工重排 + 装饰器归属）。

3. **`_require_*` 不是隐藏魔法。** 它们是显式具名方法（`composition_root.py:234/263/284`），可 grep；问题在重复与静默 noop（H-04），不在不可见。

4. **`WebUITaskManager` 的 4 个未接线参数中 3 个不是缺陷。** `cancel_task_uploads_getter` / `pause_task_uploads_getter` / `cancel_task_downloads_getter` 是可选 override，`task_manager.py:336-365` 均有可用默认实现。

5. **`module/bot_host.py` / `module/web_operations.py` 不是重复实现**，是 3 行 / 4 行的 re-export shim（`bot_host.py:3`、`web_operations.py:3-4`），`architecture_guard_case.py:83` 也把它们登记为 facade 白名单。不计入耦合。

---

## 实际执行的命令（按发现）

解释器前缀统一为：
```powershell
cd E:\codebase\tgbot
```

```powershell
# 行数 / 编码核对
.\.venv313\Scripts\python.exe -c "for f in ['module/composition_root.py','module/downloader.py','module/transfer/runner.py','module/transfer/live_transfer.py']: b=open(f,'rb').read(); print(f, len(b), b.count(b'\n'), b.count(b'\r\n'))"

# H-01 / H-09 / H-11（隐式宿主面、测试装配成本）
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\implicit_host.py
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\test_assembly_cost.py
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\repro_host_contract.py

# H-02（_resolve_method 恒真 + 双实现）
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\repro_resolve_method.py
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\dual_impl.py

# H-03 / H-04（两套接线、端口字段重复）
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\wiring_matrix.py
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\web_task_manager_wiring.py
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\wiring_per_collaborator.py
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\extra_metrics.py

# H-05 / H-10（签名抹平、协议实现形态）
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\big_methods.py

# H-07（12 参数一致 / 装饰器归属）
.\.venv313\Scripts\python.exe -c "import sys,inspect; sys.path.insert(0, r'E:\codebase\tgbot'); from module.downloader import TelegramRestrictedMediaDownloader as F; from module.transfer.engine import TransferEngine as E; fd, ed = F.download_complete_callback, E.download_complete_callback; print('facade wrapped:', hasattr(fd,'__wrapped__'), fd.__code__.co_firstlineno); print('engine wrapped:', hasattr(ed,'__wrapped__'), ed.__code__.co_firstlineno); print('same params:', list(inspect.signature(fd).parameters)==list(inspect.signature(ed).parameters))"

# 否证项
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\mro_collisions.py
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\method_similarity.py

# 汇总数字
.\.venv313\Scripts\python.exe tmp\coupling-audit\01-host\final_numbers.py

# 检索（ripgrep 语义，用于 H-06 / H-07 / H-10 的「全仓无读取点」结论）
#   pattern: downloader        path: E:\codebase\tgbot   include: *.py
#   pattern: WebTransferHost   path: E:\codebase\tgbot\module
#   pattern: __dict__          path: E:\codebase\tgbot\module
#   pattern: _require_         path: E:\codebase\tgbot\module
```

---

## 脚本清单（均在 `tmp/coupling-audit/01-host/`）

| 脚本 | 用途 | 支撑发现 |
|---|---|---|
| `metrics.py` | 首轮 AST 量化（CR/DL/runner/live_transfer） | 全部 |
| `classify.py` | facade 方法三分类（透传/胶水/实现） | H-05、H-08、H-11 |
| `dump_methods.py` | 逐方法行号 + 语句数索引 | H-05、H-07 |
| `implicit_host.py` | `__getattr__` 代理面 / `host.X` 读取面 | H-01、H-11 |
| `dual_impl.py` | host 探针清单 + 双实现配对 | H-02 |
| `repro_resolve_method.py` | 可执行证明：`_resolve_method` 恒真、兜底不可达 | H-02 |
| `repro_host_contract.py` | 可执行证明：代理越界、异常归属、签名抹平 | H-01、H-05、H-10 |
| `extra_metrics.py` | 端口字段重复、接线量、访问惯用法、`__dict__.get`、P1/P2 证明 | H-04、H-06、H-08 |
| `wiring_matrix.py` | `WebUITaskManager` 31 参数 × 2 接线点矩阵 | H-03 |
| `web_task_manager_wiring.py` | 两处接线差异 + 默认值 | H-03 |
| `wiring_per_collaborator.py` | 每个协作者的 kwarg 数 | H-03、H-04 |
| `mro_collisions.py` | MRO 与同名冲突 | 否证项 1 |
| `method_similarity.py` | 有序 token 相似度 | 否证项 2 |
| `test_assembly_cost.py` | 单测骨架与手工属性统计 | H-09 |
| `big_methods.py` | 协议成员实现形态 | H-10 |
| `final_numbers.py` | 全部头条数字一次输出 | 全部 |
