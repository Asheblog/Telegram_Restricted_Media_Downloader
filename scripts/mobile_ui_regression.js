const http = require('http');
const fs = require('fs');
const path = require('path');

function loadPlaywright() {
  try {
    return require('playwright');
  } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
  }
  const npxRoot = path.join(process.env.HOME || '', '.npm', '_npx');
  if (!fs.existsSync(npxRoot)) {
    throw new Error('Playwright is not installed. Run: npx --yes playwright --version');
  }
  const candidates = fs.readdirSync(npxRoot)
    .map(name => path.join(npxRoot, name, 'node_modules', 'playwright'))
    .filter(candidate => fs.existsSync(path.join(candidate, 'package.json')))
    .map(candidate => ({candidate, mtime: fs.statSync(candidate).mtimeMs}))
    .sort((a, b) => b.mtime - a.mtime);
  if (!candidates.length) {
    throw new Error('Playwright npx cache not found. Run: npx --yes playwright --version');
  }
  return require(candidates[0].candidate);
}

const { chromium } = loadPlaywright();

const root = path.resolve(__dirname, '..');
const webuiDir = path.join(root, 'module', 'adapters', 'webui');

function readText(file) {
  return fs.readFileSync(path.join(webuiDir, file), 'utf8');
}

function buildMobileHtml() {
  const fontsCss = readText(path.join('static', 'fonts.css'));
  const tailwindCss = readText(path.join('dist', 'tailwind.min.css'));
  const mobileBody = readText(path.join('templates', 'mobile_body.html'));
  const sharedJs = readText(path.join('static', 'shared.js'));
  const mobileScript = readText(path.join('static', 'mobile_script.js'));
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>TRMD 转存控制台</title>
<style>${fontsCss}</style>
<style>${tailwindCss}</style>
</head>
<body class="mob-body bg-bg text-text">
${mobileBody}
<script>${sharedJs}</script>
<script>${mobileScript}</script>
</body>
</html>`;
}

function startServer(html) {
  const server = http.createServer((req, res) => {
    if (req.url === '/' || req.url === '/mobile') {
      res.writeHead(200, {'content-type': 'text/html; charset=utf-8'});
      res.end(html);
      return;
    }
    if (req.url.startsWith('/fonts/')) {
      const filename = path.basename(new URL(req.url, 'http://127.0.0.1').pathname);
      const fontPath = path.join(webuiDir, 'static', 'fonts', filename);
      if (fs.existsSync(fontPath)) {
        res.writeHead(200, {'content-type': filename.endsWith('.woff') ? 'font/woff' : 'font/woff2'});
        res.end(fs.readFileSync(fontPath));
        return;
      }
    }
    res.writeHead(404, {'content-type': 'text/plain; charset=utf-8'});
    res.end('not found');
  });
  return new Promise(resolve => {
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      resolve({server, url: `http://127.0.0.1:${address.port}/mobile`});
    });
  });
}

function apiPayload(url) {
  const pathname = new URL(url).pathname;
  if (pathname === '/api/auth/status') return {step: 'done'};
  if (pathname === '/api/tasks') return {tasks: []};
  if (pathname === '/api/watches') return {watches: []};
  if (pathname === '/api/operations') {
    return {
      operations: [
        {
          id: 10,
          type: 'channel_download',
          status: 'success',
          payload: {chat_link: 'https://t.me/example_channel'},
          created_at: '2026-07-07 15:40:00',
        },
        {
          id: 11,
          type: 'upload',
          status: 'failure',
          payload: {path: 'C:\\Users\\wanglinyu\\Videos\\demo.mp4'},
          error_message: 'upload failed',
          created_at: '2026-07-07 15:41:00',
        },
      ],
    };
  }
  if (pathname === '/api/download-records') return {records: []};
  if (pathname === '/api/statistics') {
    return {
      tables: {
        link: {available: false, rows: 0},
        count: {available: false, rows: 0},
        upload: {available: false, rows: 0},
      },
    };
  }
  if (pathname === '/api/settings') {
    return {
      settings: {
        user: {},
        user: {download_type: ['video']},
        global: {
          forward_type: {video: true},
          message_filter: {media_types: {video: true}},
        },
      },
      schema: {
        download_type: ['video', 'photo'],
        forward_type: ['video', 'photo'],
        message_filter: {media_types: ['video', 'photo']},
      },
      settings_model: {
        options: {
          download_type: [{value: 'video', label: '视频'}, {value: 'photo', label: '图片'}],
          forward_type: [{value: 'video', label: '视频'}, {value: 'photo', label: '图片'}],
          message_filter_media_types: [{value: 'video', label: '视频'}, {value: 'photo', label: '图片'}],
        },
        selections: {
          user_download_type: ['video'],
          forward_type: {video: true},
          message_filter_media_types: {video: true},
        },
      },
    };
  }
  if (pathname === '/api/media/scan') {
    return {total_files: 0, total_size: 0, orphan_count: 0, orphans: []};
  }
  return {};
}

function findChromeExecutable() {
  const candidates = [
    process.env.PLAYWRIGHT_CHROME_EXECUTABLE,
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
    '/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    '/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe',
  ].filter(Boolean);
  return candidates.find(candidate => fs.existsSync(candidate));
}

async function main() {
  const html = buildMobileHtml();
  const {server, url} = await startServer(html);
  const apiCalls = [];
  const browserErrors = [];
  const executablePath = findChromeExecutable();
  const browser = await chromium.launch({
    headless: true,
    executablePath,
  });
  const page = await browser.newPage({
    viewport: {width: 430, height: 932},
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
  });
  page.on('pageerror', error => browserErrors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') browserErrors.push(message.text());
  });

  await page.route('**/api/**', route => {
    apiCalls.push(new URL(route.request().url()).pathname);
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(apiPayload(route.request().url())),
    });
  });

  const failures = [];
  try {
    await page.goto(url, {waitUntil: 'networkidle'});
    await page.waitForTimeout(250);

    const layout = await page.evaluate(() => {
      const contentEl = document.querySelector('#mob-content');
      const content = contentEl.getBoundingClientRect();
      const contentStyle = window.getComputedStyle(contentEl);
      const contentPaddingX = parseFloat(contentStyle.paddingLeft) + parseFloat(contentStyle.paddingRight);
      const panel = document.querySelector('#collapse-transfer-form').getBoundingClientRect();
      const head = document.querySelector('#collapse-transfer-form .mob-collapse__head');
      head.click();
      const opened = document.querySelector('#collapse-transfer-form').getBoundingClientRect();
      return {
        viewport: window.innerWidth,
        contentWidth: content.width,
        contentInnerWidth: content.width - contentPaddingX,
        closedWidth: panel.width,
        openedWidth: opened.width,
      };
    });
    if (Math.abs(layout.contentWidth - layout.viewport) > 1) {
      failures.push(`mob-content width ${layout.contentWidth} != viewport ${layout.viewport}`);
    }
    if (Math.abs(layout.closedWidth - layout.contentInnerWidth) > 1) {
      failures.push(`closed collapse width ${layout.closedWidth} != content inner ${layout.contentInnerWidth}`);
    }
    if (Math.abs(layout.openedWidth - layout.closedWidth) > 1) {
      failures.push(`collapse width changed ${layout.closedWidth} -> ${layout.openedWidth}`);
    }
    const transferOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (transferOverflow > 1) {
      failures.push(`transfer view overflows horizontally by ${transferOverflow}px`);
    }

    await page.waitForFunction(() => !document.body.innerText.includes('加载中...'));
    if (!apiCalls.includes('/api/tasks')) {
      failures.push('initial mobile transfer view did not request /api/tasks');
    }

    await page.click('[data-mob-tab="watches"]');
    await page.waitForTimeout(250);
    if (!apiCalls.includes('/api/watches')) {
      failures.push('watch tab did not request /api/watches');
    }

    await page.click('[data-mob-tab="downloads-uploads"]');
    await page.waitForTimeout(250);
    if (!apiCalls.includes('/api/settings')) {
      failures.push('downloads/uploads tab did not request /api/settings for download types');
    }
    const downloadTypesText = await page.locator('#mob-channel-download-types').innerText();
    if (!downloadTypesText.includes('视频') || downloadTypesText.includes('无可用类型')) {
      failures.push('download types did not render from settings on downloads/uploads tab');
    }
    if (!apiCalls.includes('/api/operations')) {
      failures.push('downloads/uploads tab did not request /api/operations');
    }
    const operationsText = await page.locator('#mob-operations-list').innerText();
    if (!operationsText.includes('频道下载') || !operationsText.includes('https://t.me/example_channel')) {
      failures.push('channel download operation did not render with payload chat link');
    }
    if (!operationsText.includes('本地上传') || !operationsText.includes('upload failed')) {
      failures.push('upload operation did not render payload path/error message');
    }
    const operationsOverflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (operationsOverflow > 1) {
      failures.push(`downloads/uploads view overflows horizontally by ${operationsOverflow}px`);
    }

    await page.click('[data-mob-tab="profile"]');
    const profileLayout = await page.evaluate(() => {
      const contentEl = document.querySelector('#mob-content');
      const content = contentEl.getBoundingClientRect();
      const contentStyle = window.getComputedStyle(contentEl);
      const contentPaddingX = parseFloat(contentStyle.paddingLeft) + parseFloat(contentStyle.paddingRight);
      const profileMenu = document.querySelector('#mob-profile-menu').getBoundingClientRect();
      return {
        contentInnerWidth: content.width - contentPaddingX,
        profileMenuWidth: profileMenu.width,
        overflow: document.documentElement.scrollWidth - window.innerWidth,
      };
    });
    if (Math.abs(profileLayout.profileMenuWidth - profileLayout.contentInnerWidth) > 1) {
      failures.push(`profile menu width ${profileLayout.profileMenuWidth} != content inner ${profileLayout.contentInnerWidth}`);
    }
    if (profileLayout.overflow > 1) {
      failures.push(`profile view overflows horizontally by ${profileLayout.overflow}px`);
    }
    await page.click('[data-profile-nav="statistics"]');
    await page.waitForTimeout(250);
    if (!apiCalls.includes('/api/statistics')) {
      failures.push('statistics subpage did not request /api/statistics');
    }
    const statisticsText = await page.locator('#mob-statistics-list').innerText();
    if (!statisticsText.includes('链接统计表') || statisticsText.includes('暂无统计数据')) {
      failures.push('statistics subpage did not render statistics table cards');
    }
    const settingsCallCountBefore = apiCalls.filter(pathname => pathname === '/api/settings').length;
    await page.click('#mob-topbar-back');
    await page.click('[data-profile-nav="settings"]');
    await page.waitForTimeout(250);
    const settingsCallCountAfter = apiCalls.filter(pathname => pathname === '/api/settings').length;
    if (settingsCallCountAfter < settingsCallCountBefore) {
      failures.push('settings subpage lost settings data');
    }

    const loadingText = await page.evaluate(() => document.body.innerText.includes('加载中...'));
    if (loadingText) failures.push('mobile UI still contains lingering 加载中...');
    if (browserErrors.length) failures.push(`browser errors:\n${browserErrors.join('\n')}`);

    if (failures.length) {
      console.error(failures.join('\n'));
      process.exitCode = 1;
    } else {
      console.log('mobile UI regression passed');
    }
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
