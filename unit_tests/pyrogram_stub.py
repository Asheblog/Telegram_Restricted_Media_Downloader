# coding=UTF-8
import sys
import types


class Dummy:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return Dummy(*args, **kwargs)

    def __and__(self, other):
        return self

    def __or__(self, other):
        return self

    def __iter__(self):
        return iter(())


class DummyModule(types.ModuleType):
    def __getattr__(self, name):
        value = type(name, (Dummy,), {})
        setattr(self, name, value)
        return value


class DummyError(Exception):
    def __init__(self, value=0, *args):
        super().__init__(*args)
        self._value = value

    @property
    def value(self):
        return self._value


class FileType:
    VOICE = 'voice'
    VIDEO = 'video'
    ANIMATION = 'animation'
    VIDEO_NOTE = 'video_note'
    DOCUMENT = 'document'
    STICKER = 'sticker'
    AUDIO = 'audio'

    def __init__(self, value):
        self.value = value


def install_pyrogram_stub() -> None:
    if 'pyrogram' in sys.modules:
        return

    pyrogram = DummyModule('pyrogram')
    pyrogram.__path__ = []
    pyrogram.__version__ = 'test'
    pyrogram.__license__ = 'test'
    pyrogram.Client = type('Client', (Dummy,), {})
    pyrogram.filters = Dummy()

    pyrogram_types = DummyModule('pyrogram.types')
    pyrogram_types.Message = type('Message', (Dummy,), {})
    pyrogram_types.Chat = type('Chat', (Dummy,), {})
    pyrogram_types.List = list
    messages_and_media = DummyModule('pyrogram.types.messages_and_media')
    bots_and_keyboards = DummyModule('pyrogram.types.bots_and_keyboards')

    class LinkPreviewOptions:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    messages_and_media.LinkPreviewOptions = LinkPreviewOptions
    messages_and_media.ReplyParameters = type('ReplyParameters', (Dummy,), {})
    bots_and_keyboards.InlineKeyboardButton = type('InlineKeyboardButton', (Dummy,), {})
    bots_and_keyboards.InlineKeyboardMarkup = type('InlineKeyboardMarkup', (Dummy,), {})
    bots_and_keyboards.BotCommand = type('BotCommand', (Dummy,), {})
    bots_and_keyboards.CallbackQuery = type('CallbackQuery', (Dummy,), {})
    pyrogram_types.messages_and_media = messages_and_media
    pyrogram_types.bots_and_keyboards = bots_and_keyboards
    pyrogram.types = pyrogram_types

    parse_mode = DummyModule('pyrogram.enums.parse_mode')
    parse_mode.ParseMode = type('ParseMode', (Dummy,), {})
    enums = DummyModule('pyrogram.enums')
    enums.parse_mode = parse_mode

    errors = DummyModule('pyrogram.errors')
    for name in (
            'BadMsgNotification', 'FileReferenceExpired', 'FloodWait', 'FloodPremiumWait',
            'InternalServerError', 'ServiceUnavailable', 'AuthBytesInvalid', 'RPCError',
            'CDNFileHashMismatch', 'VolumeLocNotFound'
    ):
        setattr(errors, name, type(name, (DummyError,), {}))

    bad_request = DummyModule('pyrogram.errors.exceptions.bad_request_400')
    for name in (
            'MsgIdInvalid', 'UsernameInvalid', 'ChannelInvalid', 'BotMethodInvalid',
            'UsernameNotOccupied', 'PeerIdInvalid', 'MessageNotModified',
            'ChannelPrivate', 'ChatForwardsRestricted', 'AccessTokenInvalid',
            'MediaCaptionTooLong', 'MessageIdInvalid'
    ):
        setattr(bad_request, name, type(name, (DummyError,), {}))

    not_acceptable = DummyModule('pyrogram.errors.exceptions.not_acceptable_406')
    for name in ('ChannelPrivate', 'ChatForwardsRestricted'):
        setattr(not_acceptable, name, type(name, (DummyError,), {}))

    unauthorized = DummyModule('pyrogram.errors.exceptions.unauthorized_401')
    for name in ('SessionRevoked', 'AuthKeyUnregistered', 'SessionExpired', 'Unauthorized'):
        setattr(unauthorized, name, type(name, (DummyError,), {}))

    forbidden = DummyModule('pyrogram.errors.exceptions.forbidden_403')
    forbidden.ChatWriteForbidden = type('ChatWriteForbidden', (DummyError,), {})
    exceptions = DummyModule('pyrogram.errors.exceptions')
    for name in (
            'FilePartMissing', 'ChatAdminRequired', 'PhotoInvalidDimensions',
            'PhotoSaveFileInvalid', 'PhoneNumberInvalid'
    ):
        setattr(exceptions, name, type(name, (DummyError,), {}))

    handlers = DummyModule('pyrogram.handlers')
    handlers.MessageHandler = type('MessageHandler', (Dummy,), {})
    handlers.CallbackQueryHandler = type('CallbackQueryHandler', (Dummy,), {})

    file_id = DummyModule('pyrogram.file_id')
    file_id.FILE_REFERENCE_FLAG = 1
    file_id.PHOTO_TYPES = set()
    file_id.WEB_LOCATION_FLAG = 2
    file_id.FileType = FileType
    file_id.FileId = type('FileId', (Dummy,), {})
    file_id.ThumbnailSource = type('ThumbnailSource', (Dummy,), {})
    file_id.b64_decode = lambda value: b'\0' * 12
    file_id.rle_decode = lambda value: value

    raw = DummyModule('pyrogram.raw')
    raw.types = DummyModule('pyrogram.raw.types')
    raw.functions = DummyModule('pyrogram.raw.functions')
    raw.functions.messages = DummyModule('pyrogram.raw.functions.messages')
    raw.core = DummyModule('pyrogram.raw.core')
    raw.core.TLObject = type('TLObject', (Dummy,), {})
    utils = DummyModule('pyrogram.utils')
    utils.parse_text_entities = lambda *args, **kwargs: {}
    utils.get_channel_id = lambda value: int(f'-100{value}')
    pyrogram.raw = raw
    pyrogram.utils = utils

    crypto = DummyModule('pyrogram.crypto')
    crypto.aes = DummyModule('pyrogram.crypto.aes')
    crypto.mtproto = DummyModule('pyrogram.crypto.mtproto')
    qrlogin = DummyModule('pyrogram.qrlogin')
    qrlogin.QRLogin = type('QRLogin', (Dummy,), {})
    session = DummyModule('pyrogram.session')
    session.Auth = type('Auth', (Dummy,), {})
    session.Session = type('Session', (Dummy,), {})
    session_session = DummyModule('pyrogram.session.session')
    session_session.Result = type('Result', (Dummy,), {})

    sys.modules['pyrogram'] = pyrogram
    sys.modules['pyrogram.types'] = pyrogram_types
    sys.modules['pyrogram.types.messages_and_media'] = messages_and_media
    sys.modules['pyrogram.types.bots_and_keyboards'] = bots_and_keyboards
    sys.modules['pyrogram.enums'] = enums
    sys.modules['pyrogram.enums.parse_mode'] = parse_mode
    sys.modules['pyrogram.errors'] = errors
    sys.modules['pyrogram.errors.exceptions'] = exceptions
    sys.modules['pyrogram.errors.exceptions.bad_request_400'] = bad_request
    sys.modules['pyrogram.errors.exceptions.not_acceptable_406'] = not_acceptable
    sys.modules['pyrogram.errors.exceptions.unauthorized_401'] = unauthorized
    sys.modules['pyrogram.errors.exceptions.forbidden_403'] = forbidden
    sys.modules['pyrogram.handlers'] = handlers
    sys.modules['pyrogram.file_id'] = file_id
    sys.modules['pyrogram.raw'] = raw
    sys.modules['pyrogram.raw.types'] = raw.types
    sys.modules['pyrogram.raw.functions'] = raw.functions
    sys.modules['pyrogram.raw.functions.messages'] = raw.functions.messages
    sys.modules['pyrogram.raw.core'] = raw.core
    sys.modules['pyrogram.utils'] = utils
    sys.modules['pyrogram.crypto'] = crypto
    sys.modules['pyrogram.crypto.aes'] = crypto.aes
    sys.modules['pyrogram.crypto.mtproto'] = crypto.mtproto
    sys.modules['pyrogram.qrlogin'] = qrlogin
    sys.modules['pyrogram.session'] = session
    sys.modules['pyrogram.session.session'] = session_session

    pymediainfo = DummyModule('pymediainfo')
    pymediainfo.MediaInfo = type('MediaInfo', (Dummy,), {'parse': staticmethod(lambda *args, **kwargs: Dummy())})
    sys.modules['pymediainfo'] = pymediainfo

    qrcode = DummyModule('qrcode')
    qrcode.QRCode = type(
        'QRCode',
        (Dummy,),
        {
            'add_data': lambda self, *args, **kwargs: None,
            'make': lambda self, *args, **kwargs: None,
            'modules': []
        }
    )
    qrcode.constants = Dummy()
    sys.modules['qrcode'] = qrcode
