# coding=UTF-8
"""WebUI HTTP handlers split by API domain."""

from . import (
    archive_author,
    auth,
    media,
    misc,
    settings,
    setup_api,
    static_pages,
    stats,
    tasks,
    watches,
)

# GET: after auth + setup gate (static_pages handled separately before gate)
GET_DISPATCHERS = (
    auth.handle_get,
    setup_api.handle_get,
    tasks.handle_get,
    settings.handle_get,
    misc.handle_get,
    stats.handle_get,
    watches.handle_get,
    media.handle_get,
    archive_author.handle_get,
)

# POST: after auth + setup gate (auth login/logout handled before gate)
POST_DISPATCHERS = (
    auth.handle_post,
    setup_api.handle_post,
    tasks.handle_post,
    stats.handle_post,
    watches.handle_post,
    misc.handle_post,
    media.handle_post,
    archive_author.handle_post,
)

PATCH_DISPATCHERS = (
    settings.handle_patch,
)

PUT_DISPATCHERS = (
    watches.handle_put,
)

DELETE_DISPATCHERS = (
    misc.handle_delete,
    watches.handle_delete,
    tasks.handle_delete,
)


def dispatch_get(handler, server, parsed) -> bool:
    for dispatch in GET_DISPATCHERS:
        if dispatch(handler, server, parsed):
            return True
    return False


def dispatch_post(handler, server, parsed) -> bool:
    for dispatch in POST_DISPATCHERS:
        if dispatch(handler, server, parsed):
            return True
    return False


def dispatch_patch(handler, server, parsed) -> bool:
    for dispatch in PATCH_DISPATCHERS:
        if dispatch(handler, server, parsed):
            return True
    return False


def dispatch_put(handler, server, parsed) -> bool:
    for dispatch in PUT_DISPATCHERS:
        if dispatch(handler, server, parsed):
            return True
    return False


def dispatch_delete(handler, server, parsed) -> bool:
    for dispatch in DELETE_DISPATCHERS:
        if dispatch(handler, server, parsed):
            return True
    return False
