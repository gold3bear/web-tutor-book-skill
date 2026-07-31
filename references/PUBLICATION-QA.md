# 网页教程书出版验收

## 目录

1. 验收原则
2. 浏览器逐页审计
3. 视觉抽查
4. 内容与出版表面
5. PDF 同步
6. 打包门禁

## 1. 验收原则

验收对象是最后一次修改后的产物，不是某个较早的成功构建。内容、样式、截图、标签、页序或文件名发生变化后，旧 HTML、PDF、contact sheet、审计报告和哈希全部失效。

同时检查四层：

- 源内容与台账；
- 浏览器 DOM 和交互；
- 读者实际看到的视觉表面；
- PDF 文本层与逐页渲染。

自动检查负责找候选问题，最终视觉判断仍需查看截图和 contact sheet。

用户明确启用批量书页截图审计时，另行读取
[`LOOMLOOM-VISUAL-REVIEW.md`](LOOMLOOM-VISUAL-REVIEW.md)，并把
`loomloom-publication-visual-audit` 生成的、已经完成本地原图复核的报告作为第五层
辅助证据。云端原始候选不是出版结论，外部报告的 `publishReady` 也不替代本文件的
打包门禁。

## 2. 浏览器逐页审计

先启动 HTTP 预览服务。由本地 Agent 根据当前环境选择可用的浏览器能力，完成
打印视图、桌面阅读器和移动阅读器的逐页检查。浏览器实现不绑定 Playwright；
可以使用当前 Agent 环境提供的浏览器工具、Chrome 控制能力或其他能够取得 DOM、控制台与截图的
等价方案。

技能附带的 Playwright 脚本只是可选自动化适配器。在项目已经具备 Playwright，
或 `BROWSER_NODE_MODULES` 指向含 Playwright 的 `node_modules` 时，可以运行：

```bash
node <skill-dir>/scripts/audit_reader.mjs \
  http://127.0.0.1:5173/ review/publication-dom-audit.json
```

该可选脚本默认约定：

- 打印入口：`?mode=print`；
- 打印页：`.ebr-print-page`，页 ID 来自 `data-page-id`；
- 当前阅读页：`.ebr-stage > .ebr-page`；
- 可滚动正文：`.ebr-source__body`。

可用环境变量覆盖：`BROWSER_NODE_MODULES`（兼容旧名 `CODEX_NODE_MODULES`）、`CHROME_PATH`、`PRINT_PAGE_SELECTOR`、`READER_PAGE_SELECTOR`、`SOURCE_BODY_SELECTOR`、`FORBIDDEN_VISIBLE_LABELS`。项目使用不同 DOM 契约时，显式设置选择器，不要为了通过检查伪造类名。找不到 Playwright 时，不应阻塞 Skill 使用；应回退到本地 Agent 可用的浏览器能力。

脚本默认使用严格模式，发现失败项时返回非零状态，并在 JSON 中写入
`summary.passed`、`summary.failureCount` 与失败明细。`AUDIT_STRICT=0`
只用于诊断，不得作为发布通过依据。装饰图片允许使用 `alt=""`；只有完全缺少
`alt` 属性才属于可访问性失败。

通过条件：

- 页 ID 唯一且非空；
- 没有空白计划外页面；
- 图片全部加载且有替代文本；
- 固定页没有意外越界；
- 允许滚动的区域可以到达全部内容；
- 桌面 1440×1000、手机 390×844、手机 360×800 均无控制台错误；
- 读者页数与打印视图计划页数一致，除非文档明确说明流式打印续页差异。

## 3. 视觉抽查

先查看整书 contact sheet，再放大以下页面：

1. 封面；
2. 第一张 Chapter Open；
3. 至少两张复杂流程图；
4. 最长正文和最长 Prompt；
5. 代码与表格；
6. 每一种真实截图；
7. 最后一页。

重点识别：

- 流程图占高后正文被挤出；
- 整页缩小后底部出现大块留白；
- 截图清晰但与内容无关；
- 图题、页脚或 CTA 被裁切；
- 手机只有部分正文可见却没有滚动提示；
- Chapter Open 空旷或装饰图没有信息增量。

## 4. 内容与出版表面

运行内容覆盖审计，并要求 100% 映射、无源漂移、无非法块。然后在最终 DOM 中检查：

- 裸露的 `**`、代码围栏、Markdown 链接语法；
- “完整原文”“下一页阅读原文”等编辑态提示；
- “页面截图 / 流程图 / 信息图”等重复类型徽标；
- 无效复制按钮、空链接、内部调试名称；
- 术语大小写和 Agent 称谓；
- 真实截图的替代文本、来源与场景边界。

字符串搜索命中替代文本或正文合法用词时，不应机械删除；应检查它是否成为无信息增量的可见 UI。

## 5. PDF 同步

PDF 导出后检查：

```bash
pdfinfo output/pdf/book.pdf
pdftoppm -png output/pdf/book.pdf tmp/pdfs/book/page
```

再用 `pypdf` 或 `pdfplumber` 检查：总页数、空文本页、元数据标题、链接数量、中文提取、裸露 Markdown 和已删除 UI 文案。图片页或矢量页可能没有可提取文字，删除空白页前必须查看渲染墨迹。

网页与 PDF 至少并排对照封面、一个流程图和一个真实截图页。PDF 只通过文本检查而没有视觉复验，不能交付。

## 6. 打包门禁

打包前依次确认：

1. 最后一次源码修改之后重新构建；
2. 内容覆盖与浏览器逐页审计通过；无论使用哪种浏览器能力，都保留截图、DOM/控制台结果或等价审计证据；
3. 如启用外部批量视觉审计，已完成页面身份和原图证据复核；只把 `accepted` 和
   `reframed` 问题进入修复队列，并保留误报轨迹；
4. 外部审计后如修改页面，已使旧截图、哈希和报告失效；重新运行本地门禁，并记录
   最终版本是否再次云端复跑；
5. 最终 PDF 重新导出并逐页渲染；
6. 审计报告中的页数、图片数、图解数、文件大小与实际一致；
7. SHA-256 由最终 HTML/PDF 重新生成；
8. ZIP 不包含缓存、临时截图、`node_modules`、系统元数据或旧版产物；
9. 解压 ZIP 后再次运行技能校验，并抽测核心脚本。

任何一项失败，都应修复后从受影响的上游步骤重新执行。
