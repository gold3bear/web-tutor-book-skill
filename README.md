# Web Tutor Book Skill

把 Markdown、文章、PDF、DOCX、教程稿、聊天案例或知识库材料，制作成内容保真的网页教程书、翻页手册和视觉一致的可搜索 PDF。

`web-tutor-book` 面向支持 `SKILL.md` 工作流的本地 Agent。它不绑定特定平台，也不强制依赖 Playwright；Agent 可以根据自身环境选择浏览器、截图、PDF 和图像生成能力。

## 核心能力

- 以内容台账确保原文事实、步骤、代码、表格与限定条件不被排版过程擅自删减。
- 按章节和语义单元编辑分页，不把教程压缩成只有标题的幻灯片。
- 支持目录、键盘与触摸翻页、URL 深链、断点续读和连续阅读。
- 支持内容相关、无文字底图的技术出版物封面；书名和副标题使用 HTML/CSS 排版。
- 为流程图、真实截图、代码、表格和长正文选择合适页型。
- 从同一内容与组件体系导出视觉保真的可搜索 PDF。
- 支持可选 EPUB 3 输出规划。
- 提供内容覆盖审计和可选的浏览器自动化审计脚本。

## 让 Agent 安装

把下面的指令直接交给支持 Skill 的本地 Agent：

```text
请安装 GitHub 仓库中的 web-tutor-book Skill：
https://github.com/gold3bear/web-tutor-book-skill

请先阅读仓库根目录的 SKILL.md，检查所有脚本和引用文件，再按照你当前 Agent
平台支持的 Skill 安装方式，把整个仓库安装为名为 web-tutor-book 的本地 Skill。
不要只复制 SKILL.md；需要同时保留 agents、references 和 scripts 目录。
安装完成后，请验证 Skill 可被识别，并告诉我安装路径和验证结果。
```

不同 Agent 的 Skill 目录和安装入口可能不同，应以该平台的官方方式为准。支持从 GitHub 安装的 Agent 可以直接使用本仓库地址；手动安装时必须保留完整目录结构。

## 使用示例

```text
请使用已安装的 web-tutor-book Skill，把我提供的教程 Markdown 制作成一本可翻页的
网页教程书。使用完整保留模式，先建立内容台账和页纲，在开发前向我确认章节、
语义页数量、封面方向和最终交付格式。完成后导出视觉一致、文字可搜索的 PDF。
```

在 Codex 中也可以直接写：

```text
$web-tutor-book 请把这份教程制作成网页电子书和视觉保真的 PDF。
```

## 仓库结构

```text
web-tutor-book-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── BOOK-PLAN-FORMAT.md
│   ├── CONTENT-FIDELITY.md
│   ├── COVER-SYSTEM.md
│   ├── PDF-EXPORT.md
│   ├── PUBLICATION-QA.md
│   └── READER-CRAFT.md
└── scripts/
    ├── audit_reader.mjs
    └── source_coverage.py
```

## 验证

初始化或审计内容台账：

```bash
python3 scripts/source_coverage.py --help
node --check scripts/audit_reader.mjs
```

`audit_reader.mjs` 是可选的 Playwright 适配器，并不是 Skill 的必装依赖。没有 Playwright 时，本地 Agent 应使用当前环境已有的浏览器能力完成等价验收。

## 许可

[MIT License](LICENSE)

