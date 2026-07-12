// module/adapters/webui/static/watch_ui_helpers.js
(function (root) {
  function shortTelegramLink(link) {
    if (!link) return '-';
    return String(link)
      .replace(/^https?:\/\/(t\.me|telegram\.me)\//i, '')
      .replace(/\/+$/, '') || '-';
  }

  function formatWatchRoute(sourceLink, targetLink) {
    return shortTelegramLink(sourceLink) + ' → ' + shortTelegramLink(targetLink || '本地');
  }

  function summarizeWatchEvent(evt) {
    const status = evt && evt.status;
    const message = (evt && evt.message) || '';
    if (status === 'success') {
      return { kind: 'success', titleKey: 'watches.eventForwarded', detail: '' };
    }
    if (status === 'skipped' || /过滤|filter/i.test(message)) {
      var titleKey = 'watches.eventSkipped';
      if (/关键词|keyword/i.test(message)) titleKey = 'watches.eventFilterKeyword';
      return { kind: 'filtered', titleKey: titleKey, detail: message };
    }
    return { kind: 'failure', titleKey: 'watches.eventFailed', detail: message };
  }

  function filterWatchEventsByStatus(events, filter) {
    var list = events || [];
    if (!filter || filter === 'all') return list.slice();
    return list.filter(function (evt) {
      var kind = summarizeWatchEvent(evt).kind;
      if (filter === 'filtered') return kind === 'filtered';
      return kind === filter;
    });
  }

  var WatchUiHelpers = {
    shortTelegramLink: shortTelegramLink,
    formatWatchRoute: formatWatchRoute,
    summarizeWatchEvent: summarizeWatchEvent,
    filterWatchEventsByStatus: filterWatchEventsByStatus,
  };

  root.WatchUiHelpers = WatchUiHelpers;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WatchUiHelpers: WatchUiHelpers };
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
