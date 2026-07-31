# 网页教程书的视觉保真 PDF 导出

## 目录

1. 先确定 PDF 产品类型
2. 使用同一组件树
3. 固定视觉页与流式正文页
4. 打印 CSS 与浏览器导出
5. 常见失败模式
6. 逐页验收与空白页处理
7. 交付检查表
8. 发布同步门禁

## 1. 先确定 PDF 产品类型

不要把所有 PDF 都当成同一种产品：

- **视觉保真分享版**：尽量保持网页电子书的封面、3:4 书页、Chapter Open、流程图、插图和字体层级。适合对外分享。
- **A4 内容打印版**：按纸张阅读重新排版，允许与网页不同。适合打印、批注和长文阅读。

用户说“导出的 PDF 要和网页版一样”时，选择视觉保真分享版。可以同时保留 A4 版，但文件名和交付说明必须明确区分。

## 2. 使用同一组件树

视觉保真版必须复用网页阅读器的页面数据、React/Vue 组件、主题 token、字体和素材。推荐增加 `?mode=print` 或独立 `/print` 路由，将全部语义页顺序渲染：

```tsx
export function PrintBook() {
  return (
    <main className="print-book">
      {BOOK_PAGES.map((page, index) => (
        <article
          className={`print-page print-page--${page.kind}`}
          data-page-id={page.id}
          key={page.id}
        >
          {page.content}
        </article>
      ))}
    </main>
  );
}
```

不要：

- 在 ReportLab、Canvas 或第二套 HTML 中重新拼一遍封面与流程图；
- 把网页逐页截成图片后合成 PDF；
- 为 PDF 维护另一份手工章节内容。

ReportLab 可以用于明确命名的 A4 内容版，但不用于声称“复用网页版设计”的版本。

## 3. 固定视觉页与流式正文页

同一本书需要两种打印策略。

### 固定视觉页

以下页型保持一个物理页面和固定出版物构图：

- cover；
- chapter-open；
- visual companion；
- 流程图、信息图；
- 以真实截图为主体的页面；
- 内容已经确认能放入一页的案例页和结论页。

固定视觉页使用与阅读器相同的宽高比，例如 3:4。检查：

```js
scrollHeight === clientHeight
scrollWidth === clientWidth
```

边框、阴影或箭头可能让 `scrollWidth` 多出少量像素；同时检查所有后代元素的实际边界，不能只看一个数值。

不要通过缩放整张网页或在 PDF 导出时设置小于 100% 的统一比例解决溢出。页面看似“都放下了”但主体缩在上方、下方出现大面积留白，仍然是不合格版式。固定页的根容器必须真实占满纸张尺寸；截图或图表在其内容区内使用 `object-fit: contain`，而不是缩放整页。

### 流式正文页

解释正文、长 Prompt、代码、表格和引用在网页中可能依赖内部滚动。打印时必须取消滚动和绝对定位，让内容跨物理页自然流动：

```css
.print-page--source {
  height: auto;
  min-height: var(--book-page-height);
  overflow: visible;
}

.print-page--source .source-page {
  position: relative;
  inset: auto;
  min-height: var(--book-page-height);
}

.print-page--source .source-body {
  overflow: visible;
}
```

使用 `break-inside: avoid` 要克制。适合短表格、短流程图和标题块；不适合可能超过剩余页高的长 Prompt 或大卡片。错误地禁止拆分页会产生“只有标题的一页”或大面积空白。遇到这种情况依次选择：

1. 为长内容创建语义续页；
2. 允许卡片内部跨页，并让卡片标题与首段保持在一起；
3. 适度减少打印版上下留白；
4. 最后才小幅调整字号，不能牺牲可读性。

不要在长正文页沿用网页内部滚动条；PDF 不存在可靠的滚动阅读。

## 4. 打印 CSS 与浏览器导出

页面尺寸必须同时写入组件布局和 `@page`：

```css
:root {
  --book-page-width: 150mm;
  --book-page-height: 200mm;
}

@page {
  size: 150mm 200mm;
  margin: 0;
}

@media print {
  html,
  body,
  #root,
  .print-book {
    width: var(--book-page-width);
    margin: 0;
    padding: 0;
  }

  .print-page {
    width: var(--book-page-width);
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }

  .print-page + .print-page {
    break-before: page;
  }
}
```

使用 Chromium/Playwright 导出并设置：

- `printBackground: true`；
- `preferCSSPageSize: true`；
- 四边 margin 为 0；
- 不启用浏览器默认页眉页脚；
- 导出前等待 `document.fonts.ready`；
- 等待全部图片完成加载，包括失败事件，避免任务永久挂起。

若 Playwright 自带 Chromium 不存在，优先检测本机 Chrome/Chromium 的 `executablePath`，不要立即下载大型浏览器依赖。导出脚本应允许用环境变量覆盖浏览器路径与 Node 模块路径。

输出放在 `output/pdf/`；中间渲染放在 `tmp/pdfs/`。不得覆盖另一种用途的 PDF。

## 5. 常见失败模式

### PDF 封面像另一份文档

原因：在 PDF 库中重新排版，而不是复用网页组件。表现为标题居中、插图缩小、顶栏消失、留白和字体层级改变。

修复：回到同源打印路由；让封面组件与网页共用 CSS、素材和页面比例。

### 流程图变糊

原因：使用截图或低分辨率画布。

修复：让流程图继续以 HTML/CSS/SVG 渲染，再由 Chromium 写入 PDF。确认 PDF 放大后文字和线条仍清晰。

### 正文被裁掉

原因：把网页的固定高度、`overflow: hidden/auto` 原样用于打印。

修复：仅视觉页固定高度；正文页取消内部滚动并允许分页。

### 出现标题孤页或只有一行的尾页

原因：长卡片设置了 `break-inside: avoid`，或打印可用高度略小于页面组件。

修复：允许长卡片跨页、减少打印留白、创建续页，并复查 widow/orphan。不要用删除文字解决。

### 出现完全空白的尾页

原因：固定物理高度、CSS 分页和像素/mm 舍入共同产生额外碎片页。

修复顺序：

1. 检查 `height`、`min-height`、边框和 `break-before/after`；
2. 确认空白页不是规划中的图片页或留白页；
3. 用文本提取定位候选页；
4. 将候选页渲染成图片，确认没有截图、矢量线条、页码或其他墨迹；
5. 只删除同时满足“无有效文本、无有效墨迹、非计划页型”的页面。

禁止仅凭文本提取为空自动删除页面；图片页和纯矢量流程图也可能没有可提取文字。

### PDF 字体变成方框或层级变平

原因：字体未加载、未嵌入，或者 PDF 版统一替换成单一中文字体。

修复：等待字体加载，检查 PDF 实际字体；网页字体无法嵌入时选择允许嵌入且视觉相近的替代字体，并记录差异。

## 6. 逐页验收与空白页处理

导出成功不是完成。每次有意义的修改后：

1. 用 `pdfinfo` 检查页数、尺寸和文件大小；
2. 用 Poppler 将所有页渲染成 PNG；
3. 生成带页码的 contact sheet；
4. 扫描空白页、极少文字页、突然改变背景色或比例的页面；
5. 放大检查以下代表页：
   - 封面；
   - 第一个 Chapter Open；
   - 至少两个复杂流程图；
   - 最长正文或 Prompt；
   - 代码页和表格页；
   - 真实产品截图页；
   - 最后一页；
6. 与网页版对应页面截图并排比较；
7. 提取 PDF 文本，抽查标题、正文、代码和中文字符；
8. 检查可点击链接数量与目标；
9. 再运行内容覆盖审计。

如果网页有封面、流程图或截图页，至少选择各一页，把网页版截图与 PDF 渲染页并排比较。只看 contact sheet 容易漏掉统一缩小、页脚偏移和截图清晰度问题。

视觉审查必须查看所有页的 contact sheet，不能只检查封面。发现候选问题后再看原尺寸单页。

## 7. 交付检查表

交付时报告：

- PDF 类型：视觉保真版或 A4 内容版；
- 页面尺寸与总页数；
- 文件路径和文件大小；
- 内容覆盖率、源内容漂移和批准省略；
- 文字是否可搜索/复制；
- 链接是否保留；
- 是否使用同一组件树；
- 已检查的代表页面和 contact sheet 路径；
- 仍存在的差异，例如流式正文续页没有复制网页 folio。

只有以下条件同时通过才可交付：

- 封面和视觉页与网页版构图一致；
- 固定页无裁切；
- 流式页无内容丢失；
- 无未解释的空白页；
- 中文、代码、表格、截图和链接正常；
- 正式构建与内容覆盖审计通过。

## 8. 发布同步门禁

最后一次内容或样式修改会使此前的 PDF 与审计证据失效。按以下顺序重新收口：

1. 类型检查和正式构建；
2. 打印视图页数、空白页、破图和越界审计；
3. 导出最终 PDF，确认文件名和元数据标题；
4. 用 `pdfinfo`、`pypdf` 或 `pdfplumber` 检查页数、页面尺寸、空文本页、链接、中文与原始 Markdown；
5. 渲染全部 PDF 页面并重新生成 contact sheet；
6. 放大检查封面、流程图、真实截图、最长正文、末页；
7. 重新生成审计报告和 SHA-256；
8. 最后才复制、压缩或发布交付包。

不要在“删一个按钮”“改一个标签”“换一张截图”后沿用旧 PDF、旧 contact sheet 或旧哈希。
