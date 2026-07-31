---
name: web-tutor-book
description: 将文章、Markdown、PDF、DOCX、教程稿、聊天案例或知识库材料编辑成内容保真的网页教程书、翻页手册或 EPUB 风格电子书，并可从同一组件树导出视觉保真的可搜索 PDF；也可审查已有教程或 PDF 是否达到内部使用、公开 QuickStart、教程书或正式出版标准。使用语义分页、内容台账、逐页视觉检查和 P0/P1/P2 质量门禁防止删减与低质量交付。Use when users ask for web books, tutorial books, interactive manuals, paginated guides, EPUB-like readers, high-fidelity PDF exports, O'Reilly-style technical books, or quality audits of existing tutorials and PDFs.
---

# Web Tutor Book

把原始材料编辑成可翻页、可连续阅读、可审计的教程型电子书。借鉴网页演示的语义分幕与首章锚点，但以**内容保真**而不是口播节奏为最高约束。

## 不可违反的内容契约

1. 完整保留用户原始材料为 `source.md` 或等价原始文件，不覆盖、不改写。
2. 默认使用“完整保留模式”：保留所有事实、步骤、限定条件、例外、示例、代码、表格、引用和风险提示。
3. 不设置每页字数上限，也不为追求画面简洁而摘要原文。页面放不下时，依次选择：增加语义页、创建续页、使用正文页内滚动、转为可重排连续阅读。
4. 将“语义页”理解为编辑排版单元，不是幻灯片。一个主题可以占若干页，一段长文也可以自然延续。
5. 只有用户明确批准后才能省略内容，并在台账中记录批准说明。不得用“重复”“不重要”“太长”自行删减。
6. 改写只允许提升可读性，不得改变事实、因果、语气强度或适用范围。无法确定时保留原句。
7. 将新增解释、编辑提示和原文明确区分；不得把 Agent 补写的内容伪装成来源事实。

每次开始内容规划前，完整阅读 [`references/CONTENT-FIDELITY.md`](references/CONTENT-FIDELITY.md)。每次设计页纲时阅读 [`references/BOOK-PLAN-FORMAT.md`](references/BOOK-PLAN-FORMAT.md)。采用经典技术出版物、动物版画或内容隐喻封面时，完整阅读 [`references/COVER-SYSTEM.md`](references/COVER-SYSTEM.md)。每次实现阅读器或做视觉复验时阅读 [`references/READER-CRAFT.md`](references/READER-CRAFT.md)。用户要求 PDF 或打印版时，必须阅读 [`references/PDF-EXPORT.md`](references/PDF-EXPORT.md)。进入最终验收或打包前，完整阅读 [`references/PUBLICATION-QA.md`](references/PUBLICATION-QA.md)。

## 现有文档质量审计模式

当用户要求判断已有教程、网页书或 PDF 是否合格时，不进入制作工作流，改用
[`references/DOCUMENT-QUALITY-AUDIT.md`](references/DOCUMENT-QUALITY-AUDIT.md)：

1. 先声明目标用途和读者；未说明时按 `public-quickstart` 检查。
2. 对 PDF 执行元数据、文本层、图片、链接、字体、书签与页面尺寸扫描；可使用
   [`scripts/audit_pdf.py`](scripts/audit_pdf.py) 产生候选问题。
3. 渲染全部页面并查看 contact sheet，再放大检查代表页。
4. 检查任务是否从前置条件走到可验证结果，并覆盖费用、权限、上传、发布、失败处理和安全边界。
5. 在线核验时间敏感的链接、版本、价格、收益和产品能力。
6. 先判 P0，再按 100 分模型评分，输出“合格 / 有条件合格 / 不合格”。
7. 缺少源稿或台账时，明确写“内容保真无法验证”，不得声称 100% 内容覆盖。
8. 报告必须提供页码证据、修复方式和可复验的通过条件。

## 工作流

### Phase 1：摄取材料与建立内容台账

1. 读取用户材料的全部内容；遇到 PDF、DOCX、表格或网页时，使用适合该格式的读取能力先完整提取。
2. 将材料原样保存为项目内 `source.md`；非 Markdown 原件也要保留，并另外生成可审计的文本版本。
3. 初始化内容台账：

```bash
python3 <skill-dir>/scripts/source_coverage.py init source.md content-ledger.json
```

4. 检查提取结果是否丢失表格、代码、脚注、图片说明或列表层级。必要时修正 `source.md` 后重新初始化台账。

### Phase 2：编辑架构与语义分页

1. 按 [`references/BOOK-PLAN-FORMAT.md`](references/BOOK-PLAN-FORMAT.md) 创建 `book-plan.md`。
2. 为每个源内容块分配一个或多个 `page_id`，并在 `content-ledger.json` 填写保留方式：
   - `verbatim`：原文呈现；
   - `faithful-edit`：等义编辑，细节不减少；
   - `visual-plus-text`：图解辅助，但完整文字仍在页面或相邻续页；
   - `appendix`：正文引用，完整内容进入附录；
   - `user-approved-omit`：仅限用户明确批准。
3. 页面容量不足时增加 `-cont-1`、`-cont-2` 等续页，禁止先删内容再“适配”。
4. 同时规划两种基础阅读路径：
   - `reader`：语义翻页；
   - `article`：连续、可搜索、可复制的完整正文。
   用户需要 PDF 时再规划 `print`：复用 `reader` 的封面与视觉页，同时让长正文可分页流动。
5. 为每张流程图、插图和真实截图记录关联内容块、教学目的、素材来源和承载页。图会挤压正文时，优先建立独立视觉页，并把完整文字放在紧邻正文页；不得把“图 + 被裁掉的文字”视为完成。
6. 把封面拆成稳定编辑系统与可变内容主视觉：使用隔离的 CoverBrief 表达当前书的对象、动作、结构变化和安全区，再与纯视觉风格预设动态编译最小图像 Prompt。不得把整本书、历史案例或未选方案传给图像模型。封面图只能作为无文字底图，书名、副标题、作者、版本等全部使用 HTML/CSS 文字层。
7. 建立术语表，固定产品名、人名、大小写和 Agent 称谓；批量替换后必须复查代码、URL、文件名和引用，避免误改。
8. 规划完成后运行覆盖审计。未达到 100% 映射不得开始网页开发。

```bash
python3 <skill-dir>/scripts/source_coverage.py audit source.md content-ledger.json \
  --report review/coverage-plan.json
```

### Checkpoint：一次确认五件事

在开发前向用户展示并等待确认：

1. 章节与语义页数量；
2. 内容保真模式：默认完整保留，是否存在用户批准的省略；
3. 视觉主题、两个内容相关封面方向与真实素材来源；
4. 开发方式：首章验收后逐章、顺序或并行；
5. 交付形态：网页、视觉保真 PDF、A4 内容版、EPUB，是否需要多种版本。

没有明确要求时，选择“完整保留 + 首章后逐章确认”。

### Phase 3：首章锚点

1. 先实现首章完整样稿，不做空骨架。
2. 至少包含三类不同语义页，例如章节扉页、解释正文、流程图、代码页或检查表。
3. 保留章节对应的全部源内容；视觉图解只能辅助，不能替代文字。
4. 当“流程图 + 完整说明”不能舒适共页时，拆成相邻两页：视觉页只解释结构，正文页完整承载步骤。不要缩小整页或正文来腾空间。
5. 实现目录、前后翻页、键盘、触摸、URL deep link、断点续读和连续阅读入口。
6. 使用本地 HTTP 预览服务验收；不得只依赖 `file://` 打开结果，因为模块、资源和路由可能表现不同。
7. 在桌面与至少 390×844、360×800 两个手机视口复验。
8. 运行覆盖审计、类型检查、构建和控制台检查；修复后再让用户验收首章。

### Phase 4：完成全书

按用户选择的方式完成其余章节。每章都要：

1. 回读该章源内容和台账；
2. 实现书页；
3. 检查页面容量；
4. 更新台账；
5. 审计该章是否保留全部内容。

并行开发时，每个 Agent 只修改自己的章节文件，不得修改全局注册表；给它当前章节的源内容、页纲、台账块和首章代码风格。

### Phase 5：最终质量与导出

1. 运行覆盖审计，要求 `unmapped_blocks = 0`、`invalid_blocks = 0`、`source_drift = false`。
2. 逐页检查桌面和手机：除明确标注为可滚动的正文/代码页外，禁止裁切。
3. 检查目录、前进/后退、URL hash、刷新恢复、键盘和触摸。
4. 检查连续阅读模式包含全部内容，搜索和复制可用。
5. 做出版表面清理：渲染 Markdown 语义而不是泄漏 `**`、代码围栏或链接语法；删除“完整原文”“下一页阅读原文”“页面截图/流程图/信息图”等编辑态或重复类型标签；复制按钮只保留在确有复用价值的代码或 Prompt 上，不默认出现在每个对话卡片中。
6. 检查所有真实截图的相关性、清晰度、裁切、替代文本和来源说明；没有真实证据时宁可使用明确标注的流程图，也不要伪造产品 UI 或终端截图。
7. 运行类型检查和正式构建；报告构建体积与资源优化结果。
8. 由本地 Agent 根据当前环境选择可用浏览器能力，或使用可选的 [`scripts/audit_reader.mjs`](scripts/audit_reader.mjs) 适配器，逐页扫描打印视图和三种阅读器视口；不强制安装 Playwright，要求无空白页、破图、意外越界和控制台错误。
9. 用户要求 PDF 时，按 [`references/PDF-EXPORT.md`](references/PDF-EXPORT.md) 从同一组件树创建专用打印入口。封面、Chapter Open、流程图和截图页保持固定出版物构图；长正文、代码和表格改为可分页流式布局。不得用另一套 ReportLab 版式冒充网页版高保真导出，也不得用整页截图牺牲文字搜索与链接。
10. PDF 导出后必须逐页渲染并生成 contact sheet，至少放大检查封面、章节扉页、流程图、最长正文、代码/表格、真实截图和末页。清除空白页前同时检查文本、页面墨迹与计划页型，禁止仅凭“提取不到文字”删除图片页或矢量图页。
11. 用户要求 EPUB 时，从相同章节源导出 EPUB 3；不要把固定尺寸网页直接塞入 EPUB。EPUB 正文应可重排，代码、表格和图片需有降级样式。
12. 把任何内容、样式、标签、截图或页序修改都视为会使旧构建、旧 PDF、旧 contact sheet、旧审计报告和校验哈希失效。最后一次修改后重新执行完整构建与发布验收，再打包交付。

## 项目结构

```text
my-tutor-book/
├── source.md
├── content-ledger.json
├── book-plan.md
├── reader/                 # 网页阅读器源码
├── dist/
│   ├── book.html           # 可选单文件离线版
│   └── book.epub           # 用户要求时生成
├── output/
│   └── pdf/
│       ├── book-visual.pdf # 复用网页视觉的分享版
│       └── book-a4.pdf     # 可选的传统打印版
├── tmp/
│   └── pdfs/               # PDF 逐页渲染与 contact sheet
└── review/
    ├── coverage-plan.json
    ├── coverage-final.json
    ├── publication-dom-audit.json
    ├── visual-review.md
    └── pdf-visual-review.md
```

## 最终交付必须说明

- 源材料块数、100% 映射是否通过、是否有用户批准的省略；
- 总章节数与总语义页数；
- 网页翻页版、连续阅读版、PDF 和 EPUB 的实际输出路径；
- 已测试的视口、交互、构建结果和仍存在的限制。
- 真实截图的来源与用途、PDF 页数/尺寸/文件大小、contact sheet 与最终校验哈希。

不得只说“已完成”，也不得把视觉完成误当作内容完成。
