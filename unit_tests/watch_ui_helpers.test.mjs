// unit_tests/watch_ui_helpers.test.mjs
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const { WatchUiHelpers: h } = require(
  path.join(__dirname, '../module/adapters/webui/static/watch_ui_helpers.js')
);

assert.equal(h.shortTelegramLink('https://t.me/pikpak_bot'), 'pikpak_bot');
assert.equal(h.shortTelegramLink('https://t.me/c/4209310295'), 'c/4209310295');
assert.equal(h.shortTelegramLink(''), '-');

assert.equal(
  h.formatWatchRoute('https://t.me/c/4209310295', 'https://t.me/pikpak_bot'),
  'c/4209310295 → pikpak_bot'
);

assert.deepEqual(
  h.summarizeWatchEvent({ status: 'success', message: '转发成功。' }),
  { kind: 'success', badgeKey: 'watches.badgeSuccess', title: '', titleKey: null, detail: '' }
);
assert.deepEqual(
  h.summarizeWatchEvent({ status: 'success', message: '转发成功：视频' }),
  { kind: 'success', badgeKey: 'watches.badgeSuccess', title: '视频', titleKey: null, detail: '' }
);
assert.equal(
  h.summarizeWatchEvent({
    status: 'skipped',
    message: '跳过转发(已被消息过滤器过滤：命中过滤关键词：[广告])',
  }).titleKey,
  'watches.eventFilterKeyword'
);
assert.equal(
  h.summarizeWatchEvent({ status: 'failure', message: '转发失败：timeout' }).kind,
  'failure'
);

const events = [
  { status: 'success', message: 'ok' },
  { status: 'skipped', message: 'filtered' },
  { status: 'failure', message: 'err' },
];
assert.equal(h.filterWatchEventsByStatus(events, 'all').length, 3);
assert.equal(h.filterWatchEventsByStatus(events, 'success').length, 1);
assert.equal(h.filterWatchEventsByStatus(events, 'filtered').length, 1);
assert.equal(h.filterWatchEventsByStatus(events, 'failure').length, 1);

const partitioned = h.partitionWatchesByComment([
  { id: 'a', include_comment: false },
  { id: 'b', include_comment: true },
  { id: 'c' },
  { id: 'd', include_comment: 1 },
]);
assert.deepEqual(partitioned.withoutComment.map((w) => w.id), ['a', 'c']);
assert.deepEqual(partitioned.withComment.map((w) => w.id), ['b', 'd']);
assert.deepEqual(h.partitionWatchesByComment(null), { withoutComment: [], withComment: [] });

console.log('watch_ui_helpers.test.mjs: ok');
