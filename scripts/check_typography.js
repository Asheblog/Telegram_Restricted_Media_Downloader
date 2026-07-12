#!/usr/bin/env node
/**
 * Guardrail: WebUI typography must stay on the compact type scale.
 * Allowed sizes: page 20 / title 16 / body 14 / caption 12 via Tailwind
 * text-xl / text-base / text-sm / text-xs (or .type-* wrappers).
 * Only raw font-size: 16px is allowed (html root + mobile inputs for iOS).
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const webui = path.join(root, 'module', 'adapters', 'webui');

const SCAN_DIRS = [
  path.join(webui, 'static'),
  path.join(webui, 'templates'),
];

const SCAN_EXTS = new Set(['.css', '.js', '.html']);
const SKIP_NAMES = new Set(['tailwind.min.css']);

const ARBITRARY_TEXT = /text-\[(\d+)px\]/g;
const FONT_SIZE_PX = /font-size:\s*(\d+(?:\.\d+)?)px/g;

const errors = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'fonts' || entry.name === 'dist') continue;
      walk(full);
      continue;
    }
    if (!SCAN_EXTS.has(path.extname(entry.name))) continue;
    if (SKIP_NAMES.has(entry.name)) continue;
    checkFile(full);
  }
}

function checkFile(file) {
  const rel = path.relative(root, file);
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split(/\r?\n/);

  lines.forEach((line, idx) => {
    const lineNo = idx + 1;
    let m;
    ARBITRARY_TEXT.lastIndex = 0;
    while ((m = ARBITRARY_TEXT.exec(line)) !== null) {
      errors.push(`${rel}:${lineNo}: forbidden arbitrary text-[${m[1]}px] — use type scale (text-xs/sm/base/xl)`);
    }
    FONT_SIZE_PX.lastIndex = 0;
    while ((m = FONT_SIZE_PX.exec(line)) !== null) {
      const px = m[1];
      if (px === '16') continue; // root + mobile inputs only
      errors.push(`${rel}:${lineNo}: forbidden font-size: ${px}px — use .type-* / text-xs|sm|base|xl`);
    }
  });
}

for (const dir of SCAN_DIRS) {
  if (fs.existsSync(dir)) walk(dir);
}

if (errors.length) {
  console.error('Typography check failed:\n' + errors.map((e) => '  ' + e).join('\n'));
  process.exit(1);
}

console.log('Typography check passed (compact scale: 12/14/16/20 + input 16px).');
