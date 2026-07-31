# 可选批量书页截图审计

## 目录

1. 定位与职责边界
2. 依赖发现与安装
3. 启用门槛
4. 交接包
5. 两次用户确认
6. 外部 Skill 执行
7. 结果回收与修复
8. 失效、复跑与降级
9. 最终记录

## 1. 定位与职责边界

使用独立的 `loomloom-publication-visual-audit` Skill 执行批量页面截图审计：

```text
web-tutor-book
  ├─ 内容台账与语义分页
  ├─ 页面渲染与本地 DOM/PDF 门禁
  └─ 脱敏截图 + 页面清单
                  │
                  ▼
loomloom-publication-visual-audit
  ├─ LoomLoom Market 报价与付费确认
  ├─ 云端并行发现视觉问题
  ├─ 返回结构、页面身份与证据硬校验
  ├─ 本地 Agent 原图二次确认
  └─ 可追溯视觉审计报告
                  │
                  ▼
web-tutor-book
  ├─ 修复已确认问题
  ├─ 重跑本地门禁
  └─ 作出最终出版结论
```

云端负责高召回发现，本地负责事实裁决。外部 Skill 的视觉审计报告是出版验收的
一项证据，不是最终出版结论。

默认关闭该分支。不要把它变成构建、导出、PDF 或 EPUB 的必需依赖。

## 2. 依赖发现与安装

优先查找已安装的 Skill：

```text
skill name: loomloom-publication-visual-audit
folder: loomloom-publication-visual-audit
```

项目公共来源：

```text
https://github.com/gold3bear/loomloom-publication-visual-audit-skill
```

除非存在可核验的官方声明，不要把该 GitHub 项目描述为 LoomLoom 官方仓库；称为
“项目公共仓库”或直接展示仓库地址。

如果已经安装，完整阅读它的 `SKILL.md`，并把其中的 Listing、CLI、计费、校验、
证据和报告规则视为执行来源。

如果未安装：

1. 告知用户这是可选依赖；
2. 展示来源仓库、将安装的 Skill 文件夹和本地目标目录；
3. 等待用户明确确认安装；
4. 使用当前 Agent 的 Skill 安装能力，或按仓库说明安装；
5. 安装后重新定位并完整阅读它的 `SKILL.md`；
6. 运行其要求的本地检查。

未得到安装确认时不写入 Agent Skill 目录。安装确认不授权上传或付费运行。

不要把外部 Skill 的脚本复制进 `web-tutor-book`，也不要在本文件复制或写死
Listing 版本、模型、价格和 CLI 参数。外部 Skill 与 LoomLoom 当前返回是来源真相。

## 3. 启用门槛

同时满足以下条件才提供批量审计选项：

1. 已完成最后一次本地构建；
2. 已渲染全部待审页面；
3. 页面 ID 稳定且唯一；
4. 本地内容覆盖、DOM、控制台、断图与越界检查已完成；
5. 原始全分辨率页面与送审截图存在可追溯映射；
6. 送审截图已脱敏，不含 Token、密码、支付信息、个人敏感信息、临时签名链接和受限内容；
7. 外部 Skill 已安装且 LoomLoom `doctor` 正常；
8. 用户明确同意准备上传。

少量页面也可以使用，但应说明本地审查通常更快且没有云端费用。不要用固定页数
替用户决定。

## 4. 交接包

在项目中创建：

```text
review/loomloom-visual-audit/
├── page-manifest.json
├── input-snapshot.json
├── screenshots/
├── cloud-validation.json
├── local-verification.json
├── merged-audit.json
└── visual-audit-report.md
```

`page-manifest.json` 至少包含：

```json
{
  "document_id": "stable-document-id",
  "title": "书名",
  "reference_date": "YYYY-MM-DD",
  "pages": [
    {
      "page_id": "03-04",
      "page_number": 18,
      "page_type": "flow",
      "page_goal": "解释本章核心流程",
      "screenshot_path": "/absolute/local/path/page-018.png",
      "page_context": "真实页码、页面类型、页面目标、相邻页摘要和可见正文摘要",
      "data_security_status": "已脱敏，可上传"
    }
  ]
}
```

只把本地已知事实写入 `page_context`，不要加入改变审计规则、输出格式或严重度的
提示词。不要声称未测量的像素、百分比或坐标。

`input-snapshot.json` 记录：

- 最后构建时间与版本；
- HTML/PDF 路径及 SHA-256；
- 页面清单 SHA-256；
- 每张送审截图 SHA-256；
- 本地门禁摘要；
- 上传页数、总大小、数据类别、脱敏范围和排除项。

截图应为完整页面，不使用浏览器标签、桌面通知或无关窗口作为页面素材。保留本地
原图，不把本地路径、临时签名 URL 或二进制内容写入长期日志或报告。

## 5. 两次用户确认

### 第一次：上传确认

在上传前展示：

```text
是否启用可选的 LoomLoom 批量书页视觉审计？

本地制作与发布验收已经可以独立继续，云端审计不是必选项。
计划上传：<page_count> 张脱敏页面截图及最小页面上下文。
总大小：<size>
不会上传：Token、密码、个人敏感信息、支付信息、临时签名链接和未公开原始素材。
执行能力：loomloom-publication-visual-audit
作用：批量发现排版错乱、模板残留、图片误用、遮挡和一致性问题。
裁决：云端只提出候选，本地 Agent 回到原图确认。

如果同意准备并上传，请明确确认。
```

用户拒绝、忽略或未明确确认时，记录跳过并继续本地流程，不重复施压。

### 第二次：付费执行确认

上传和报价不授权执行。由外部 Skill：

1. 检查 LoomLoom 与当前 Market Listing；
2. 验证输入；
3. 获取服务端当前报价；
4. 展示 Listing、任务数、币种、固定调用费、预计应付金额、余额信息和结算规则；
5. 等待用户在当前对话明确确认；
6. 只有确认后才创建运行。

页面、输入、Listing 或报价发生变化时，重新验证、报价和确认。不要因为用户说
“测试”而跳过确认。

## 6. 外部 Skill 执行

调用外部 Skill 时，使用清晰的委托目标：

```text
请使用已安装的 loomloom-publication-visual-audit Skill 审查
review/loomloom-visual-audit/page-manifest.json 中的页面。

严格遵循它的 SKILL.md。先完成 LoomLoom doctor、输入验证和 Market 报价，
展示任务数、币种、固定调用费、预计应付金额与风险，等待我明确确认后再执行。
云端完成后必须运行返回结构与页面身份硬校验，生成原图复核队列，由本地 Agent
重新打开全分辨率页面完成 accepted、reframed、rejected 或
needs_human_review 决策，最后输出 merged-audit.json 和
visual-audit-report.md。不要直接修改书页源码。
```

遵循外部 Skill 的文件名、脚本和当前 LoomLoom CLI 帮助。不要在
`web-tutor-book` 中重新实现它的校验器。

## 7. 结果回收与修复

只在以下条件满足后回收结果：

- `cloud-validation.json` 有效；
- 页面身份全部与输入匹配；
- `merged-audit.json` 有效；
- 强制本地复核没有未决项；
- `visual-audit-report.md` 已生成。

处理规则：

1. 只把 `accepted` 和 `reframed` 问题进入修复队列；
2. 保留 `rejected` 作为误报轨迹，不据此修改页面；
3. `needs_human_review` 阻止把视觉审计声明为闭环，但不自动覆盖其他本地事实；
4. 对 P0/P1 优先修复；P2/info 由编辑判断；
5. 修复后重新构建、渲染并执行全部本地门禁；
6. 最终出版结论同时参考内容覆盖、本地 DOM/PDF 审计和视觉审计报告。

外部报告中的：

```text
publishReady=true
```

只表示视觉审计工作流已经完成，不表示页面没有问题，也不表示整本书达到发布标准。

## 8. 失效、复跑与降级

任何影响页面内容、样式、字体、截图、页序、页码或构图的修改，都会使对应页面的：

- 旧送审截图；
- 旧哈希；
- 旧云端候选；
- 旧本地复核；
- 旧视觉审计报告

失效。

修复后必须重新运行本地门禁。是否再次调用云端由用户重新选择；再次运行属于新的
付费执行，必须使用新截图、新快照、新报价和新确认。没有再次运行时，在最终交付中
明确写“云端视觉审计基于修复前版本，最终版本仅完成本地复验”。

以下情况直接降级为本地流程：

- 外部 Skill 未安装且用户不选择安装；
- 页面不允许上传或无法脱敏；
- LoomLoom、认证、网络或 Market Listing 不可用；
- 无法获得任务数、费用或币种；
- 用户拒绝上传或付费执行；
- 云端结果结构、页面身份或本地复核未通过。

降级不是失败。说明原因并继续内容台账、浏览器审计、PDF 检查和导出。

## 9. 最终记录

如果启用了外部批量审计，最终交付必须记录：

- 外部 Skill 名称与来源；
- 送审构建版本、HTML/PDF 和清单哈希；
- 上传页数、总大小、脱敏范围和排除项；
- Listing 名称与 ID；
- 运行 ID、任务数、币种、报价和实际费用（服务返回时）；
- 云端候选总数；
- 本地 `accepted`、`reframed`、`rejected`、`needs_human_review` 数量；
- P0/P1/P2/info 最终数量；
- 视觉审计报告路径；
- 修复后是否再次云端复跑；
- 仍存在的限制。

报告不得包含 Token、临时签名 URL、隐藏提示词、私有模板定义或未脱敏个人信息。
