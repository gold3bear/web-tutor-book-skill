# 内容驱动的封面系统

## 目录

1. 核心原则
2. 上下文隔离
3. CoverBrief
4. 风格预设
5. 动态提示词编译
6. 底图与 HTML 文字层
7. 生成流程
8. 验收清单

## 1. 核心原则

复用编辑系统，不复用上一项目的主视觉。每本书都从本书内容重新推导主体、动作、结构变化和留白位置。

基础编辑系统可以保持：

- 3:4 出版物比例和克制网格；
- 暖色纸张、衬线标题、可读正文与等宽代码字体；
- 经典科学图版或自然史技术书的安静、准确、权威气质；
- 网页、手机和 PDF 共用同一封面组件。

必须按内容变化：

- 主体及其动作；
- 动作如何转化为本书的系统关系；
- 视觉密度、方向和安全留白；
- 是否使用动物、植物、工具、机器或非具象结构。

不要维护默认动物清单，也不要把任何旧案例作为新封面的起点。没有合理生物隐喻时，明确采用非动物方案。

## 2. 上下文隔离

不要把整本书、历史项目 Prompt 或示例封面直接发送给图像模型。先在本地完成内容理解，再只传递当前封面必需的最小视觉简报。

不得进入图像 Prompt：

- 其他项目的主体、动作、动物或品牌；
- 与封面无关的正文、代码、URL、内部路径和聊天记录；
- Token、账号、个人信息或未公开业务数据；
- 仅用于解释方法的案例文字；
- 候选方案中没有被选中的视觉元素。

Prompt 编译前执行污染检查：

1. Prompt 中的专有名词是否都来自当前 CoverBrief；
2. 是否无理由重复了上一项目的主体或动作；
3. 是否包含当前画面不需要的产品细节；
4. 删除某个句子后画面意图是否仍然完整；如果是，删除该句；
5. 最终 Prompt 是否只描述“画什么、如何构图、以什么视觉语言呈现”。

## 3. CoverBrief

先生成结构化简报，不直接写图像 Prompt：

```yaml
cover_brief:
  topic: ""
  content_object: ""
  core_action: ""
  structural_change: ""
  reader_result: ""
  desired_impression: ""
  misreading_to_avoid: ""
  subject: ""
  subject_action: ""
  composition: ""
  safe_area:
    position: "top | left | right | lower"
    percent: 0
  accent_role: ""
  source_terms_allowed: []
  sensitive_terms_excluded: []
```

要求：

- `topic` 使用一句抽象语义，不复制整段正文；
- `subject` 和 `subject_action` 来自当前书的核心方法；
- `structural_change` 说明输入如何转化为结果；
- `source_terms_allowed` 是图像 Prompt 可以出现的专有词白名单；
- `sensitive_terms_excluded` 只用于本地过滤，不发送给图像模型；
- `safe_area` 根据 HTML 标题实际行数和副标题高度计算。

先提出两个 CoverBrief 方向，其中至少一个允许非动物方案。展示映射关系、误读风险和构图，等待用户确认后只保留被选中的简报。

## 4. 风格预设

风格预设只描述视觉语言，不包含主体、动作或具体项目名。基础预设：

```yaml
style_preset:
  id: "classic-technical-plate"
  rendering_language: "archival scientific plate"
  linework: "fine monochrome engraved linework"
  substrate: "warm uncoated paper"
  palette: "neutral ink with one restrained accent"
  visual_density: "precise, quiet, editorial"
  aspect_ratio: "3:4 portrait"
```

可以根据用户选择修改预设，但不要把其他封面的主体写进风格预设。风格负责“怎么画”，CoverBrief 负责“画什么”。

## 5. 动态提示词编译

不保存可直接复制的固定长 Prompt。每次只从已确认的 CoverBrief 和风格预设动态编译：

```text
prompt_parts = [
  describe(brief.subject, brief.subject_action),
  describe(brief.structural_change, brief.reader_result),
  describe(brief.composition, brief.safe_area),
  describe(style_preset),
  required_exclusion
]
prompt = join_non_empty(prompt_parts)
```

编译规则：

- 每个视觉名词必须能追溯到 CoverBrief；
- 不补写未确认的动物、道具、场景或产品元素；
- 不引用历史项目示例；
- 不发送完整书名、作者、版本等 HTML 文字层内容；
- 排除项只保留一句，避免大量否定词反向激活无关概念：

```text
Background artwork only; exclude all typography, logos, watermarks and interface elements.
```

如果模型仍生成伪文字，重新生成或局部清理；不要持续向 Prompt 追加大量具体禁词。

## 6. 底图与 HTML 文字层

封面图片只作为底图，不承担任何文字信息：

- 图片内部不得出现书名、副标题、作者、版本、系列名、Logo、水印、数字或伪文字；
- 所有文字由 HTML/CSS 排版，保持可搜索、可访问、可响应和可在 PDF 中提取；
- 先确定文字层需要的空间，再生成或裁切底图；
- 安全区应安静、低对比、纹理较少，主体和高对比细节位于安全区之外；
- 移除 HTML 文字层后，底图仍应具有完整视觉意义。

常用安全区：

- `top`：顶部约 28%–36%，适合中文长标题和副标题；
- `left`：左侧约 38%–45%，适合横向或宽封面；
- `right`：右侧约 34%–42%；
- `lower`：底部约 24%–32%，只用于较短标题。

`book-plan.md` 记录：

```text
封面文字层：
预计书名行数：
安全区位置与占比：
主视觉区域：
移动端裁切策略：
```

组件分层：

```tsx
<section className="book-cover">
  <img className="book-cover__plate" src={coverPlate} alt="与本书方法相关的主视觉说明" />
  <header className="book-cover__type">
    <span>系列与版本</span>
    <h1>书名</h1>
    <p>副标题</p>
  </header>
</section>
```

不要把完成后的 HTML 封面截图成一张图片，也不要为 PDF 制作带文字的第二套封面位图。

## 7. 生成流程

1. 阅读完整材料并在本地提炼内容语义；
2. 生成两个不共享主体的 CoverBrief 方向；
3. 估算 HTML 文字层，确定安全区；
4. 向用户展示映射、误读风险和构图；
5. 用户确认后丢弃未选方向，避免继续污染生成上下文；
6. 选择纯视觉风格预设；
7. 动态编译最小 Prompt 并执行污染检查；
8. 调用可用图像生成能力或使用用户素材；
9. 检查底图中的真实文字和伪文字；
10. 保存原始底图、网页优化图、CoverBrief、风格预设、最终 Prompt、模型和日期；
11. 使用同一 HTML 封面组件完成网页、手机和 PDF；
12. 对比三端裁切和安全区，不用整页缩放修复。

没有图像生成能力时，可以使用用户素材、公共领域科学图版或原创 SVG/CSS 底图，并记录来源。

## 8. 验收清单

- CoverBrief 是否只包含当前项目的必要视觉语义？
- 最终 Prompt 是否没有历史项目主体、示例词和无关细节？
- 主视觉是否解释本书核心方法，而不只是符合某种风格？
- 是否至少比较过两个方向，并在确认后丢弃未选方向？
- 是否无理由复用了上一项目的主体或动作？
- 图像 Prompt 是否没有完整正文、代码、URL、凭证和敏感信息？
- 底图是否没有文字、数字、伪文字、Logo、水印或界面元素？
- HTML 文字层、底图和主题 token 是否分离？
- 安全区是否根据标题实际行数确定？
- 桌面、手机和 PDF 是否保持同一识别系统与可读文字层？
- 是否保存 CoverBrief、最终 Prompt、模型、原图和优化图的来源记录？
