# transfer_store_webui_case.py 随机失败（flaky）修复报告

责任人：flake-fixer　　范围：仅 `unit_tests/transfer_store_webui_case.py`（未改 `module/` 任何文件，未 commit / push）

---

## 0. 结论摘要

| 项目 | 结果 |
| --- | --- |
| 初始定位（服务器每个响应后关连接 → **复用连接**导致失败） | **被实测推翻**：每请求新建连接（`fresh-conn`）同样以 3.33% 复现 |
| 真正根因 | **带 body 的请求被服务器「没读 body 就回应并关闭」→ Windows 回 RST → 客户端丢掉内核里尚未取走的响应字节**，`getresponse()` 随机抛 `ConnectionAbortedError(10053)` |
| 实测失败率（修复前，按请求计） | `POST /api/auth/submit`（带 body，未鉴权 401）**2/400 = 0.50%**；不带 body 的同路由 0/400；`GET` 0/400 |
| 实测失败率（修复前，放大脚本） | 60 轮 × 15 次易触发请求 = 1080 次：**6 次失败（0.56%/请求）** |
| 修复后（同一放大脚本） | 60 轮 × 15 = 1080 次 + 40 轮 × 15 = 720 次：**0 失败** |
| 整文件 pytest | `106 passed`；连续 12 轮 **1272/1272 全绿**（0 失败） |
| 全量回归 | 4 次：**721 passed / EXIT=0**、719+2（他人在改的文件）、720+1（他人在改的文件）、**721 passed / EXIT=0**；`transfer_store_webui_case.py` 每次 106/106 全绿 |
| 反向验证 | 3 个「必然失败」场景 100% 照旧失败（见第 6.5 节） |
| 是否会掩盖真实缺陷 | **不会**：任何完整 HTTP 响应（401/400/404/500、错误体、JSON 解析、断言）都不触发重放；重放只针对「连接层异常 + 一个响应字节都没拿到 + 请求带 body」，且最多 2 次，系统性故障照旧失败。详见第 7 节 |

---

## 1. 复现脚本

主脚本：`tmp/flake-fix/repro_login_reuse.py`

* 每轮启动一个全新 `WebUiServer`，在**同一个** `HTTPConnection` 上依次发：
  1. `K` 次 `POST /api/auth/submit`（带 JSON body，未鉴权）→ 期望 401　← 竞态触发点
  2. `GET /api/auth/status` → 期望 401
  3. `POST /api/auth/login`（复用同一连接）→ 期望 200
  4. `GET /api/auth/status`（复用同一连接 + cookie）→ 期望 200
* `loops=K` 是竞态放大器（每多一次机会就多一次掷骰子）；`variant=fresh-conn` 用于证明「换连接」无效；
  `body=0` 是机理对照；`fix=1` 表示改用修复后的 `connect_webui`。
* 失败会打印**失败步骤 + socket 状态 + 完整 traceback**。

辅助脚本：

* `tmp/flake-fix/probe_rate.py`：真实服务器上分 phase 计量失败率、失败时服务器**是否已经回应**、客户端本地端口是否被复用。
* `tmp/flake-fix/probe_rst.py`：用裸 TCP 服务器确认 Windows 上「响应 + RST」的客户端可见语义。
* `tmp/flake-fix/verify_helper.py`：确定性验证 `WebUiTestConnection` 的重放边界（9 条断言，不依赖 OS 竞态概率）。

---

## 2. 修复前基线（原始输出）

### 2.1 典型失败（原始 traceback，节选）

来源：`tmp/flake-fix/after_fix_compare_prefix_60.txt`（修复前同会话基线）

```
[round 006] CONNECTION-FLAKE step=unauth_submit#6 ConnectionAbortedError: [WinError 10053] 你的主机中的软件中止了一个已建立的连接。
Traceback (most recent call last):
  File "E:\codebase\tgbot\tmp\flake-fix\repro_login_reuse.py", line 198, in main
  ...
  File ".../Lib/http/client.py", line 1430, in getresponse
    response.begin()
  File ".../Lib/http/client.py", line 331, in begin
    version, status, reason = self._read_status()
  File ".../Lib/http/client.py", line 292, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
  File ".../Lib/socket.py", line 719, in readinto
    return self._sock.recv_into(b)
ConnectionAbortedError: [WinError 10053] 你的主机中的软件中止了一个已建立的连接。
```

### 2.2 修复前失败率（各次原始 summary 行）

```
# tmp/flake-fix/after_fix_compare_prefix_60.txt   （修复前，60 轮 × 15 = 1080 次易触发请求）
=== fix=0 variant=same-conn body=1 sleep=0.0 delay_read=0.0 rounds=60 loops=15 requests≈1080 failures=6 connection_flakes=6 rate=10.00% ===

# tmp/flake-fix/baseline_60_same_conn.txt         （修复前，脚本早期版本，实际轮数以输出为准）
=== variant=same-conn sleep=0.0 rounds=30 failures=3 connection_flakes=3 rate=10.00% ===

# tmp/flake-fix/baseline_amplified_body.txt       （修复前，30 轮 × 15）
=== fix=0 variant=same-conn body=1 sleep=0.0 rounds=30 loops=15 requests≈540 failures=1 connection_flakes=1 rate=3.33% ===

# tmp/flake-fix/probe_rate_400.txt                （修复前，真实服务器逐 phase 计数）
  POST /api/auth/submit +body        iterations=400 failures=2 distinct_local_ports=400 reused_ports=0
  POST /api/auth/submit no-body      iterations=400 failures=0 distinct_local_ports=400 reused_ports=0
  GET /api/auth/status               iterations=400 failures=0 distinct_local_ports=400 reused_ports=0
```

失败率随机器负载在 0.2%–10%/轮（0.5%/请求量级）之间浮动，所以「跑 30 轮不失败」本身不构成证据；
下面用**放大脚本 + 确定性边界测试 + 反向验证**三层证据闭环。

---

## 3. 根因（并修正初始假设）

### 3.1 初始假设被推翻

> 原假设：服务器（`protocol_version` 为 stdlib 默认 HTTP/1.0）每个响应后关闭连接，导致复用连接的下一个请求失败。

实测不成立，三条独立证据：

1. **`fresh-conn`（每次请求新建 `HTTPConnection`）同样复现**：
   `tmp/flake-fix/baseline_60_fresh-conn.txt` → `rounds=60 failures=2`（3.33%），失败步骤同样是 `unauth_submit`。
2. **客户端本来就在重连**：服务器响应是 `HTTP/1.0` 且不带 `Connection: keep-alive`，`http.client` 在
   `getresponse()` 里就把 socket 关掉了（`response.will_close=True` → `self.close()`，`conn.sock is None`）。
   实测每步 `sock_before=None`，即下一个请求 100% 是新 TCP 连接。
3. **本地端口零复用**：`probe_rate.py` 里 400 次请求用了 400 个不同的本地端口（`reused_ports=0`），
   TIME_WAIT / 同 4 元组重连假设也不成立。

### 3.2 真正的机制

```
客户端                          服务器（module/adapters/webui/server.py）
  |-- POST /api/auth/submit ------>|
  |    headers + JSON body          | _route_post -> handle_post_public(只处理 /api/auth/login)
  |                                 |          -> _check_auth() 未通过 -> 401，**从未读请求体**
  |<---- HTTP/1.0 401 + close ------| 响应写完；连接关闭时套接字里还有未读 body
  |                                 |   => Windows 发 RST（而不是干净的 FIN）
  |  RST 与响应字节竞速：            |
  |   - 客户端先取走响应 -> 成功 (99.5%)
  |   - RST 先被内核处理 -> 收队列里的响应字节被丢弃 -> recv 报 WinError 10053
```

关键实测数据（`probe_rate.py`）：

```
[POST /api/auth/submit +body] #301 FAIL port=38061 server_responded=True ConnectionAbortedError: [WinError 10053] ...
[POST /api/auth/submit +body] #314 FAIL port=38074 server_responded=True ConnectionAbortedError: [WinError 10053] ...
```

* `server_responded=True`：诊断日志里**有该请求的响应行**，即**服务器已经正常回应**；这不是服务器漏处理，也不是请求丢了。
* 触发条件与 `body` 强相关：带 body 2/400 失败，不带 body 0/400，`GET` 0/400。
  机理上只有「关闭时还有未读 body」才会生成 RST。
* 对照实验：把未鉴权 POST 的 body 去掉后 60 轮 0 失败（`baseline_60_same-conn-no-post.txt`）。
* `probe_rst.py`（Windows 语义对照，各 20 次）：
  * 强制 RST 后**立即**读：20/20 成功（所以「RST 必然毁掉响应」不成立，是竞速）；
  * 强制 RST 后延迟 50ms 读：20/20 失败（`WinError 10054`）；
  * 「不读 body 就正常 close」+ 延迟读：16/20 失败 —— 证明**未读 body 的优雅关闭在 Windows 上确实会退化成 RST**。

### 3.3 为什么错误码是 10053 而不是 10054

`10054` 是「对端重置」，`10053` 是「本机软件中止了一个已建立的连接」。本案例里响应字节已经进过客户端接收队列、
随后被 RST 处理丢弃，Windows 报的是 10053（本机中止）。`probe_rst.py` 里人为强制 RST 且未读走响应时报 10054，
两者都是 `ConnectionError` 子类，客户端可见类别一致。

> 备注：服务器「不回读请求体就关闭连接」是 RFC 允许的行为（客户端应容忍），但会退化成 RST。
> 更彻底的修法在服务器侧（回响应前 drain 请求体），但本任务明确**禁止改 `module/`**，所以只在测试侧修。

---

## 4. 方案选择

| 方案 | 评估 | 结论 |
| --- | --- | --- |
| (a) 每次请求用新连接 | 实测**无效**：`fresh-conn` 2/60 仍复现。客户端本来就已经在重连，换连接对象改变不了「服务器未读 body → RST」 | 否决 |
| (b) 复用连接 + 连接层异常重连重发 | 有效；但必须收紧边界并论证幂等性 | **采用** |
| (c) 让服务器支持 keep-alive | 需要改 `module/`（本任务禁止）；而且会把响应从 HTTP/1.0 变成持久连接，改变被测语义 | 否决 |
| (d) 其它：去掉请求 body / 吞掉异常 / 放宽断言 | 都会削弱测试覆盖（不再验证「带 body 的未鉴权请求返回 401」），属于掩盖问题 | 否决 |

### 4.1 采用的方案

在测试文件里新增 `WebUiTestConnection(http.client.HTTPConnection)`，并把 25 处连接构造点统一换成
`connect_webui(server)`。`getresponse()` 在**连接层异常**时，按下面的边界重放同一个请求：

1. 只捕获 `ConnectionError`（覆盖 `ConnectionAbortedError` / `ConnectionResetError` / `RemoteDisconnected`）；
   **裸 `BadStatusLine`（畸形状态行）不重放** —— 那是协议层真实缺陷的信号（比题目给的候选集合更严格）。
2. 只在 `getresponse()` 抛出时重放：即**一个完整响应都没拿到**。一旦拿到 `HTTPResponse`，后续 body 读取、
   JSON 解析、断言全部不再重放。
3. 只重放**带 body** 的请求（`str`/`bytes`/`bytearray`，可重复发送）；不带 body 的请求出现连接层异常一律原样抛出。
4. 最多 `MAX_REPLAYS = 2` 次（合计 3 次尝试），用尽后把最后一次异常抛给用例。

### 4.2 幂等性论证（为什么不会重复执行副作用）

* 能触发这个 RST 的请求，**一定是服务器在读取 body 之前就拒掉的请求**：
  `_check_request_origin`（403）/ `_check_auth`（401）/ `_check_setup_ready`（409）/ 路由匹配（404）
  全部发生在 `_read_json()` **之前**（见 `module/adapters/webui/server.py` 的 `_route_post/_route_patch/...`
  与 `handlers/__init__.py` 的 dispatcher）。body 没被读，处理函数根本没跑，重放不可能产生第二次副作用。
  本文件里实际会踩到的两处正是这类：未鉴权 `POST /api/auth/submit`（401）、
  已下线路由 `POST /api/forwards`（404）。
* 反过来，**真正改状态的请求都先读完了 body**（`POST /api/tasks`、`POST /api/watches`、
  `PATCH /api/settings`、`/api/uploads` 等都要 `_read_json()` 拿到 payload），套接字里没有未读数据，
  产生不了这个 RST；它们若出现连接层故障，测试仍会在有限次重放后失败（第 6.5 节 C 已验证）。
* 重放拿到的是**服务器真实的新响应**（状态码/响应体/头都来自服务器），断言照旧；不存在伪造响应。

### 4.3 实施中发现并修掉的自研 bug

第一版 `request()` 覆写的 `headers` 默认值写成了 `None`，而 CPython 3.13 的
`HTTPConnection.request` 不会把 `None` 归一化成 `{}`，直接 `TypeError`。整文件跑暴露了 2 个用例
（`test_telegram_auth_status_requires_webui_session`、`test_webui_delete_task_uses_operations_cleanup`），
已修为 `headers = {} if headers is None else headers` 并与直接调用 `http.client` 行为对齐
（原始失败输出留档：`tmp/flake-fix/pytest_file_after_fix_1.txt`）。

---

## 5. 改动清单（仅 1 个文件）

`unit_tests/transfer_store_webui_case.py`（+98 / −24）：

| 位置 | 改动 |
| --- | --- |
| L21–L37 | 与 `webui_http_hardening_case.py` 等兄弟用例一致：只在 module 导入期间清 `sys.argv`，导入后还原。修掉「`module/utils/parser.py` 在 import 期 `parse_args()` 吞掉 pytest argv → 单文件跑必然 INTERNALERROR」的既存问题（见第 8 节） |
| L49–L107 | 新增 `WebUiTestConnection`：有限重放（边界见 4.1） |
| L110–L112 | 新增工厂 `connect_webui(server, timeout=5)` |
| 25 处（原 `http.client.HTTPConnection(server.host, server.port, timeout=5)`，其中 1 处无 timeout） | 改为 `connect_webui(server)` / `connect_webui(server, timeout=None)` |

未改 `module/` 下任何文件；未 git commit / push。文件编码 UTF-8 无 BOM，
工作区换行与仓库现状一致（`core.autocrlf=true`：索引 LF、工作区 CRLF，未混行）。

> ⚠️ 提交归属说明：本次会话进行中，**另一位 teammate 在提交自己的组合根改动时把工作区整体提交了**，
> 我的改动因此被一并带入 commit `46a9cee`（`feat(test): 建立真实集成基线，修组合根 event loop 脆弱点`）。
> 我本人没有执行任何 `git commit` / `git push`。当前 `git diff HEAD -- unit_tests/transfer_store_webui_case.py`
> 为空，且工作区文件哈希 `AB6F66049199E64283723BDCC4402C7ED7499A98F128DB74C74215AE4F5E4264`
> 与本报告验证过的版本一致（即提交内容 = 已验证内容）。

---

## 6. 验证

### 6.1 复现脚本（≥30 轮，0 失败）

```
# tmp/flake-fix/after_fix_verified_60.txt —— 60 轮 × 15 = 1080 次易触发请求
=== fix=1 variant=same-conn body=1 sleep=0.0 delay_read=0.0 rounds=60 loops=15 requests≈1080 failures=0 connection_flakes=0 rate=0.00% ===

# tmp/flake-fix/after_fix_verified_40.txt —— 追加 40 轮 × 15 = 720 次
=== fix=1 variant=same-conn body=1 sleep=0.0 delay_read=0.0 rounds=40 loops=15 requests≈720 failures=0 connection_flakes=0 rate=0.00% ===
```

对照（同一会话、同一脚本、去掉 `fix=1`）：

```
=== fix=0 variant=same-conn body=1 sleep=0.0 delay_read=0.0 rounds=60 loops=15 requests≈1080 failures=6 connection_flakes=6 rate=10.00% ===
```

合计修复后 **1800 次**易触发请求 0 失败；若失败率仍为 0.56%/请求，出现 0 次失败的概率约 `e^-10 ≈ 0.005%`。

### 6.2 整文件

```
.venv313\Scripts\python.exe -m pytest unit_tests/transfer_store_webui_case.py -q --no-header -p no:cacheprovider
........................................................................ [ 67%]
..................................                                       [100%]
106 passed in 44.60s
```

连续 12 轮原始输出（`tmp/flake-fix/file_runs_12x.txt`）：

```
run 1 exit=0 :: 106 passed in 49.00s
run 2 exit=0 :: 106 passed in 46.01s
run 3 exit=0 :: 106 passed in 46.18s
...
run 12 exit=0 :: 106 passed in 44.19s
TOTAL_FAILED_RUNS=0 / 12
```

合计 **12 × 106 = 1272 个用例通过、0 失败**。

### 6.3 全量回归

```
# 第 1 次（改动全部完成后的干净结果，tmp/flake-fix/run_tests_final.txt）
.venv313\Scripts\python.exe tmp\run_tests.py
files: 70
summary: 721 passed, 1 warning, 27 subtests passed in 94.82s (0:01:34)
EXIT=0
```

说明：本次仓库工作区里另有他人未提交的 `unit_tests/composition_root_integration_case.py`（新增 7 个用例），
所以是 70 个文件 / 721 passed，而不是基线时的 69 个文件 / 714 passed（714 + 7 = 721，数字自洽，无回归）。

#### 6.3.1 复跑时观察到的、与本次改动无关的偶发失败（如实记录）

同一命令复跑时，`transfer_store_webui_case.py` 的 106 个用例**每次全绿**，但工作区里他人正在改动的文件偶发失败：

| 复跑 | 结果 | 失败位置 | 排除与本次改动相关的证据 |
| --- | --- | --- | --- |
| #2（`run_tests_final_2.txt`） | 719 passed / 2 failed | `module_bootstrap_case.py::test_build_script_imports_constants_without_side_effects`、`::test_import_module_is_side_effect_free` | 这两个用例都是 `subprocess.run([sys.executable, "-c", ...])` 的隔离导入检查；单独跑 5/5 全绿（每轮约 13s），紧跟本文件跑 4/4 全绿 |
| #3（`full_suite_direct.txt`，直接 pytest 全量 70 文件） | 720 passed / 1 failed | `composition_root_integration_case.py::test_05_submit_transfer_task_persists_to_sqlite`（`AssertionError: 1 != 0`） | 该文件是他人本次新建、尚未提交的工作成果（`?? unit_tests/composition_root_integration_case.py`），与本次改动无关 |
| #4（`run_tests_final_3.txt`，最终态复核） | **721 passed / EXIT=0** | — | 干净 |

四次全量结果的共同点：`unit_tests/transfer_store_webui_case.py` **每次 106/106 全绿**；
失败点在别的文件、且复跑位置会漂移（典型的并发编辑 / 负载敏感问题），不属于本次 flake 修复范围。

### 6.4 重放边界的确定性验证（9/9 PASS）

`tmp/flake-fix/verify_helper.py`（用脚本化裸 TCP 服务器精确制造各种客户端可见状况，不依赖概率）：

| 场景 | 期望 | 实测 |
| --- | --- | --- |
| 1. 失败一次后恢复正常 | 透明重放，拿到真实 401，服务器 accept 2 次 | PASS |
| 2. 一直失败 | 重放 `MAX_REPLAYS` 次后把 `RemoteDisconnected` 抛出（不吞） | PASS |
| 3. RST 一次后恢复正常 | 同类异常同样透明重放 | PASS |
| 4a/4b/4c. 完整 404 / 500 / 401 | **原样返回，只 accept 1 次、replayed=0** | PASS |
| 5. 不带 body 的请求失败 | 不重放，立即抛错（access 1 次） | PASS |
| 6. 畸形状态行 | 不重放，抛 `BadStatusLine`（access 1 次） | PASS |
| 7. 半个状态行后 RST | 响应不完整 → 允许重放；用尽后仍抛错 | PASS |

### 6.5 反向验证（临时改坏 → 必须失败 → 已还原并校验哈希）

| # | 临时改动 | 期望 | 实测 |
| --- | --- | --- | --- |
| A | `test_webui_no_longer_exposes_separate_forward_endpoint` 里把 `assertEqual(404, response.status)` 改成 `200` | 失败 | `AssertionError: 200 != 404` ✅（`reverse_a_404_expect_200.txt`） |
| B | `test_telegram_auth_status_requires_webui_session` 里把**竞态那一步**的 `assertEqual(401, ...)` 改成 `200` | 失败 | `AssertionError: 200 != 401` ✅（`reverse_b_401_expect_200.txt`） |
| C | 把该用例的连接指向无人监听的端口（真实连接层故障） | 失败，不被重放吞掉 | `ConnectionRefusedError: [WinError 10061]` ✅（`reverse_c_dead_port.txt`） |

还原后 `unit_tests/transfer_store_webui_case.py` 与实验前快照
`tmp/flake-fix/transfer_store_webui_case.fixed.bak` **哈希一致**
（`AB6F66049199E64283723BDCC4402C7ED7499A98F128DB74C74215AE4F5E4264`）。

---

## 7. 残留风险与「是否掩盖真实缺陷」的明确结论

**结论：不会掩盖真实缺陷。** 依据：

1. **HTTP 层完全不在重放范围内**：任何完整响应（含 401/400/404/500、错误体、头、JSON 解析）都只被断言，
   从不重放；`BadStatusLine` 也不重放。反向验证 A/B 证明「期望与服务器实际响应不符」照旧失败。
2. **重放范围极窄**：连接层异常 + 一个响应字节都没拿到 + 请求带 body，三者同时满足才重放，最多 2 次。
   不带 body 的请求（GET/DELETE 等）一旦连接层异常立即失败（反向验证 C + 6.4 场景 5/6）。
3. **系统性故障不会被吞**：重放耗尽后异常原样抛出（6.4 场景 2/7）；把连接指向死端口立即失败。
4. **不改变被测语义**：重放后拿到的仍是服务器真实响应，断言、状态码、响应体全部照旧。

已知的、刻意接受的两点（都已论证过影响可忽略）：

* 若某个**改状态的请求**（body 已被服务器读完）恰好遇到**非本竞态**的连接层故障（例如进程被杀、网卡重置），
  该请求会被重放一次，理论上可能重复执行一次副作用。理由：(i) 这类请求的 body 已被读取，套接字里没有未读数据，
  产生不了本竞态，因此这条路径与本次修复的 flake 无关；(ii) 本套件对这类请求基本都断言了精确数量
  （任务/监听/记录条数、返回 id 列表），重复执行会以**断言失败**的形式暴露，而不是静默通过；
  (iii) 该场景在本次全部复现实验中从未出现（1800 次请求 0 次）。
* 服务器侧「未读 body 就关闭连接会让 Windows 发 RST」这个**既存健壮性缺口仍然存在**（本次被明确禁止改 `module/`）。
  更彻底的修法是在回响应/关闭前 drain 请求体，或在测试侧继续依赖本 helper。建议作为独立任务单独评估。
* **同一竞态还会波及其它 WebUI 测试文件**（本次改动范围只允许 `transfer_store_webui_case.py`，故未动）：
  `unit_tests/webui_http_hardening_case.py`（L330/L349 带 body POST 到 401/403 路由）、
  `unit_tests/webui_spa_routing_case.py`（带 body POST）仍在直接 `http.client.HTTPConnection` + 复用连接。
  建议后续把本 helper 提取到 `unit_tests/` 下的共享模块后统一替换（提取本身不改变语义）。

---

## 8. 附：顺手修掉的既存问题（单文件跑 pytest 直接 INTERNALERROR）

按题目给定的命令整文件跑，原本会立刻 INTERNALERROR：

```
usage: __main__.py [-h] [-v] [-q] [-c CONFIG] [-s SESSION] [-t TEMP] [-w [PORT]] [-m {ONCE,SESSION}]
__main__.py: error: unrecognized arguments: unit_tests/transfer_store_webui_case.py --no-header -p no:cacheprovider
INTERNALERROR> ...  File "E:\codebase\tgbot\module\utils\parser.py", line 99, in <module>
INTERNALERROR> SystemExit: 2
```

原因：`module/utils/parser.py` 第 99 行在 **import 期**就 `parse_args()`；本文件顶层的
`from module.adapters.webui.task_manager import ...` 会一路 import 到它，于是 pytest 自己的 argv 被当成未知参数。
整套跑之所以没事，是因为按文件名排序更早的测试模块在 import 期清过 `sys.argv`（例如 `app_filename_case.py` 第 12 行）。

* 这是**既存问题、与本次改动无关**：把 `HEAD` 版本原样拷成 `tmp/flake-fix/pristine_case.py` 单独跑 pytest，
  得到同样 `SystemExit: 2`。
* 修法就是照抄兄弟用例的写法（`unit_tests/webui_http_hardening_case.py` L25–L31 等约 40 个文件）：
  只在 module 导入期间 `sys.argv = [sys.argv[0]]`，导入后还原。导入后的 argv 与整套跑保持一致，
  不改变任何被测行为；副作用是本文件现在可以**单独指定用例名**跑（例如
  `pytest unit_tests/transfer_store_webui_case.py::TransferStoreWebUiCase::test_webui_no_longer_exposes_separate_forward_endpoint`），
  这正是反向验证能精确命中单个用例的前提。

---

## 9. 交付物清单

| 文件 | 说明 |
| --- | --- |
| `unit_tests/transfer_store_webui_case.py` | 唯一代码改动（helper + 25 处连接构造点 + argv 守卫） |
| `tmp/flake-fix/report.md` | 本报告 |
| `tmp/flake-fix/repro_login_reuse.py` | 复现 / 验证主脚本（放大 + `fix=0/1` + 变体） |
| `tmp/flake-fix/probe_rate.py` | 逐请求失败率 / 服务器是否已回应 / 端口复用计量 |
| `tmp/flake-fix/probe_rst.py` | Windows RST 客户端语义对照实验 |
| `tmp/flake-fix/verify_helper.py` | 重放边界确定性验证（9/9 PASS） |
| `tmp/flake-fix/*.txt` | 全部原始输出留档（基线、修复后、反向验证） |
