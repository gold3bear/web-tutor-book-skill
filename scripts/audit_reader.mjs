#!/usr/bin/env node

import { createRequire } from "node:module";
import { access, mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

const require = createRequire(import.meta.url);

function loadPlaywrightAdapter() {
  const attempts = [];
  const loaders = [];
  const browserNodeModules =
    process.env.BROWSER_NODE_MODULES ?? process.env.CODEX_NODE_MODULES;
  if (browserNodeModules) {
    loaders.push([
      "BROWSER_NODE_MODULES",
      () => require(resolve(browserNodeModules, "playwright")),
    ]);
  }
  loaders.push(
    [
      "current project",
      () => createRequire(resolve(process.cwd(), "package.json"))("playwright"),
    ],
    ["Node.js module resolution", () => require("playwright")],
  );
  for (const [label, load] of loaders) {
    try {
      return load();
    } catch (error) {
      attempts.push(`${label}: ${error.code ?? error.message}`);
    }
  }
  throw new Error(
    [
      "The optional Playwright audit adapter is unavailable.",
      "Use the local Agent's available browser tools to perform the same publication checks,",
      "or install Playwright in the tutorial project,",
      "or set BROWSER_NODE_MODULES to a node_modules directory containing Playwright.",
      `Resolution attempts: ${attempts.join("; ")}`,
    ].join(" "),
  );
}

const { chromium } = loadPlaywrightAdapter();

const baseUrl = process.argv[2] ?? "http://127.0.0.1:5173/";
const outputPath = process.argv[3] ?? "review/publication-dom-audit.json";
const printPageSelector = process.env.PRINT_PAGE_SELECTOR ?? ".ebr-print-page";
const readerPageSelector = process.env.READER_PAGE_SELECTOR ?? ".ebr-stage > .ebr-page";
const sourceBodySelector = process.env.SOURCE_BODY_SELECTOR ?? ".ebr-source__body";
const strict = process.env.AUDIT_STRICT !== "0";
const forbiddenVisibleLabels = (
  process.env.FORBIDDEN_VISIBLE_LABELS ??
  "完整原文 · 可在页内继续阅读||先看结构，下一页阅读完整原文。"
)
  .split("||")
  .map((label) => label.trim())
  .filter(Boolean);
const chromeCandidates = [
  process.env.CHROME_PATH,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
].filter(Boolean);

let executablePath;
for (const candidate of chromeCandidates) {
  try {
    await access(candidate);
    executablePath = candidate;
    break;
  } catch {}
}

const browser = await chromium.launch({
  headless: true,
  ...(executablePath ? { executablePath } : {}),
});

function collectConsoleErrors(page) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  return errors;
}

async function waitForAssets(page) {
  await page.evaluate(async () => {
    await document.fonts?.ready;
    await Promise.all(
      [...document.images].map((image) =>
        image.complete
          ? Promise.resolve()
          : new Promise((done) => {
              image.addEventListener("load", done, { once: true });
              image.addEventListener("error", done, { once: true });
            }),
      ),
    );
  });
}

function pageAudit(pageElement, index, kind, allowVerticalOverflow, forbiddenLabels) {
  const pageRect = pageElement.getBoundingClientRect();
  const images = [...pageElement.querySelectorAll("img")];
  const insideScrollableRegion = (element) => {
    for (let parent = element.parentElement; parent && parent !== pageElement; parent = parent.parentElement) {
      const style = getComputedStyle(parent);
      if (
        (/(auto|scroll)/.test(style.overflowX) && parent.scrollWidth > parent.clientWidth + 1) ||
        (/(auto|scroll)/.test(style.overflowY) && parent.scrollHeight > parent.clientHeight + 1)
      ) return true;
    }
    return false;
  };
  const outside = [...pageElement.querySelectorAll("*")]
    .filter((element) => {
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      if (
        style.display === "none" ||
        style.visibility === "hidden" ||
        rect.width === 0 ||
        rect.height === 0 ||
        insideScrollableRegion(element)
      ) return false;
      return (
        rect.right > pageRect.right + 1 ||
        rect.left < pageRect.left - 1 ||
        (!allowVerticalOverflow && (rect.bottom > pageRect.bottom + 1 || rect.top < pageRect.top - 1))
      );
    })
    .slice(0, 8)
    .map((element) => ({
      tag: element.tagName,
      className: String(element.className ?? "").slice(0, 100),
      text: (element.textContent ?? "").trim().slice(0, 80),
    }));
  const visibleLeafTexts = [...pageElement.querySelectorAll("*")]
    .filter((element) => element.children.length === 0 && getComputedStyle(element).display !== "none")
    .map((element) => (element.textContent ?? "").trim());
  const editorialLabels = forbiddenLabels.filter((label) => visibleLeafTexts.includes(label));
  return {
    index: index + 1,
    id: pageElement.dataset.pageId ?? pageElement.getAttribute("aria-label") ?? "",
    kind,
    textLength: (pageElement.innerText ?? "").trim().length,
    imageCount: images.length,
    brokenImageCount: images.filter((image) => !image.complete || image.naturalWidth === 0).length,
    missingAltCount: images.filter((image) => !image.hasAttribute("alt")).length,
    decorativeImageCount: images.filter(
      (image) => image.hasAttribute("alt") && !image.alt.trim(),
    ).length,
    scrollWidth: pageElement.scrollWidth,
    clientWidth: pageElement.clientWidth,
    scrollHeight: pageElement.scrollHeight,
    clientHeight: pageElement.clientHeight,
    outside,
    editorialLabels,
  };
}

const pageAuditSource = pageAudit.toString();

async function auditPrintView() {
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  const errors = collectConsoleErrors(page);
  const url = new URL(baseUrl);
  url.searchParams.set("mode", "print");
  await page.goto(url.href, { waitUntil: "networkidle" });
  await waitForAssets(page);
  const rows = await page.evaluate(
    ({ selector, auditSource, forbiddenLabels }) => {
      const audit = (0, eval)(`(${auditSource})`);
      return [...document.querySelectorAll(selector)].map((element, index) => {
        const kind = [...element.classList]
          .find((className) => className.startsWith("ebr-print-page--"))
          ?.replace("ebr-print-page--", "") ?? "";
        return audit(element, index, kind, kind === "source", forbiddenLabels);
      });
    },
    {
      selector: printPageSelector,
      auditSource: pageAuditSource,
      forbiddenLabels: forbiddenVisibleLabels,
    },
  );
  await page.close();
  return { errors, rows };
}

async function auditReader(ids, name, width, height) {
  const page = await browser.newPage({ viewport: { width, height } });
  const errors = collectConsoleErrors(page);
  await page.goto(`${baseUrl}#page=${encodeURIComponent(ids[0])}`, { waitUntil: "networkidle" });
  await waitForAssets(page);
  const rows = [];
  for (const id of ids) {
    await page.evaluate((pageId) => { location.hash = `page=${pageId}`; }, id);
    await page.waitForTimeout(30);
    rows.push(await page.evaluate(
      ({ selector, sourceSelector, pageId, auditSource, forbiddenLabels }) => {
        const audit = (0, eval)(`(${auditSource})`);
        const element = document.querySelector(selector);
        if (!element) return { id: pageId, missing: true };
        const result = audit(element, 0, "reader", false, forbiddenLabels);
        const sourceBody = element.querySelector(sourceSelector);
        return {
          ...result,
          id: pageId,
          sourceBodyOverflow: sourceBody ? sourceBody.scrollHeight - sourceBody.clientHeight : 0,
        };
      },
      {
        selector: readerPageSelector,
        sourceSelector: sourceBodySelector,
        pageId: id,
        auditSource: pageAuditSource,
        forbiddenLabels: forbiddenVisibleLabels,
      },
    ));
  }
  await page.close();
  return { name, width, height, errors, rows };
}

try {
  const print = await auditPrintView();
  const ids = print.rows.map((page) => page.id).filter(Boolean);
  const readers = [];
  for (const [name, width, height] of [
    ["desktop", 1440, 1000],
    ["mobile390", 390, 844],
    ["mobile360", 360, 800],
  ]) readers.push(await auditReader(ids, name, width, height));
  const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);
  const failures = [];
  if (print.rows.length === 0) failures.push("No print pages were found.");
  if (print.rows.some((page) => !page.id)) failures.push("One or more print pages have no page ID.");
  if (duplicateIds.length > 0) failures.push(`Duplicate page IDs: ${[...new Set(duplicateIds)].join(", ")}`);
  for (const page of print.rows) {
    const label = page.id || `print page ${page.index}`;
    if (page.textLength === 0 && page.imageCount === 0) failures.push(`${label} is blank.`);
    if (page.brokenImageCount > 0) failures.push(`${label} has broken images.`);
    if (page.missingAltCount > 0) failures.push(`${label} has images without alt attributes.`);
    if (page.outside.length > 0) failures.push(`${label} has content outside the fixed page.`);
    if (page.editorialLabels.length > 0) failures.push(`${label} exposes editorial labels: ${page.editorialLabels.join(", ")}`);
  }
  for (const error of print.errors) failures.push(`Print view error: ${error}`);
  for (const reader of readers) {
    if (reader.rows.length !== ids.length) failures.push(`${reader.name} reader page count does not match the print plan.`);
    for (const row of reader.rows) {
      const label = `${reader.name} ${row.id || `page ${row.index}`}`;
      if (row.missing) {
        failures.push(`${label} is missing.`);
        continue;
      }
      if (row.brokenImageCount > 0) failures.push(`${label} has broken images.`);
      if (row.missingAltCount > 0) failures.push(`${label} has images without alt attributes.`);
      if (row.outside.length > 0) failures.push(`${label} has content outside the reader page.`);
      if (row.editorialLabels.length > 0) failures.push(`${label} exposes editorial labels: ${row.editorialLabels.join(", ")}`);
    }
    for (const error of reader.errors) failures.push(`${reader.name} reader error: ${error}`);
  }
  const result = {
    createdAt: new Date().toISOString(),
    baseUrl,
    selectors: { printPageSelector, readerPageSelector, sourceBodySelector },
    forbiddenVisibleLabels,
    print: { pageCount: print.rows.length, duplicateIds: [...new Set(duplicateIds)], ...print },
    readers,
    summary: {
      passed: failures.length === 0,
      strict,
      failureCount: failures.length,
      failures,
    },
  };
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`);
  console.log(outputPath);
  console.log(failures.length === 0 ? "Audit passed." : `Audit found ${failures.length} failure(s).`);
  if (strict && failures.length > 0) process.exitCode = 1;
} finally {
  await browser.close();
}
