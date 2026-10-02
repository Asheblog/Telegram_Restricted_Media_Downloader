# A3 — 构建 / 前端资源 / 测试基建耦合取证

- 仓库：`E:\codebase\tgbot`（TRMD）
- HEAD：`1f7a43bbafb758c649f2f6beaf2a7e91363f1c2f`（工作树除 `tmp/` 外干净）
- 取证方式：**只读**。未修改 `module/`、`unit_tests/`、前端资源；未执行前端构建（未运行 tailwind CLI 的写盘模式、未运行 `build_frontend.py` 的 `main()`）；只读调用 `build_frontend.py` 的纯函数在内存中重建以做比对。
- 写入范围：仅 `tmp/coupling-audit/03-build/`
- 解释器：可用解释器是 `.venv313\Scripts\python.exe`（3.13.7）。`.venv\Scripts\python.exe` 是 3.14.0a5 且 C 扩展 ABI 不匹配（见 F5），因此所有 Python 命令如无特别说明均用 `.venv313`。

发现类型标注：**[已证实耦合]** = 有可复现命令/字节级证据；**[风格偏好]** = 无量化代价，仅约定问题。

---

## 总览：最严重 3 条

| 排名 | ID | 一句话 |
|---|---|---|
| 1 | **F1/F3** | `assets.py` 是 1.2 MB 生成物，占 `module/` 全部 Python 字节的 **41.4%**、占近 200 次提交全仓改动行的 **13.1%**；唯一覆盖它的 43 个测试断言的是「生成物」而不是「源文件」，因此**改源文件忘重生成 → 测试全绿 + 页面陈旧** |
| 2 | **F4** | 无 `[tool.pytest.ini_options]` + 测试命名 `*_case.py` ⇒ 默认调用 `pytest unit_tests` **收集 0 个用例、exit 5**；702 个用例只有显式传文件名才会跑；仓库唯一架构守门 `architecture_guard_case.py` 因此从未自动执行；唯一 CI 是 tag 触发的 Docker 构建，不含任何测试 |
| 3 | **F5** | 默认环境 `.venv` 是 **Python 3.14.0a5**，`import yaml` 即 **0xC0000005 访问违例**（不是可读报错）；`.venv313`（3.13.7）正常。且 `build.py` 明确拒绝 ≥3.14，与 `pyproject` 的 `>=3.13.2` 无上界不一致 |

---

## F1 `assets.py`：1.2 MB 生成物，同一份 CSS/字体在三处重复内联

**类型：[已证实耦合]**

### 现象
`module/adapters/webui/assets.py` 是仓库最大的单个文件，由 `build_frontend.py` 生成，内容是 **3 份完整 HTML 文档 + 1 份字体 base64 字典**，以 `r"""..."""` 原始字符串字面量内联在 Python 源码里。

### 证据：文件:行号
- `module/adapters/webui/build_frontend.py:110-123` — 用 f-string 拼接源码并写盘：
  ```
  output = f'''# coding=UTF-8
  # WebUI 静态资源 — 由 build_frontend.py 自动生成
  # 请勿手动编辑。模板文件在 templates/ 和 static/ 目录。

  WEB_UI_HTML = r"""{desktop_html}"""
  ...
  FONTS = {font_dict_src}
  '''
  OUTPUT_FILE.write_text(output, encoding="utf-8")
  ```
- `module/adapters/webui/build_frontend.py:94` — `tailwind_css = read_text(DIST_DIR / "tailwind.min.css")`
- `module/adapters/webui/build_frontend.py:42-46` — `_inject_css()` 做字符串替换：`/* fonts.css */`、`/* tailwind.min.css */`
- `module/adapters/webui/build_frontend.py:62-64` — desktop：`<!-- VIEWS PLACEHOLDER -->` / `/* shared.js */` / `/* desktop.js */`
- `module/adapters/webui/build_frontend.py:75-90` — mobile 是**代码内 f-string 硬编码外壳**（含 `<title>`、`<style>` 两个、`class="mob-body bg-bg text-text"`），不是模板文件
- `module/adapters/webui/build_frontend.py:27-39` — `_load_font_data()` 把 13 个 `.woff2` 全部 `base64.b64encode`
- `module/adapters/webui/assets.py:5` / `:8756` / `:15350` — 三个常量起始行
- `module/adapters/webui/assets.py:226` / `:8977` / `:15571` — **`tailwindcss v4.1.18` 的同一份压缩 CSS 出现 3 次**
- `module/adapters/webui/assets.py:15665-15679` — `FONTS` 字典
- 唯一生产消费者：`module/adapters/webui/handlers/static_pages.py:6`
  `from module.adapters.webui.assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML, LOGIN_PAGE_HTML, FONTS`（`:55`、`:67` 使用）

### 证据：命令原始输出
```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s1_assets_stats.py
[assets.py] bytes=1203917 lines=15679 chars=1180314
[assets.py] top-level names=4 string/dict consts=4
  CONST WEB_UI_HTML              bytes=    447549 lines=5-8754 span=8750
  CONST WEB_UI_MOBILE_HTML       bytes=    403987 lines=8756-15348 span=6593
  CONST LOGIN_PAGE_HTML          bytes=    113629 lines=15350-15663 span=314
  CONST FONTS                    bytes=        -1 lines=15665-15679 span=15
[FONTS] entries=13 dict_lines=15
[FONTS] total_b64_chars=222444 decoded_bytes=166833 biggest=('d8e4fe0452aa.woff2', 64428)
[dup] 40-line window duplication per const (sha1):
  WEB_UI_HTML: inner_lines=8749 windows=8709 unique=8707 dup_windows=2
  WEB_UI_MOBILE_HTML: inner_lines=6593 windows=6553 unique=6553 dup_windows=0
  LOGIN_PAGE_HTML: inner_lines=313 windows=273 unique=273 dup_windows=0
```
```
$ # 形态
tailwind.min.css: bytes=100891 lines=2 max_line=100824 newline_count=1
static/tailwind.css: bytes=61555 lines=2502
```

### 量化
| 项 | 数值 |
|---|---|
| assets.py 体积 / 行数 | 1,203,917 B / **15,679 行**（任务描述中的 14,917 行是旧数据） |
| 占 `module/` 全部 145 个 `.py` 字节比 | **41.4%**（1,203,917 / 2,909,765） |
| 顶层常量数 | **4 个**（3 个 HTML + 1 个 FONTS 字典） |
| 最大常量 | `WEB_UI_HTML` = **447,549 B**（8,750 行） |
| tailwind.min.css 3 份内联 | 100,891 × 3 = **302,673 B = assets.py 的 25.1%** |
| FONTS base64 | 222,444 字符 → 166,833 B 原始字体 = **assets.py 的 18.5%** |
| fonts.css 3 份内联 | 9,234 × 3 = 27,702 B |
| base64 内联资源 | **有**，仅 13 个 woff2（无图片/无其它二进制） |
| 文件内重复资源块 | 40 行 sha1 窗口：`WEB_UI_HTML` 8,709 窗口仅 2 个重复 → **单文件内基本无重复**；重复发生在**跨常量**（tailwind × 3、fonts.css × 3） |
| 前端源文件 | 23 个（4 模板 + 6 static + 13 woff2），合计 14,446 行；另有中间产物 `dist/tailwind.min.css` |
| 生成物 vs 源文件 | 23 个源文件 → **4 个常量**，非一一对应（见 F2） |

### 具体代价
1. **审查成本**：全仓 churn 第一名。近 200 次提交中 assets.py 被改 **141 次（70.5%）**，`+10,793/-3,082 = 13,875 行`，占全仓改动行（106,287）的 **13.1%**；第二名 `unit_tests/transfer_store_webui_case.py` 仅 6,015 行。单次提交 diff 中位数约 150 行，**最大 2,215 行**（`e6818d1`）。任何前端一行的改动都在 review 里堆出一个机器生成的大 diff，reviewer 实际上无法审阅其内容。
2. **内存/解析**：`compile()` 这个文件实测 10.0 ms（1.2 MB 源码），每个导入 WebUI 静态页的进程都要付这份钱；文件本身不构成运行时峰值（exec 后仅 4 个常量），但它是纯搬运负担。
3. **单一真相被稀释**：同一份 tailwind CSS 维护 3 份拷贝，字体 CSS 3 份。想全局改一个 CSS 变量必须改 3 处（虽然由生成器保证，但人工读 `assets.py` 时看到的是 3 处）。

### 最小改进建议
- 首选：把 `assets.py` 移出 git（加入 `.gitignore`）并在 `module.bootstrap.initialize()` 或 Docker 构建期生成。收益：churn 从 13.1% 降到 ~0，同时消除 F3 的漂移风险（因为不再有提交的副本）。
- 次选（改动最小）：保留提交，但给 CI 加一条「重生成后 `git diff --exit-code`」守门 —— 见 F3 的可运行脚本。
- 无论哪种：把 `fonts.css` / `tailwind.min.css` 从 3 份内联改为 3 个 HTML 引用同一份外部资源（或抽成一个共享常量拼接），可去掉 302,673 + 27,702 ≈ **330 KB 的冗余**。

---

## F2 生成链路：两条命令、零处记录；`build.py` 与前端无关

**类型：[已证实耦合]**

### 现象
改前端源文件后需要**手工顺序执行两条命令**，而这两条命令既不在 `package.json` 里，也不在任何文档或 CI 里。

### 证据：文件:行号（实际通读，非推测）
- `package.json:10-12` —— scripts 只有一个占位：
  ```json
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  ```
  **没有** `build` / `build:css` / `build:frontend`。
- `package.json:24-27` —— devDependencies 有 `@tailwindcss/cli@^4.1.18`、`tailwindcss@^4.1.18`，说明 tailwind 编译是预期步骤。
- `build.py:1-139` —— **与前端完全无关**。它是 Nuitka 单文件打包脚本：`build.py:129-137` 拼 `nuitka --standalone --onefile ... --include-data-file=... main.py`，通篇不读 `templates/`、`static/`、`dist/`，也不调用 `build_frontend.py`。
- `module/adapters/webui/build_frontend.py:16-20` —— 输入/输出目录常量；`:93-129` `main()` 是唯一写盘点。
- 生成链路（读 `build_frontend.py` 得到的确切流程）：
  ```
  static/tailwind.css  --(tailwind CLI, 未记录)-->  dist/tailwind.min.css
  templates/{base,views,login,mobile_body}.html
  static/{watch_ui_helpers,shared,desktop,mobile_script}.js
  static/fonts.css + static/fonts/*.woff2
        --(python module/adapters/webui/build_frontend.py)-->  assets.py
  ```
- 全仓（排除 `.worktrees/`、`node_modules`、`.venv*`、`tmp/`）grep `tailwindcss/cli|@tailwindcss/cli|npx tailwind|tailwindcss -i` **只命中 `package.json:25` 与 `package-lock.json`**（依赖声明），无任何调用命令记录。

### 证据：命令原始输出
```
$ node_modules\.bin\tailwindcss.cmd --help
≈ tailwindcss v4.1.18
Usage:
  tailwindcss [--input input.css] [--output output.css] [--watch] [options…]
Options:
  -i, --input ················· Input file
  -o, --output ················ Output file [default: `-`]
  -m, --minify ················ Optimize and minify the output
```
```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s3_mutation_cost.py
== 场景A: static/shared.js 改 1 个字符 ==
  WEB_UI_HTML: asset_lines_changed=+1/-1 hunks=1 bytes_delta=1
  WEB_UI_MOBILE_HTML: asset_lines_changed=+1/-1 hunks=1 bytes_delta=1
== 场景B: 新增 1 个 Tailwind 工具类（需重跑 tailwind CLI）==
  WEB_UI_HTML: changed_lines=+3/-1 bytes_delta=31
  WEB_UI_MOBILE_HTML: changed_lines=+3/-1 bytes_delta=31
  LOGIN_PAGE_HTML: changed_lines=+3/-1 bytes_delta=31
== 场景C: 只改 desktop.js（仅 desktop 常量）==
  WEB_UI_HTML: changed_lines=+1 /-1
```

### 量化
- **必须执行的命令数**：2 条（tailwind CLI + build_frontend），且顺序不可颠倒、都不在自动化里。
- 源→常量映射（**非一一对应**）：
  | 源文件 | 进入哪个常量 | 份数 |
  |---|---|---|
  | `static/shared.js`、`static/watch_ui_helpers.js` | `WEB_UI_HTML` + `WEB_UI_MOBILE_HTML` | 2 |
  | `static/tailwind.css`→`dist/tailwind.min.css` | 全部 3 个 | 3 |
  | `static/fonts.css` | 全部 3 个 | 3 |
  | `templates/base.html`、`views.html`、`static/desktop.js` | `WEB_UI_HTML` | 1 |
  | `templates/login.html` | `LOGIN_PAGE_HTML` | 1 |
  | `templates/mobile_body.html`、`static/mobile_script.js` + `build_frontend.py:75-90` 内嵌外壳 | `WEB_UI_MOBILE_HTML` | 1 |
  | `static/fonts/*.woff2` × 13 | `FONTS` 字典（base64） | 1 |
- **改一行前端需要重新生成什么**：若只改 JS/HTML 文案 → 只需第 2 条命令；若涉及任何 Tailwind class（新增/删除类名）→ 必须**先**重跑 tailwind CLI 再重跑 build_frontend。
- **git diff 会有多大**：改 1 个字符 → 1~2 个「行」变化（数字上很小）；但改 1 个 tailwind class → `dist/tailwind.min.css` 是 **2 行、单行最长 100,824 字符** 的压缩产物，git diff 显示「1 行变更」而实际内容是 3 × ~100 KB 的巨型行 ⇒ **`git diff` 文本量约 300 KB**，且 `--stat` 会显示极小的行数变化而严重低估实际改动体积。

### 具体代价
- 新人/新会话必须凭记忆重建 tailwind 命令（`-i module/adapters/webui/static/tailwind.css -o module/adapters/webui/dist/tailwind.min.css --minify`），否则 `dist/tailwind.min.css` 不更新 → class 不生效，但 `assets.py` 可能仍被重生成，产生「样式莫名其妙不对」的假象。
- 两步手工操作没有幂等入口，无法在 CI 里一键复现或校验。

### 最小改进建议
在 `package.json` 补两个脚本，把隐式知识变成可执行契约：
```json
"scripts": {
  "build:css": "tailwindcss -i module/adapters/webui/static/tailwind.css -o module/adapters/webui/dist/tailwind.min.css --minify",
  "build:frontend": "npm run build:css && python module/adapters/webui/build_frontend.py"
}
```

---

## F3 双份真相：目前**同步**，但没有任何守门，且现有测试无法发现漂移

**类型：[已证实耦合]**（风险为潜在，非当前已发生）

### 现象
`templates/` + `static/` 是真相源，`assets.py` 是提交进 git 的副本。**当前两者逐字节一致**，但仓库里没有任何机制保证它会继续一致；而唯一覆盖 UI 的 43 个测试断言的是副本本身。

### 证据：命令原始输出（同步状态）
```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s2_drift_check.py
[source sizes] tailwind.min.css=100891 fonts.css=9234 font_files=13
[rebuilt] WEB_UI_HTML=447549B, WEB_UI_MOBILE_HTML=403987B, LOGIN_PAGE_HTML=113629B
[assets]  WEB_UI_HTML=447549B, WEB_UI_MOBILE_HTML=403987B, LOGIN_PAGE_HTML=113629B
[compare] WEB_UI_HTML            rebuilt_sha=701673d0968112d5 assets_sha=701673d0968112d5 IDENTICAL=True len_diff=0
[compare] WEB_UI_MOBILE_HTML     rebuilt_sha=17b58da21238927f assets_sha=17b58da21238927f IDENTICAL=True len_diff=0
[compare] LOGIN_PAGE_HTML        rebuilt_sha=20b222d8ac670077 assets_sha=20b222d8ac670077 IDENTICAL=True len_diff=0
[fonts dict] assets_keys=13 source_files=13 keys_equal=True
  fonts_all_identical=True
OVERALL_STALE=False
```
（该脚本只调用 `build_frontend.py` 的 `build_*` 纯函数，**不调用 `main()`**，因此不写盘。）

### 证据：文件:行号 + 命令原始输出（守门缺失）
`unit_tests/web_ui_assets_case.py` 是唯一覆盖 UI 的测试，43 个测试方法、273 个 `assertIn`：
```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s6_churn_shims.py
== 3) web_ui_assets_case.py 是否引用前端源文件（能否检出漂移）==
  'static/': 0 次
  'templates/': 0 次
  'desktop.js': 0 次
  'shared.js': 0 次
  'mobile_script.js': 0 次
  'views.html': 0 次
  'mobile_body.html': 0 次
  'base.html': 0 次
  'login.html': 0 次
  'build_frontend': 0 次
  'tailwind.css': 0 次
  'dist/': 0 次
  assertIn/assertNotIn 次数 = 273
  测试方法数 = 43
```
- `unit_tests/web_ui_assets_case.py:10` 从 **shim** 导入：`from module.web_ui_assets import WEB_UI_HTML, WEB_UI_MOBILE_HTML, LOGIN_PAGE_HTML`
- 该文件还硬编码了**压缩后**的 CSS 片段，共 10 条形似 minify 产物，例如：
  - `'.login-page{background-color:var(--color-bg);width:100%;'`（`:105`）
  - `'@media (min-width:64rem){.download-upload-align-spacer{min-height:184px}'`（`:220`）
  - `'.task-items-table .task-item-col-error{width:28%}'`（`:313`）
- CI 侧：`.github/workflows/release_docker.yml:3-6` 只在 `v*.*.*` tag push 触发，全部步骤是 buildx + GHCR 登录 + build/push，**没有任何测试或校验步骤**。
- `Dockerfile:54` `COPY module/ ./module/` —— 直接拷已提交的 `assets.py`，构建期**不重新生成**。

### 量化
| 风险方向 | 触发条件 | 会不会被发现 |
|---|---|---|
| **假阴性（真问题）** | 改 `static/*.js` / `templates/*.html`，忘记跑 build_frontend | **不会**。`web_ui_assets_case.py` 43 个测试全绿（它读旧副本），CI 无校验，Docker 直接拷旧副本 ⇒ 发布出去的是旧页面 |
| **假阳性（假问题）** | 升级 tailwind（如 v4.1.18 → v4.2），或压缩器输出格式微调，源文件一字未改 | **会红**。10 条断言绑定压缩后字面串，43 个测试连带失败，误导排查方向 |
- 覆盖缺口量：23 个前端源文件中，被测试直接引用的 = **0 个**；被间接覆盖 = 全部（经由副本）。

### 具体代价
「源已修、页面仍旧」这类不一致在当前基建下**无法被自动化发现**，只能靠人工 diff。一旦发生，表现是 UI 行为与代码不符且全绿，排查成本极高。

### 最小改进建议
1. 立即可用：把下面的脚本放进 `unit_tests/`（或 CI），它已验证可用且能检出 1 字节级别的漂移。本次已实现于 `tmp/coupling-audit/03-build/check_frontend_drift.py`：
```python
# 重建后逐字节比对，只读、不写 assets.py
built = bf.build_desktop_html(tailwind, fonts_css)
if built != act["WEB_UI_HTML"]:
    print("FRONTEND DRIFT DETECTED"); sys.exit(1)
```
   实跑结果：
   ```
   $ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\check_frontend_drift.py
   FRONTEND IN SYNC — assets.py 与 templates/ static/ dist/ 逐字节一致
   EXITCODE=0
   $ # 灵敏度验证（内存中加 1 行 CSS，不写盘）
   baseline identical = True
   after 1-line css change identical = False
   ```
2. CI 加一步：`python module/adapters/webui/build_frontend.py && git diff --exit-code -- module/adapters/webui/assets.py`
3. 把 `web_ui_assets_case.py` 中 10 条压缩产物字面串断言改为对**源文件**或语义标记（如 `data-nav`、`id=`）断言，去掉对压缩器输出的绑定。

---

## F4 测试基建：默认调用收集 0 个用例（exit 5），702 个用例需显式传文件名

**类型：[已证实耦合]**

### 现象
- `pyproject.toml` 无 pytest 配置；pytest 默认 `python_files = test_*.py *_test.py`，而 `unit_tests/` 下测试全部叫 `*_case.py`。
- `pytest unit_tests` 收集 **0** 个用例并返回 exit 5；显式传文件名才会收集（pytest 对命令行直接指定的路径会绕过 `python_files` 匹配）。

### 证据：文件:行号
- `pyproject.toml` 全文 31 行，**无 `[tool.pytest.ini_options]`**。相关段仅为：
  - `pyproject.toml:11` `requires-python = ">=3.13.2"`
  - `pyproject.toml:24-25` `[dependency-groups]` / `dev = ["pytest>=8.0"]`
  - `pyproject.toml:27-31` `[tool.hatch.build.targets.wheel]` / `[tool.uv]` —— 之后文件结束
- 无 `pytest.ini` / `tox.ini` / `setup.cfg` / `noxfile.py` / `Makefile` / `conftest.py`；无 `.pre-commit-config.yaml`；`.git/hooks/pre-commit` 不存在。
- `.github/workflows/` 下**只有** `release_docker.yml`，无任何测试 job。
- 仓库自己的计划文档写的就是这条无效命令：`docs/superpowers/plans/2026-08-14-decouple-module-side-effects.md:105` → `python -m pytest unit_tests/ -q`；`.worktrees/watches-action-consolidation/CONTEXT.md:209` → 「测试: `unit_tests/`，pytest 运行」。

### 证据：命令原始输出（实测）
```
$ .\.venv\Scripts\python.exe -m pytest unit_tests -q
no tests ran in 0.01s
EXITCODE=5
```
```
$ .\.venv313\Scripts\python.exe -m pytest unit_tests -q
no tests ran in 0.03s
EXITCODE=5
```
```
$ .\.venv313\Scripts\python.exe -m pytest unit_tests --collect-only -q
no tests collected in 0.01s
EXITCODE=5
```
```
$ .\.venv313\Scripts\python.exe -m pytest unit_tests/web_ui_assets_case.py -q
...........................................                              [100%]
43 passed in 0.29s
EXITCODE=0
```
```
$ # 显式传全部 66 个 *_case.py
$ .\.venv313\Scripts\python.exe -m pytest <66 个文件> -q
........................................................................ [ 10%]
...（中间省略）...
702 passed, 1 warning, 27 subtests passed in 78.54s (0:01:18)
EXITCODE=0
```
唯一 warning（真实信号，非本任务范围但值得记）：
```
unit_tests/web_task_deferred_pause_case.py::...::test_recover_pausing_without_active_item_converges_to_paused
  E:\codebase\tgbot\module\persistence\store\schema.py:272: RuntimeWarning:
  coroutine 'TelegramUploader.send_media_worker' was never awaited
```

### 量化
| 项 | 数值 |
|---|---|
| `unit_tests/*_case.py` | **66** 个 |
| 匹配默认 pytest 模式（`test_*.py`/`*_test.py`）的测试文件 | **0** 个 |
| 默认调用收集用例数 / 退出码 | **0** / **exit 5** |
| 显式传名调用用例数 / 耗时 / 退出码 | **702 passed + 27 subtests** / 78.54 s / **exit 0** |
| 差异倍数 | **0 → 702**（差 702 个用例） |
| 依赖 `pyrogram_stub` 的测试文件 | **60 / 66**（`install_pyrogram_stub` 出现 **119** 次，覆盖 60 个文件） |
| 含 `unittest.main()` 的文件 | 63 |
| 唯一架构守门 `architecture_guard_case.py` | 314 行 / 7 个测试，**同样只有显式传名才跑** |

### 具体代价
1. **静默空跑**：exit 5（NO_TESTS_COLLECTED）在很多 CI/脚本里与 exit 0 一样被当作「没失败」，或干脆因为命令看起来成功而被忽略。任何按文档/直觉执行 `pytest unit_tests` 的人得到的是一个**什么都没验证**的绿灯。
2. **架构守门形同虚设**：`unit_tests/architecture_guard_case.py` 是仓库唯一的架构约束执行者，包含 7 条硬约束：
   - `test_module_import_graph_has_no_cycles`（`:158-196` 无 import 环）
   - `test_subpackages_do_not_import_top_level_shims`（`:198-219` 子包不得 import 顶层 shim）
   - `test_no_layer_inversions`（`:221-246` core/domain/infra/…/adapters 分层方向）
   - `test_composed_host_resolves_every_attribute_read`（`:248-286` 宿主属性解析，防 `AttributeError` 线上崩溃）
   - `test_composition_root_has_no_reflective_getattr`（`:288-293`）
   - `test_transfer_ports_have_no_host_reflection`（`:295-298`）
   - `test_top_level_contains_only_facade_and_shims`（`:300-310`）
   由于默认调用收集 0 个用例、CI 不跑测试，**这 7 条约束实际上从未自动执行**。这是 F6（shim 层无限增长）能长期存在的直接原因。
3. **无 CI 兜底**：`.github/workflows/release_docker.yml:3-6` 仅监听 tag；`Dockerfile` 只做 `pip install` + `COPY`，不含测试。所以「702 个用例」这个数字在自动化里从未出现过。

### 最小改进建议（1 段配置，收益 0 → 702）
```toml
# pyproject.toml
[tool.pytest.ini_options]
python_files = ["test_*.py", "*_test.py", "*_case.py"]
testpaths = ["unit_tests"]
```
并在 `.github/workflows/` 增加一个 `on: [push, pull_request]` 的 `pytest -q` job（当前 CI 无任何测试步骤）。

---

## F5 环境耦合：默认 `.venv` 是 3.14.0a5，`import yaml` 直接访问违例

**类型：[已证实耦合]**

### 现象
仓库并存两个虚拟环境。任务默认指向的 `.venv` 是 **Python 3.14.0a5**，其 `yaml` C 扩展 ABI 不匹配，导入即触发 Windows 访问违例（进程级崩溃，无 Python traceback）。可用的 `.venv313` 是 3.13.7。

### 证据：文件:行号 / 命令原始输出
```
$ Get-Content .venv\pyvenv.cfg
home = C:\Users\wanglinyu\AppData\Local\Programs\Python\Python314
implementation = CPython
uv = 0.8.22
version_info = 3.14.0a5
include-system-site-packages = false
prompt = telegram-restricted-media-downloader
```
```
$ Get-Content .venv313\pyvenv.cfg
home = C:\Users\wanglinyu\AppData\Roaming\uv\python\cpython-3.13.7-windows-x86_64-none
implementation = CPython
uv = 0.8.22
version_info = 3.13.7
include-system-site-packages = false
```
```
$ .\.venv\Scripts\python.exe -V
Python 3.14.0a5
$ .\.venv\Scripts\python.exe -c "import yaml; print('yaml ok', yaml.__version__)"
EXITCODE=-1073741819          # 0xC0000005 STATUS_ACCESS_VIOLATION
$ .\.venv313\Scripts\python.exe -c "import yaml; print('yaml ok', yaml.__version__)"
yaml ok 6.0.3
EXITCODE=0
$ .\.venv313\Scripts\python.exe -c "import module; print('module ok', module.__version__)"
module ok 0.2.248
EXITCODE=0
```
```
$ .\.venv\Scripts\python.exe -m pytest unit_tests/web_ui_assets_case.py -q
Windows fatal exception: access violation
  ...
  File "E:\codebase\tgbot\.venv\Lib\site-packages\yaml\cyaml.py", line 7 in <module>
  File "E:\codebase\tgbot\.venv\Lib\site-packages\yaml\__init__.py", line 13 in <module>
  File "E:\codebase\tgbot\module\__init__.py", line 10 in <module>
  File "E:\codebase\tgbot\unit_tests\web_ui_assets_case.py", line 10 in <module>
EXITCODE=-1073741819
```
`module/__init__.py:10` 是崩溃入口：`import yaml  # noqa: F401  (re-exported for back-compat: ``from module import yaml``)`。
另一队友的 `tmp/pytest_full.txt` 记录了**完全相同**的崩溃栈，说明可复现、非偶发。

### 量化
- 受影响命令：任何用 `.venv` 且经由 `module/__init__.py` 的 Python 执行（测试、`main.py`、`build.py`）——**全部**。
- 崩溃形态：`STATUS_ACCESS_VIOLATION`，退出码 `-1073741819`，**不是** Python 异常，无法被 `try/except`、`pytest` 或 `unittest` 捕获成可读失败。
- 口径不一致：`build.py:95-111` 的 `check_python_version()` 硬编码 `min_version=(3,9,0)`、`max_version=(3,14,0)`，要求 `3.9.0 ≤ Python < 3.14.0`；而 `pyproject.toml:11` 是 `requires-python = ">=3.13.2"`（无上界）。用 `.venv`（3.14.0a5）跑 `python build.py` 会在**第一步** `sys.exit(1)`（因为 `(3,14,0) < (3,14,0)` 为假），连打包都不可能开始。

### 具体代价
新会话/新机器上，默认环境会给出**进程级崩溃**而不是「依赖没装好」这类可行动信息，极易被误判成代码问题（本次任务描述里就一度被误述为「全量测试原生崩溃」）。同时 `build.py` 与 `pyproject.toml` 对 Python 上界的口径不一致，是同一类「环境契约没有单点定义」的问题。

### 最小改进建议
1. 删除 `.venv` 或重建为 3.13.x，并在 `README.md`/`CONTRIBUTING` 明确「默认使用 `.venv313`」。
2. 把版本上界写进 `pyproject.toml` 与 `build.py` 对齐：`requires-python = ">=3.13.2,<3.14"`，让 `build.py:96-111` 直接读 `pyproject` 而不是各自硬编码。
3. 若要保留 3.14 支持：升级/重装 `pyyaml` wheel，验证 `import yaml` 后再纳入。

---

## F6 39 个顶层 shim 几乎只被测试使用，生产仅剩 2 处；24/39 用 `import *` 且无 `__all__`

**类型：[已证实耦合]**（其中「该不该有 shim 层」是架构选择，不评；「shim 没有边界约束」是实证问题）

### 现象
`module/` 顶层 44 个非 `__init__` 的 `.py` 中，**39 个是 shim**（文件内含 `Compatibility shim` 标记字符串），5 个是真实现。判定「是否 shim」的方式是**注释里有没有那句字符串**。

### 证据：文件:行号
- `unit_tests/architecture_guard_case.py:300-310` —— 用标记字符串分类，并断言真实现集合恰好等于期望值：
  ```python
  def test_top_level_contains_only_facade_and_shims(self):
      shims = {path.name for path in (MODULE_DIR).glob("*.py")
               if "Compatibility shim" in path.read_text(encoding="utf-8")}
      real = {path.name for path in (MODULE_DIR).glob("*.py") if path.name not in shims}
      self.assertEqual(EXPECTED_TOP_LEVEL_REAL, real)
  ```
  `:27-30` `EXPECTED_TOP_LEVEL_REAL = {"__init__.py","bootstrap.py","composition_root.py","constants.py","downloader.py","ports.py"}`
- `unit_tests/architecture_guard_case.py:14-25` `OLD_TOP_LEVEL_NAMES`（39 个名字，与 39 个 shim 一一对应）
- `unit_tests/architecture_guard_case.py:198-219` 只禁止**子包**（`len(parts) >= 3`）import 这些名字：
  ```python
  for alias in aliases:
      if not alias.startswith("module."): continue
      leaf = alias.split(".")[1] if len(alias.split(".")) > 1 else None
      if leaf in OLD_TOP_LEVEL_NAMES:
          violations.append(f"{name}:{node.lineno} imports {alias}")
  ```
  注意：只查 `Import`/`ImportFrom` 的**第一条** alias，且只对子包生效 —— 顶层文件与 `unit_tests/` 不在约束内。
- shim 样例（`module/uploader.py` 全文 9 行）：
  ```python
  # coding=UTF-8
  """Compatibility shim — implementation in module.infra.uploader."""
  import asyncio
  import os
  import random

  from pyrogram import utils

  from module.infra.uploader import *  # noqa: F401,F403
  ```

### 证据：命令原始输出
```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s7_final.py
顶层 shim=39  顶层真实模块=5 -> ['bootstrap', 'composition_root', 'constants', 'downloader', 'ports']
== 生产代码（module/ 子包 + main.py + scripts/）引用顶层 shim 的位置 ==
  main.py:8  module.util
  scripts\diagnose_pikpak_forward.py:98  module.util
  生产引用 shim 总数 = 2 处
== 测试代码引用顶层 shim 的位置（按 shim 汇总）==
  测试引用 shim 总数 = 160 处, 覆盖 29 个 shim
    module.source_folders                 x36
    module.pikpak_archive                 x33
    module.transfer_store                 x27
    module.pikpak_integration             x10
    module.enums                          x6
    ...
== shim 是否真的一行都不能删：只看生产（不含测试）==
  生产代码完全没引用的 shim = 38/39
== 5) 真实模块是否定义 __all__ ==
  module/ 下定义 __all__ 的文件 = 10 / 145
```
```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s6_churn_shims.py
== 4) shim `from X import *` 名称泄漏 ==
  使用 `import *` 的 shim = 24/39
  没有 __all__ 的 shim（star 会把被导入模块的 import 也一起再导出）:
    archive_author_jobs.py ...  （共 22 个）
    uploader.py                    显式别名=['utils'] 额外顶层 import=[module.asyncio, module.os, module.random]
                                      star 目标: module.infra.uploader(__all__=NO)
```

### 量化
| 项 | 数值 |
|---|---|
| 顶层 shim / 真实现 | **39 / 5**（`bootstrap`、`composition_root`、`constants`、`downloader`、`ports`） |
| 生产代码引用 shim 的位置 | **2 处**（`main.py:8`、`scripts/diagnose_pikpak_forward.py:98`，都指向 `module.util`） |
| 生产完全未引用的 shim | **38 / 39** |
| 测试代码引用 shim 的位置 | **160 处**，覆盖 **29** 个 shim |
| shim 用 `import *` 的比例 | **24 / 39** |
| 定义 `__all__` 的 module 文件 | **10 / 145**（⇒ star 会连带再导出库 import） |
| 顶层 shim 总字节 | ~5.6 KB（体积不是问题，**边界**才是） |

### 具体代价
1. **保活关系倒置**：38/39 个 shim 在生产里是死代码，但被测试深度依赖（160 处）。删任何 shim 都要改测试；测试又不默认运行 ⇒ 删 shim 的破坏性在默认流程里不可见。
2. **泄漏的门面**：`module/uploader.py` 让 `module.uploader.asyncio` / `.os` / `.random` / `.utils` 成为合法名字（因为它自己 `import` 了这些，`import *` 目标又无 `__all__`）。任何 `from module.uploader import *` 都会把 `Path`、`re` 等库符号一起灌进来，为「看起来能用但语义不对」的引用创造空间。
3. **判据不是结构而是字符串**：`architecture_guard_case.py:300-310` 靠注释文本 `Compatibility shim` 判定。一个含任意实现的文件只要写上这句话就被算作 shim，从而绕过 `EXPECTED_TOP_LEVEL_REAL` 断言。守门强度取决于注释。
4. **约束有盲区**：`:198-219` 只查子包、只查首个 alias；`from module.util import yaml` 这类多 alias 形式、以及顶层文件/测试对 shim 的使用完全不设限 ⇒ shim 层可以无限增长。

### 最小改进建议
1. 给 39 个 shim 加显式 `__all__`（或改成显式名单 re-export），至少消灭 `module.uploader.asyncio` 这类泄漏。
2. 把 `OLD_TOP_LEVEL_NAMES` + 注释标记换成**显式清单 + 结构断言**：「shim 文件除 docstring 外只允许 `Import`/`ImportFrom`/`__all__` 赋值」。这样 shim 就无法藏实现，也不再依赖注释文本。
3. 生产侧统一到真实现路径（`main.py:8`、`scripts/diagnose_pikpak_forward.py:98` 改 `module.utils.util`），把 shim 保留给外部/历史调用方，并标注弃用计划。

---

## F7 `source_folders.py`：真实高 fan-in，但**不是**垃圾桶

**类型：[风格偏好] —— 结论为「不构成垃圾桶」；下列量化供 Lead 判断，不建议作为问题项**

### 现象与证据
`module/domain/archive_naming/source_folders.py`：37,564 B / 1,102 行 / 41 个顶层定义（**全部是 `def`，无 `class`**），其中 9 个私有辅助（`_` 前缀），32 个公开函数。

```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s5_source_folders.py
== module\domain\archive_naming\source_folders.py ==
  bytes=37564 lines=1102 imports_at_top=6
  顶层定义数 = 41
  （41 个函数清单见 out_s5_source_folders.txt）
== 顶层 import 依赖 ==
    import os
    import re
    from typing import Optional, Union
    from module.core.archive_title_source import ARCHIVE_TITLE_SOURCE_*, normalize_archive_title_source
    from module.utils.path_tool import extract_full_extension, validate_title
    from module.utils.telegram_links import channel_username_from_link, message_id_from_telegram_link
== source_folders fan-in ==
  生产代码 import 点 = 28
  测试代码 import 点 = 36
  去重: 生产文件 23 个, 测试文件 4 个, 合计 27
```

### 量化
| 项 | 数值 |
|---|---|
| 行数 / 字节 | 1,102 / 37,564 |
| 顶层定义 | **41 个函数**（9 私有 + 32 公开），0 个类 |
| 对外部依赖（module 内） | **仅 3 个**：`core.archive_title_source`、`utils.path_tool`、`utils.telegram_links` |
| 生产 fan-in | **23 个文件 / 28 个 import 点**（`downloader.py`、`core/app.py`、`core/filter.py`、`transfer/*`、`adapters/webui/*`、`adapters/bot/*`、`adapters/pikpak/*`、`utils/util.py`） |
| 测试 fan-in | 4 个文件 / 36 个点，其中 `unit_tests/source_folder_archive_case.py`（90,334 B）单文件 26 个点 |
| 函数主题集中度 | 41 个函数全部围绕同一主题：作者/标题抽取与打分、`Source Post Archive Path` 构造与解析 |

### 判定
**不是垃圾桶**，而是一个**深模块**（deep module）：41 个导出、1,102 行、对外仅 3 个依赖，函数命名与职责高度同质——
- 归一化/判定：`normalize_author_label`、`is_denied_post_author`、`normalize_title_candidate`、`is_post_folder_segment`
- 抽取：`extract_post_author_candidates_from_text`、`post_author_from_message(_from_telegram_message/_from_messages)`、`extract_message_body_title`、`title_from_media_file_name`
- 打分/选择：`score_title_line`、`_pick_from_title_buckets`、`pick_best_title_line`、`pick_best_message_title`
- 路径拼装/解析：`split_archive_source_folder`、`archive_source_folder`、`archive_source_folder_for_messages`、`resolve_forward_archive_source_folder`、`join_local_source_folder`、`channel_folder_from_archive_path`
没有出现「与主题无关的杂项函数」这一垃圾桶特征。

按 `architecture_guard_case.py:221-246` 的层规则，`domain` 允许被所有层依赖，因此 23 个生产文件的 fan-in **不构成分层违规**。

### 需要 Lead 注意的真实代价（非垃圾桶，但是变更放大点）
41 个函数共享一份隐式的「标题打分/去噪」契约，任一函数语义变更会同时影响 23 个生产文件；而覆盖它的是**一个 90 KB 的巨型测试文件**（`source_folder_archive_case.py`），测试粒度与模块边界不匹配。

### 最小改进建议（可选）
1. 为该模块补 `__all__`（当前 145 个 module 文件只有 10 个有），把 32 个公开函数变成显式契约。
2. 按依赖切两半：**纯文本侧**（`normalize_*`、`score_title_line`、`pick_best_title_line`、`extract_message_body_title` —— 无 telegram 依赖）与**消息→路径侧**（`archive_source_folder*`、`post_author_from_*`、`split_archive_source_folder`）。前者可无桩独立回归，直接缓解 F8 的桩依赖。

---

## F8 `pyrogram_stub`：60/66 个测试文件用桩替换整个 pyrogram API 面，且桩在模块级是宽松的

**类型：[已证实耦合]**

### 现象与作用（回答「为何门面 import 必须打桩」）
- `unit_tests/pyrogram_stub.py`（228 行 / 8,963 B）在**任何 module 子模块被导入之前**把自己伪造的 `pyrogram` 家族塞进 `sys.modules`。
- 必要性：生产代码在**模块顶层**就 `from pyrogram import ...`（如 `module/uploader.py:7`、`module/adapters/bot/*`），因此 `module.*` 的导入链会强制拉起真实 pyrogram。桩把这条链断开，使单元测试不依赖真实客户端/网络/账号。`pyrogram_stub.py:74-76` 的短路 `if 'pyrogram' in sys.modules: return` 决定了**调用顺序敏感**：必须先装桩，再导入 module（这就是每个 `*_case.py` 顶部都写 `install_pyrogram_stub()` 的原因）。
- 该桩还刻意加固了一处语义（`pyrogram_stub.py:27-41`）：
  ```python
  class DummyFilters:
      """Stands in for pyrogram.filters, keeping command()'s required argument.

      A permissive stub would silently accept ``filters.command()``, which raises
      TypeError against real Pyrogram and aborts Bot.start_bot.
      """
  ```
  即作者已认识到「宽松桩会掩盖真实 API 契约」这一风险，并只堵了 `filters.command()` 一个点。

### 证据：命令原始输出
```
$ .venv313\Scripts\python.exe tmp\coupling-audit\03-build\s8_stub_probe.py
install_pyrogram_stub() 返回 = None
pyrogram.__file__ = <class 'unit_tests.pyrogram_stub.__file__'>
pyrogram.__version__ = test
pyrogram.__path__ = []

--- 桩的宽松面在『模块属性』而不是『实例方法』 ---
  实例方法属性：AttributeError -> 'Client' object has no attribute 'this_method_does_not_exist_in_real_pyrogram' (严格, 好)
  pyrogram.types.SomeTypeThatDoesNotExistInRealPyrogram -> <class 'unit_tests.pyrogram_stub.SomeTypeThatDoesNotExistInRealPyrogram'>
  ^ 真实 pyrogram 会 ImportError/AttributeError；桩动态造类 -> 假阴性
  from pyrogram.enums import SomeEnumThatDoesNotExistEither -> <class 'unit_tests.pyrogram_stub.SomeEnumThatDoesNotExistEither'>
  ^ 同上：模块级符号名写错，测试不会红

--- 桩的内部不一致：sys.modules 里有、父模块属性上没有 ---
  pyrogram.enums.ParseMode -> AttributeError: type object 'enums' has no attribute 'ParseMode'
  但 from pyrogram.enums import ParseMode 可用（见上）
    pyrogram.types     属性=yes sys.modules=yes
    pyrogram.enums     属性=yes sys.modules=yes     <-- 属性存在，但对象是动态造的 class，不是准备好的 DummyModule
    pyrogram.errors    属性=yes sys.modules=yes
    ...

--- 桩显式建模的模块 API 名称 ---
  显式建模名称数 = 110
  pyrogram_stub.py 行数 = 228 / 8963 B
  DummyModule 实例 = 30
  type(...) 动态类构造 = 27
```
```
$ # 计数
unit_tests/*_case.py            = 66
含 install_pyrogram_stub 的文件 = 60
install_pyrogram_stub 出现次数  = 119
含 unittest.main() 的文件       = 63
```

### 量化
| 项 | 数值 |
|---|---|
| 依赖桩的测试文件 | **60 / 66 = 90.9%** |
| `install_pyrogram_stub` 调用点 | 119 处 |
| 桩显式建模的 API 名称 | 110 个（30 个 `DummyModule`，27 个 `type()` 动态类） |
| 桩替换的第三方包 | `pyrogram`(+11 子模块)、`pymediainfo`、`qrcode`（`pyrogram_stub.py:213-228`） |
| 宽松面 | `DummyModule.__getattr__` 对**任意**模块级名字动态造类（`:44-48`） |

### 具体代价
1. **假阴性**：生产代码写错**模块级**符号（`from pyrogram.types import Foo` / `pyrogram.enums.Bar`）时，桩静默造类，测试不会红；而真实环境会 `ImportError`/`AttributeError`。作者已在 `DummyFilters` 上手工堵了一个同类漏洞，说明这是**已发生的**故障模式而非理论风险。
2. **桩内部不一致**：`pyrogram_stub.py:105`、`:171-172` 设置了 `pyrogram.types` / `pyrogram.raw` / `pyrogram.utils` 属性，但 `:189-211` 只写 `sys.modules['pyrogram.enums']` 等，**没有**同步设置 `pyrogram.enums` / `pyrogram.errors` / `pyrogram.file_id` / `pyrogram.handlers` / `pyrogram.session` / `pyrogram.crypto` / `pyrogram.qrlogin`。结果同一个符号两条路径行为不同：`from pyrogram.enums import ParseMode` 可用，`pyrogram.enums.ParseMode` 抛 `AttributeError`。测试能否通过取决于写法，属于隐性脆弱。
3. **版本漂移盲区**：`pyrogram.__version__ = 'test'`，桩不校验真实 kurigram（`kurigram==2.2.19`）版本；升级 `pyrogram` 后 60 个文件的测试结论不变。

### 最小改进建议
1. 一行修复内部不一致：在 `pyrogram_stub.py:189` 附近补 `pyrogram.enums = enums`，并对 `errors` / `file_id` / `handlers` / `session` / `crypto` / `qrlogin` 同样处理。
2. 让 `DummyModule.__getattr__` 对未知名字 `raise AttributeError`（配白名单），把「模块级宽松」收窄成和 `Client` 实例一样的严格 —— 这样错名的符号在测试里就会红。
3. 增加一个「桩 vs 真实 pyrogram 的 API 面差异」测试：CI 环境装真实 `kurigram`，对生产代码里出现的 `pyrogram.*` 引用做 AST 收集并逐一解析，缺哪个补哪个。

---

## 附：所有执行过的命令

### 只读探查
```
git -C E:\codebase\tgbot rev-parse HEAD
git -C E:\codebase\tgbot status --porcelain
Get-ChildItem E:\codebase\tgbot -Force
Get-ChildItem module\adapters\webui -Recurse -File
Get-ChildItem unit_tests -File
Get-ChildItem module -File
Get-ChildItem .github -Recurse -File
Get-ChildItem module\adapters\webui\templates,module\adapters\webui\static -Recurse -File
Get-Content .venv\pyvenv.cfg
Get-Content .venv313\pyvenv.cfg
Get-Content .dockerignore
Get-Content module\adapters\webui\static\tailwind.css -TotalCount 12
Get-ChildItem module\adapters\webui\dist -Force
node_modules\.bin\tailwindcss.cmd --help
```

### Git churn / 历史
```
git ls-files --error-unmatch module/adapters/webui/assets.py
git log --oneline -12 -- module/adapters/webui/assets.py
git log --oneline -200 -- module/adapters/webui/assets.py | Measure-Object   # -> 141
git log -200 --numstat --pretty=format:"C" -- module/adapters/webui/assets.py
git log -200 --numstat --pretty=format:"C"
git log -12 --numstat --pretty=format:"C|%h|%s" -- module/adapters/webui/assets.py
```

### 解释器 / 环境（F5）
```
.\.venv\Scripts\python.exe -V
.\.venv\Scripts\python.exe -c "import yaml; print('yaml ok', yaml.__version__)"        # EXITCODE=-1073741819
.\.venv\Scripts\python.exe -c "import sys;print(sys.version)"
.\.venv313\Scripts\python.exe -V
.\.venv313\Scripts\python.exe -c "import yaml; print('yaml ok', yaml.__version__)"     # yaml ok 6.0.3
.\.venv313\Scripts\python.exe -c "import module; print('module ok', module.__version__)" # module ok 0.2.248
.\.venv313\Scripts\python.exe -c "import module.adapters.bot.bot as m; print('ok')"
```

### 测试基建实测（F4）
```
.\.venv\Scripts\python.exe -m pytest --version
.\.venv\Scripts\python.exe -m pytest unit_tests -q                                      # no tests ran, exit 5
.\.venv\Scripts\python.exe -m pytest unit_tests/web_ui_assets_case.py -q                # access violation, exit -1073741819
.\.venv313\Scripts\python.exe -m pytest unit_tests -q                                   # no tests ran in 0.03s, exit 5
.\.venv313\Scripts\python.exe -m pytest unit_tests --collect-only -q                    # no tests collected, exit 5
.\.venv313\Scripts\python.exe -m pytest unit_tests/web_ui_assets_case.py -q             # 43 passed in 0.29s, exit 0
.\.venv313\Scripts\python.exe -m pytest <全部 66 个 unit_tests/*_case.py> -q            # 702 passed, 27 subtests, 78.54s, exit 0
(Get-ChildItem unit_tests -File -Filter "*_case.py").Count                              # 66
Select-String -Path unit_tests\*.py -Pattern "install_pyrogram_stub"                    # 119 处 / 60 文件
Select-String -Path unit_tests\*.py -Pattern "unittest\.main\(\)"                       # 63 文件
Select-String -Path module\*.py -Pattern "Compatibility shim"                           # 39 文件
```

### 自建只读分析脚本（均在 `tmp\coupling-audit\03-build\`）
```
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s1_assets_stats.py          # assets.py 常量/体积/base64/重复块
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s2_drift_check.py           # 内存重建 vs assets.py 逐字节比对（不写盘）
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s3_mutation_cost.py         # 改 1 行的重建代价量化
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s4_shims.py                 # shim 识别 + 引用者统计
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s5_source_folders.py        # source_folders fan-in + 函数清单
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s6_churn_shims.py           # git churn + star 泄漏 + 测试漂移检测能力
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s7_final.py                 # 生产 vs 测试的 shim 依赖、脆弱断言
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\s8_stub_probe.py            # pyrogram_stub 宽松度实测
.venv313\Scripts\python.exe tmp\coupling-audit\03-build\check_frontend_drift.py     # 漂移检测器（改进建议的可运行实现）
```

### 产出文件
```
tmp\coupling-audit\03-build\evidence.md                      <- 本文件
tmp\coupling-audit\03-build\check_frontend_drift.py          <- F3 的可运行改进实现
tmp\coupling-audit\03-build\s1_assets_stats.py   out_s1_assets_stats.txt
tmp\coupling-audit\03-build\s2_drift_check.py    out_s2_drift.txt
tmp\coupling-audit\03-build\s3_mutation_cost.py  out_s3_mutation.txt
tmp\coupling-audit\03-build\s4_shims.py          out_s4_shims.txt
tmp\coupling-audit\03-build\s5_source_folders.py out_s5_source_folders.txt
tmp\coupling-audit\03-build\s6_churn_shims.py    out_s6_churn_shims.txt
tmp\coupling-audit\03-build\s7_final.py          out_s7_final.txt
tmp\coupling-audit\03-build\s8_stub_probe.py     out_s8_stub_probe.txt
tmp\coupling-audit\03-build\out_cmd1_pytest_dir.txt          # .venv: no tests ran, exit 5
tmp\coupling-audit\03-build\out_cmd3_pytest_single.txt       # .venv: access violation 完整栈
tmp\coupling-audit\03-build\out_cmd4_pytest313_dir.txt       # .venv313: no tests ran, exit 5
tmp\coupling-audit\03-build\out_cmd5_pytest313_single.txt    # .venv313: 43 passed, exit 0
tmp\coupling-audit\03-build\out_cmd6_pytest313_allfiles.txt  # .venv313: 702 passed, exit 0
tmp\coupling-audit\03-build\out_gitnumstat_assets.txt
tmp\coupling-audit\03-build\out_stub_probe.txt
```

### 明确未做的事（约束遵守）
- 未修改 `module/`、`unit_tests/`、`templates/`、`static/`、`dist/` 任何文件；未 `git commit`。
- 未运行 `build_frontend.py` 的 `main()`（那会覆写 `assets.py`）；只导入并调用其**纯函数**做内存比对。
- 未运行 tailwind CLI 的编译模式（会写 `dist/tailwind.min.css`）；只跑了 `--help`。
- 未运行 `pytest` 之外的任何会写盘的工具；未安装依赖。
