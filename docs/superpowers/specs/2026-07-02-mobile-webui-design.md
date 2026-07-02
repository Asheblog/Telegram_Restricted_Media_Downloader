# 移动版 WebUI 设计方案

> 日期：2026-07-02
> 状态：Approved
> 关联：`module/web_ui.py`, `module/web_ui_assets.py`

---

## 一、目标

为 TRMD 转存控制台设计移动版 WebUI，通过服务端 UA 检测自动切换到移动端优化页面。

## 二、检测机制

- **方式**：服务端 `User-Agent` 检测
- **位置**：`web_ui.py` 的 `Handler._send_html()` 方法
- **匹配规则**：正则 `Mobile|Android|iPhone|iPod` 命中则返回移动版
- **逻辑**：
  ```python
  def _send_html(self):
      ua = self.headers.get('user-agent', '')
      is_mobile = bool(re.search(r'Mobile|Android|iPhone|iPod', ua))
      html = WEB_UI_MOBILE_HTML if is_mobile else WEB_UI_HTML
      # ...
  ```

## 三、页面策略：独立移动版

在 `web_ui_assets.py` 中新增三个独立变量：

| 变量 | 对应桌面版 | 说明 |
|------|-----------|------|
| `WEB_UI_MOBILE_CSS` | `WEB_UI_CSS` | 移动端专用样式 |
| `WEB_UI_MOBILE_BODY` | `WEB_UI_BODY` | 移动端 HTML 结构 |
| `WEB_UI_MOBILE_SCRIPT` | `WEB_UI_SCRIPT` | 移动端 JS（复用核心逻辑） |

组装为 `WEB_UI_MOBILE_HTML`，结构与 `WEB_UI_HTML` 一致。

## 四、导航模式

### 底部固定 Tab Bar（4 项）

| Tab | 图标含义 | 视图 ID |
|-----|---------|---------|
| 转存任务 | 列表 | `view-transfers` |
| 实时监听 | 眼睛 | `view-watches` |
| 设置 | 齿轮 | `view-settings` |
| 更多 | 三点 | 打开 Drawer |

### "更多"抽屉

从底部或右侧滑出，列出次要视图：
- 频道下载
- 本地上传
- 统计
- 下载记录

## 五、页面布局

统一单列列表驱动布局：

| 视图 | 移动端布局 |
|------|-----------|
| 转存任务 | 折叠面板（新建转存，默认收起） + 任务卡片列表 |
| 实时监听 | 折叠面板（新建监听，默认收起） + 监听卡片列表 |
| 频道下载 | 折叠面板 + 下载记录列表 |
| 本地上传 | 折叠面板 + 上传记录列表 |
| 统计 | 全宽表格，`overflow-x: auto` |
| 设置 | 单列表单，分组可折叠（section 折叠） |
| 下载记录 | 卡片列表 |

### Top Bar

精简为紧凑的 brand bar：TRMD 图标 + 标题 + 刷新按钮 + 语言切换。

## 六、表格 → 卡片列表

多列数据表在移动端改为卡片列表，每行数据变成一张卡片：

```
┌──────────────────────────────────┐
│ 状态标签        ID: #123        │
│ 来源: @channel_xxx               │
│ 进度: ████████░░ 78%             │
│ [暂停] [重试] [删除]             │
└──────────────────────────────────┘
```

统计表保持表格结构，加横向滚动。

## 七、表单适配

- 输入控件 `width: 100%`
- label 在上，input 在下（单列）
- 触控目标 ≥ 44×44px
- `<select>` 设 `font-size: 16px` 防 iOS 缩放
- 提交按钮全宽
- 新建操作通过 **FAB（右下角浮动按钮）** 触发 → 弹出 Bottom Sheet 填写表单

## 八、JS 复用

### 复用部分
- `switchView()` 视图切换核心逻辑
- API 调用函数（fetch tasks、settings、watches 等）
- i18n 函数
- `startPolling()` / `stopPolling()` 轮询逻辑
- `escapeHtml()`、日期格式化等工具函数

### 重写/新增部分
- 底部 Tab 切换逻辑（替代侧边栏按钮绑定）
- 抽屉（Drawer）展开/收起
- FAB 按钮交互
- 折叠面板展开/收起
- Bottom Sheet 弹窗
- Toast 通知组件

## 九、移动端专项优化

- **safe-area**：底部 tab 栏 `padding-bottom: env(safe-area-inset-bottom, 0)`
- **触摸反馈**：`:active` 态替代 `:hover`
- **下拉刷新**：`pull-to-refresh` 手势触发数据刷新
- **Toast 通知**：操作反馈用底部 toast
- **Viewport**：保留 `width=device-width, initial-scale=1`，增加 `maximum-scale=1, user-scalable=no`

## 十、实施优先级

### Phase 1（核心 3 视图）
1. 转存任务 — 卡片列表 + 折叠新建面板
2. 实时监听 — 卡片列表 + 折叠新建面板
3. 设置 — 可折叠分组表单

### Phase 2（补充 4 视图）
4. 频道下载
5. 本地上传
6. 统计
7. 下载记录

Phase 1 覆盖 90% 移动端使用场景。Phase 2 视图在"更多"抽屉中先显示为简易列表。

## 十一、文件变更清单

| 文件 | 变更 |
|------|------|
| `module/web_ui.py` | `_send_html()` 增加 UA 检测逻辑 |
| `module/web_ui_assets.py` | 新增 `WEB_UI_MOBILE_CSS`、`WEB_UI_MOBILE_BODY`、`WEB_UI_MOBILE_SCRIPT`、`WEB_UI_MOBILE_HTML` |
| `module/web_ui_assets.py` | 现有 JS 中提取可复用函数为公共模块 |
