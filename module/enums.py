# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/7/2 0:59
# File:enums.py
import os
import re
import sys
import time
import ipaddress
import platform

from functools import wraps
from dataclasses import dataclass
from typing import Union, Optional, Callable, Any

from module import console, log
from module.language import _t


class LinkType:
    SINGLE: str = 'single'
    GROUP: str = 'group'
    COMMENT: str = 'comment'
    TOPIC: str = 'topic'


@dataclass
class Link:
    # https://github.com/tangyoha/telegram_media_downloader/blob/master/utils/format.py#L14
    group_id: Union[str, int, None] = None
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    topic_id: Optional[int] = None


class DownloadType:
    VIDEO: str = 'video'
    PHOTO: str = 'photo'
    DOCUMENT: str = 'document'
    AUDIO: str = 'audio'
    VOICE: str = 'voice'
    ANIMATION: str = 'animation'
    VIDEO_NOTE: str = 'video_note'

    def __iter__(self):
        for key, value in vars(self.__class__).items():
            if not key.startswith('_') and not callable(value):  # 排除特殊方法和属性。
                yield value


class DownloadStatus:
    DOWNLOADING = 'downloading'
    SUCCESS = 'success'
    FAILURE = 'failure'
    SKIP = 'skip'
    RETRY = 'retry'


class UploadStatus:
    PENDING = 'pending'
    UPLOADING = 'uploading'
    SUCCESS = 'success'
    FAILURE = 'failure'
    SENT = 'sent'


class MODE:
    SESSION: str = 'SESSION'
    ONCE: str = 'ONCE'


class CalenderKeyboard:
    START_TIME_BUTTON: str = 'start time button'
    END_TIME_BUTTON: str = 'end time button'


class SaveDirectoryPrefix:
    CHAT_ID: str = '%CHAT_ID%'
    CHAT_NAME: str = '%CHAT_NAME%'
    MIME_TYPE: str = '%MIME_TYPE%'

    def __iter__(self):
        for key, value in vars(self.__class__).items():
            if not key.startswith('_') and not callable(value):  # 排除特殊方法和属性。
                yield value


class WebMeta:
    IP: str = 'IP'
    PORT: str = 'port'
    USERNAME: str = 'username'
    PASSWORD: str = 'password'


class ENVIRON:
    TRMD_WEB_PID: str = 'TRMD_WEB_PID'
    TRMD_WEB_PORT: str = 'TRMD_WEB_PORT'
    TRMD_WEB_HOST: str = 'TRMD_WEB_HOST'
    TRMD_WEB_USERNAME: str = 'TRMD_WEB_USERNAME'
    TRMD_WEB_PASSWORD: str = 'TRMD_WEB_PASSWORD'
    PSMUX_SESSION_NAME: str = 'PSMUX_SESSION_NAME'  # Windows专属。


class KeyWord:
    LINK: str = 'link'
    LINK_TYPE: str = 'link type'
    SIZE: str = 'size'
    STATUS: str = 'status'
    FILE: str = 'file'
    ERROR_SIZE: str = 'error size'
    ACTUAL_SIZE: str = 'actual size'
    ALREADY_EXIST: str = 'already exist'
    CHANNEL: str = 'channel'
    MESSAGE_ID: str = 'message id'
    TYPE: str = 'type'
    RE_DOWNLOAD: str = 're-download'
    RE_UPLOAD: str = 're-upload'
    RETRY_TIMES: str = 'retry times'
    CURRENT_DOWNLOAD_TASK: str = 'current download task'
    CURRENT_UPLOAD_TASK: str = 'current upload task'
    REASON: str = 'reason'
    RESUME: str = 'resume'
    DOWNLOAD_TASK: str = 'download task'
    UPLOAD_TASK: str = 'upload task'
    DOWNLOAD_AND_UPLOAD_TASK: str = 'download and upload task'
    FORWARD_SUCCESS: str = 'forward success'
    FORWARD_FAILURE: str = 'forward failure'
    FORWARD_SKIP: str = 'skip forward'
    UPLOAD_FILE_PART: str = 'upload file part'


class Extension:
    PHOTO = {
        'image/avif': 'avif',
        'image/bmp': 'bmp',
        'image/gif': 'gif',
        'image/ief': 'ief',
        'image/jpg': 'jpg',
        'image/jpeg': 'jpeg',
        'image/heic': 'heic',
        'image/heif': 'heif',
        'image/png': 'png',
        'image/svg+xml': 'svg',
        'image/tiff': 'tif',
        'image/vnd.microsoft.icon': 'ico',
        'image/x-cmu-raster': 'ras',
        'image/x-portable-anymap': 'pnm',
        'image/x-portable-bitmap': 'pbm',
        'image/x-portable-graymap': 'pgm',
        'image/x-portable-pixmap': 'ppm',
        'image/x-rgb': 'rgb',
        'image/x-xbitmap': 'xbm',
        'image/x-xpixmap': 'xpm',
        'image/x-xwindowdump': 'xwd'
    }
    VIDEO = {
        'video/mp4': 'mp4',
        'video/mpeg': 'mpg',
        'video/quicktime': 'qt',
        'video/webm': 'webm',
        'video/x-msvideo': 'avi',
        'video/x-sgi-movie': 'movie',
        'video/x-matroska': 'mkv'
    }
    REVERSE_PHOTO = {
        'avif': 'image/avif',
        'bmp': 'image/bmp',
        'gif': 'image/gif',
        'ief': 'image/ief',
        'jpg': 'image/jpg',
        'jpeg': 'image/jpeg',
        'heic': 'image/heic',
        'heif': 'image/heif',
        'png': 'image/png',
        'svg': 'image/svg+xml',
        'tif': 'image/tiff',
        'ico': 'image/vnd.microsoft.icon',
        'ras': 'image/x-cmu-raster',
        'pnm': 'image/x-portable-anymap',
        'pbm': 'image/x-portable-bitmap',
        'pgm': 'image/x-portable-graymap',
        'ppm': 'image/x-portable-pixmap',
        'rgb': 'image/x-rgb',
        'xbm': 'image/x-xbitmap',
        'xpm': 'image/x-xpixmap',
        'xwd': 'image/x-xwindowdump'
    }
    REVERSE_VIDEO = {
        'mp4': 'video/mp4',
        'mpg': 'video/mpeg',
        'qt': 'video/quicktime',
        'webm': 'video/webm',
        'avi': 'video/x-msvideo',
        'movie': 'video/x-sgi-movie',
        'mkv': 'video/x-matroska'
    }
    ALL_REVERSE = {
        'avif': 'image/avif',
        'bmp': 'image/bmp',
        'gif': 'image/gif',
        'ief': 'image/ief',
        'jpg': 'image/jpg',
        'jpeg': 'image/jpeg',
        'heic': 'image/heic',
        'heif': 'image/heif',
        'png': 'image/png',
        'svg': 'image/svg+xml',
        'tif': 'image/tiff',
        'ico': 'image/vnd.microsoft.icon',
        'ras': 'image/x-cmu-raster',
        'pnm': 'image/x-portable-anymap',
        'pbm': 'image/x-portable-bitmap',
        'pgm': 'image/x-portable-graymap',
        'ppm': 'image/x-portable-pixmap',
        'rgb': 'image/x-rgb',
        'xbm': 'image/x-xbitmap',
        'xpm': 'image/x-xpixmap',
        'xwd': 'image/x-xwindowdump',
        'video/mp4': 'mp4',
        'video/mpeg': 'mpg',
        'video/quicktime': 'qt',
        'video/webm': 'webm',
        'video/x-msvideo': 'avi',
        'video/x-sgi-movie': 'movie',
        'video/x-matroska': 'mkv'
    }


class GradientColor:
    # 生成渐变色:https://photokit.com/colors/color-gradient/?lang=zh
    BLUE2PURPLE_14 = [
        '#0ebeff',
        '#21b4f9',
        '#33abf3',
        '#46a1ed',
        '#5898e8',
        '#6b8ee2',
        '#7d85dc',
        '#907bd6',
        '#a272d0',
        '#b568ca',
        '#c75fc5',
        '#da55bf',
        '#ec4cb9',
        '#ff42b3'
    ]
    GREEN2PINK_11 = [
        '#00ff40',
        '#14f54c',
        '#29eb58',
        '#3de064',
        '#52d670',
        '#66cc7c',
        '#7ac288',
        '#8fb894',
        '#a3ada0',
        '#b8a3ac',
        '#cc99b8'
    ]
    GREEN2BLUE_10 = [
        '#84fab0',
        '#85f6b8',
        '#86f1bf',
        '#88edc7',
        '#89e9ce',
        '#8ae4d6',
        '#8be0dd',
        '#8ddce5',
        '#8ed7ec',
        '#8fd3f4'
    ]
    YELLOW2GREEN_10 = [
        '#d4fc79',
        '#cdfa7d',
        '#c6f782',
        '#bff586',
        '#b8f28b',
        '#b2f08f',
        '#abed94',
        '#a4eb98',
        '#9de89d',
        '#96e6a1'
    ]
    ORANGE2YELLOW_15 = [
        '#f08a5d',
        '#f1915e',
        '#f1985f',
        '#f29f60',
        '#f3a660',
        '#f3ad61',
        '#f4b462',
        '#f5bc63',
        '#f5c364',
        '#f6ca65',
        '#f6d166',
        '#f7d866',
        '#f8df67',
        '#f8e668',
        '#f9ed69'
    ]
    NEW_LIFE = [
        '#43e97b',
        '#42eb85',
        '#41ed8f',
        '#3fee9a',
        '#3ef0a4',
        '#3df2ae',
        '#3cf4b8',
        '#3af5c3',
        '#39f7cd',
        '#38f9d7'
    ]
    RED_GRADIENT_15 = [
        '#ff0000',
        '#ff0011',
        '#ff0021',
        '#ff0032',
        '#ff0043',
        '#ff0053',
        '#ff0064',
        '#ff0075',
        '#ff0085',
        '#ff0096',
        '#ff1a9e',
        '#ff33a6',
        '#ff4db0',
        '#ff66b8',
        '#ff80c2'
    ]

    @staticmethod
    def __extend_gradient_colors(colors: list, target_length: int) -> list:
        extended_colors = colors[:]
        while len(extended_colors) < target_length:
            # 添加原列表（除最后一个元素外）的逆序
            extended_colors.extend(colors[-2::-1])
            # 如果仍然不够长，继续添加正序部分
            if len(extended_colors) < target_length:
                extended_colors.extend(colors[:-1])
        return extended_colors[:target_length]

    @staticmethod
    def gen_gradient_text(text: str, gradient_color: list) -> str:
        """当渐变色列表小于文字长度时,翻转并扩展当前列表。"""
        text_lst: list = [i for i in text]
        text_lst_len: int = len(text_lst)
        gradient_color_len: int = len(gradient_color)
        if text_lst_len > gradient_color_len:
            # 扩展颜色列表以适应文本长度
            gradient_color = GradientColor.__extend_gradient_colors(gradient_color, text_lst_len)
        result: str = ''
        for i in range(text_lst_len):
            result += f'[{gradient_color[i]}]{text_lst[i]}[/{gradient_color[i]}]'
        return result

    @staticmethod
    def __hex_to_rgb(hex_color: str) -> tuple:
        """将十六进制颜色值转换为RGB元组。"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def __rgb_to_hex(r: int, g: int, b: int) -> str:
        """将RGB元组转换为十六进制颜色值。"""
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def generate_gradient(start_color: str, end_color: str, steps: int) -> list:
        """根据起始和结束颜色生成颜色渐变列表。"""
        steps = 2 if steps <= 1 else steps
        # 转换起始和结束颜色为RGB
        start_rgb = GradientColor.__hex_to_rgb(start_color)
        end_rgb = GradientColor.__hex_to_rgb(end_color)
        # 生成渐变色列表
        gradient_color: list = []
        for i in range(steps):
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i / (steps - 1))
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i / (steps - 1))
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i / (steps - 1))
            gradient_color.append(GradientColor.__rgb_to_hex(r, g, b))

        return gradient_color


class Banner:
    A = r'''
       ______           __  __                     _ __          
      / ____/__  ____  / /_/ /__  _________  _____(_) /____      
     / / __/ _ \/ __ \/ __/ / _ \/ ___/ __ \/ ___/ / __/ _ \     
    / /_/ /  __/ / / / /_/ /  __(__  ) /_/ / /  / / /_/  __/     
    \____/\___/_/ /_/\__/_/\___/____/ .___/_/  /_/\__/\___/      
                                   /_/                           
        '''
    B = r'''
    ╔═╗┌─┐┌┐┌┌┬┐┬  ┌─┐┌─┐┌─┐┬─┐┬┌┬┐┌─┐  
    ║ ╦├┤ │││ │ │  ├┤ └─┐├─┘├┬┘│ │ ├┤   
    ╚═╝└─┘┘└┘ ┴ ┴─┘└─┘└─┘┴  ┴└─┴ ┴ └─┘  
        '''
    C = r'''
     ██████╗ ███████╗███╗   ██╗████████╗██╗     ███████╗███████╗██████╗ ██████╗ ██╗████████╗███████╗    
    ██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██║     ██╔════╝██╔════╝██╔══██╗██╔══██╗██║╚══██╔══╝██╔════╝    
    ██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║     █████╗  ███████╗██████╔╝██████╔╝██║   ██║   █████╗      
    ██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║     ██╔══╝  ╚════██║██╔═══╝ ██╔══██╗██║   ██║   ██╔══╝      
    ╚██████╔╝███████╗██║ ╚████║   ██║   ███████╗███████╗███████║██║     ██║  ██║██║   ██║   ███████╗    
     ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝   ╚══════╝           
            '''
    D = r'''                                                                          
                                            ,,                                       ,,                    
      .g8"""bgd                      mm   `7MM                                       db   mm               
    .dP'     `M                      MM     MM                                            MM               
    dM'       `   .gP"Ya `7MMpMMMb.mmMMmm   MM  .gP"Ya  ,pP"Ybd `7MMpdMAo.`7Mb,od8 `7MM mmMMmm .gP"Ya      
    MM           ,M'   Yb  MM    MM  MM     MM ,M'   Yb 8I   `"   MM   `Wb  MM' "'   MM   MM  ,M'   Yb     
    MM.    `7MMF'8M""""""  MM    MM  MM     MM 8M"""""" `YMMMa.   MM    M8  MM       MM   MM  8M""""""     
    `Mb.     MM  YM.    ,  MM    MM  MM     MM YM.    , L.   I8   MM   ,AP  MM       MM   MM  YM.    ,     
      `"bmmmdPY   `Mbmmd'.JMML  JMML.`Mbmo.JMML.`Mbmmd' M9mmmP'   MMbmmd' .JMML.   .JMML. `Mbmo`Mbmmd'     
                                                                  MM                                       
                                                                .JMML.                                     
        '''
    TRMD = r'''
    ████████╗██████╗ ███╗   ███╗██████╗ 
    ╚══██╔══╝██╔══██╗████╗ ████║██╔══██╗
       ██║   ██████╔╝██╔████╔██║██║  ██║
       ██║   ██╔══██╗██║╚██╔╝██║██║  ██║
       ██║   ██║  ██║██║ ╚═╝ ██║██████╔╝
       ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝
    '''


class Validator:

    @staticmethod
    def is_contain_chinese(text: str) -> bool:
        for ch in text:
            if u'\u4e00' <= ch <= u'\u9fff':
                log.warning('如果无法正常下载,请尝试不使用中文路径后重试。')
                return True
        return False

    @staticmethod
    def is_valid_api_id(api_id: str, valid_length: int = 32) -> bool:
        try:
            if len(api_id) < valid_length:
                if api_id.isdigit():
                    return True
                else:
                    log.warning(f'意外的参数:"{api_id}",不是「纯数字」请重新输入!')
                    return False
            else:
                log.warning(f'意外的参数,填写的"{api_id}"可能是「api_hash」,请填入正确的「api_id」!')
                return False
        except (AttributeError, TypeError):
            log.error('手动编辑config.yaml时,api_id需要有引号!')
            return False

    @staticmethod
    def is_valid_api_hash(api_hash: str, valid_length: int = 32) -> bool:
        return len(str(api_hash)) == valid_length

    @staticmethod
    def is_valid_bot_token(bot_token: str, valid_format: str = ':') -> bool:
        if valid_format in bot_token:
            p = bot_token.split(valid_format)
            if len(p) == 2 and all(p):
                return True
        return False

    @staticmethod
    def is_valid_links_file(file_path: str, valid_format: str = '.txt') -> bool:
        file_path = os.path.normpath(file_path)
        return os.path.isfile(file_path) and file_path.endswith(valid_format)

    @staticmethod
    def is_valid_save_directory(save_directory: str) -> bool:
        for placeholder in SaveDirectoryPrefix():
            if placeholder in save_directory:
                save_directory = save_directory.replace(placeholder, '')
        save_directory = os.path.normpath(save_directory)
        if not os.path.exists(save_directory):
            while True:
                try:
                    question = console.input(f'目录:"{save_directory}"不存在,是否创建? - 「y|n」(默认y):').strip().lower()
                    if question in ('y', ''):
                        os.makedirs(save_directory, exist_ok=True)
                        console.log(f'成功创建目录:"{save_directory}"')
                        break
                    elif question == 'n':
                        break
                    else:
                        log.warning(f'意外的参数:"{question}",支持的参数 - 「y|n」')
                except Exception as e:
                    log.error(f'意外的错误,原因:"{e}"')
                    break
        return os.path.isdir(save_directory)

    @staticmethod
    def is_valid_number(max_tasks: int) -> bool:
        try:
            return int(max_tasks) > 0
        except ValueError:
            return False
        except Exception as e:
            log.error(f'意外的错误,原因:"{e}"')
            return False

    @staticmethod
    def is_valid_enable_proxy(enable_proxy: Union[str, bool]) -> bool:
        if enable_proxy in ('y', 'n'):
            return True
        return False

    @staticmethod
    def is_valid_scheme(scheme: str, valid_format: list) -> bool:
        return scheme in valid_format

    @staticmethod
    def is_valid_hostname(hostname: str) -> bool:
        return isinstance(ipaddress.ip_address(hostname), ipaddress.IPv4Address)

    @staticmethod
    def is_valid_port(port: int) -> bool:
        try:
            return 0 < int(port) <= 65535
        except ValueError:  # 处理非整数字符串的情况
            return False
        except TypeError:  # 处理传入非数字类型的情况
            return False
        except Exception as e:
            log.error(f'意外的错误,原因:"{e}"')
            return False

    @staticmethod
    def is_valid_download_type(dtype: list) -> bool:
        try:
            if isinstance(dtype, list):
                support_dtype: list = [_ for _ in DownloadType()]
                valid_dtype = []
                for i in dtype:
                    if i in support_dtype:
                        valid_dtype.append(i)
                    else:
                        log.warning(f'"{i}"不在支持的下载类型中,已移除。')
                dtype[:] = valid_dtype
                return bool(dtype)
            return False
        except Exception as e:
            log.error(f'意外的错误,原因:"{e}"')
            return False


class ProcessConfig:
    PROXY_AUTO_FILL = False

    @staticmethod
    def __parse_proxy_url(proxy_url: str) -> Optional[dict]:
        """解析代理URL字符串。"""
        try:
            if not proxy_url:
                return None

            # 正则表达式匹配代理URL，支持以下格式：
            # - http://username:password@host:port
            # - https://host:port
            # - socks4://host:port
            # - socks5://host:port
            # - host:port (无协议前缀)
            # - 支持URL末尾有/的情况，如 http://127.0.0.1:10808/
            pattern = r'^(?:(https?|socks[45][ah]?)://)?(?:[^@]*@)?([^:]+):(\d+)/+$'
            match = re.match(pattern, proxy_url.lower())

            if not match:
                return None

            scheme = match.group(1)
            hostname = match.group(2)
            port = match.group(3)

            # 如果没有scheme，默认为http。
            if not scheme:
                scheme = 'http'
            # socks4a和socks5h统一为socks4和socks5。
            elif scheme in ('socks4a', 'socks5h'):
                scheme = scheme[:-1]

            # 验证端口号有效性。
            try:
                port = int(port)
            except ValueError:
                return None

            if not (0 <= port <= 65535):
                return None

            return {
                'scheme': scheme,
                'hostname': hostname,
                'port': port
            }
        except Exception:
            return None

    @staticmethod
    def format_proxy_prompt(proxy: dict) -> str:
        return proxy.get('scheme', '') + '://' + proxy.get('hostname', '') + ':' + str(proxy.get('port', ''))

    @staticmethod
    def get_unix_proxy() -> Optional[dict]:
        """从环境变量获取 Unix/Linux/macOS 代理设置。"""
        env_vars = ['http_proxy', 'HTTP_PROXY', 'https_proxy', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']

        for var in env_vars:
            proxy_url = os.environ.get(var)
            if proxy_url:
                proxy_info = ProcessConfig.__parse_proxy_url(proxy_url)
                if proxy_info:
                    return proxy_info

        return None

    @staticmethod
    def get_windows_proxy() -> Optional[dict]:
        """从 Windows 注册表获取代理设置。"""
        try:
            import winreg
            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
            ) as key:
                proxy_enable, _ = winreg.QueryValueEx(key, 'ProxyEnable')
                if not proxy_enable:
                    return None

                proxy_server, _ = winreg.QueryValueEx(key, 'ProxyServer')
                if not proxy_server:
                    return None

                # 使用正则表达式解析代理服务器字符串。
                # 格式可能是: "http=127.0.0.1:7890;https=127.0.0.1:7890;socks=127.0.0.1:1080"。
                # 或者是: "127.0.0.1:7890"。
                proxy_info = {}
                pattern = r'(\w+)=([^;]+)'
                matches = re.findall(pattern, proxy_server)

                if matches:
                    for proto, addr in matches:
                        proxy_info[proto.lower()] = addr
                else:
                    # 如果没有协议前缀，则整个字符串就是代理地址。
                    proxy_info['http'] = proxy_server

                # 优先级：http > https > socks。
                proxy_addr = proxy_info.get('http') or proxy_info.get('https') or proxy_info.get('socks')

                if not proxy_addr:
                    return None

                # 使用正则表达式解析地址和端口。
                addr_pattern = r'^([^:]+):(\d+)$'
                addr_match = re.match(addr_pattern, proxy_addr)

                if not addr_match:
                    return None

                hostname = addr_match.group(1)
                try:
                    port = int(addr_match.group(2))
                except ValueError:
                    return None

                # 判断协议类型。
                scheme = 'http'
                if 'socks5' in proxy_server.lower():
                    scheme = 'socks5'
                elif 'socks4' in proxy_server.lower():
                    scheme = 'socks4'
                elif 'socks=' in proxy_server.lower():
                    # 如果只有socks=没有数字，默认socks5
                    scheme = 'socks5'

                if not (0 <= port <= 65535):
                    return None

                return {
                    'scheme': scheme,
                    'hostname': hostname,
                    'port': port
                }

        except (WindowsError, OSError, ValueError):
            return None

    @staticmethod
    def get_system_proxy(param_name: str):

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # 尝试获取系统代理（跨平台）。
                system_proxy = ProcessConfig.get_windows_proxy() if platform.system() == 'Windows' else ProcessConfig.get_unix_proxy()
                # 如果成功获取到系统代理并且包含所需的参数。
                if system_proxy and param_name in system_proxy:
                    question: str = GetStdioParams.UNDEFINED
                    if param_name == 'scheme' and ProcessConfig.PROXY_AUTO_FILL is False:
                        while True:
                            try:
                                question = console.input(
                                    f'获取到系统代理"{ProcessConfig.format_proxy_prompt(system_proxy)}",是否自动填入? - 「y|n」(默认y):').strip().lower()
                                if question in ('y', ''):
                                    ProcessConfig.PROXY_AUTO_FILL = True
                                    break
                                elif question == 'n':
                                    break
                                else:
                                    log.warning(f'意外的参数:"{question}",支持的参数 - 「y|n」')
                            except Exception as e:
                                log.error(f'意外的错误,原因:"{e}"')
                                break
                    if question in ('y', '') or ProcessConfig.PROXY_AUTO_FILL:
                        # 提取对应参数的值。
                        value = system_proxy[param_name]
                        # 根据参数类型打印相应的提示信息。
                        if param_name == 'scheme':
                            console.print(
                                f'已从系统代理自动获取「scheme」为:「{value}」',
                                style=ProcessConfig.stdio_style('scheme')
                            )
                            return {
                                'scheme': value,
                                'record_flag': True
                            }
                        elif param_name == 'hostname':
                            console.print(
                                f'已从系统代理自动获取「hostname」为:「{value}」',
                                style=ProcessConfig.stdio_style('hostname')
                            )
                            return {
                                'hostname': value,
                                'record_flag': True
                            }
                        elif param_name == 'port':
                            console.print(
                                f'已从系统代理自动获取「port」为:「{value}」',
                                style=ProcessConfig.stdio_style('port')
                            )
                            return {
                                'port': value,
                                'record_flag': True
                            }

                # 如果没有获取到系统代理或参数不完整，执行原函数。
                return func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def set_dtype(_dtype: list) -> list:
        record_dtype: list = []
        support_dtype: list = [_ for _ in DownloadType()]
        for i in _dtype:
            if i in support_dtype:
                record_dtype.append(i)
        return record_dtype

    @staticmethod
    def get_dtype(download_dtype: list) -> dict:
        """获取所需下载文件的类型。"""
        meta: dict = {}
        support_dtype: list = [_ for _ in DownloadType()]
        for dtype in download_dtype:
            meta[dtype] = True if dtype in support_dtype else False
        return meta

    @staticmethod
    def stdio_style(key: str, color=None) -> str:
        """控制用户交互时打印出不同的颜色(渐变)。"""
        if color is None:
            color = GradientColor.ORANGE2YELLOW_15
        _stdio_queue: dict = {
            'api_id': 0,
            'api_hash': 1,
            'bot_token': 2,
            'links': 3,
            'save_directory': 4,
            'max_download_task': 5,
            'max_retry_count': 6,
            'download_type': 7,
            'is_shutdown': 8,
            'enable_proxy': 9,
            'config_proxy': 10,
            'scheme': 11,
            'hostname': 12,
            'port': 13,
            'proxy_authentication': 14
        }
        return color[_stdio_queue.get(key)]

    @staticmethod
    def is_proxy_input(proxy_config: dict) -> bool:
        """检测代理配置是否需要用户输入。"""
        result: bool = False
        basic_truth_table: list = []
        advance_account_truth_table: list = []
        if proxy_config.get('enable_proxy') is False:  # 检测打开了代理但是代理配置错误。
            return False
        for _ in proxy_config.items():
            if _[0] in ['scheme', 'port', 'hostname']:
                basic_truth_table.append(_[1])
            if _[0] in ['username', 'password']:
                advance_account_truth_table.append(_[1])
        if all(basic_truth_table) is False:
            console.print('请配置代理!', style=ProcessConfig.stdio_style('config_proxy'))
            console.print(
                '[#79FCD4]如果对代理配置有疑问[/#79FCD4][#FF79D4]请访问:[/#FF79D4]\n'
                '[link=https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/wiki#配置代理时在代理在本机的情况下]'
                'https://github.com/Gentlesprite/Telegram_Restricted_Media_Downloader/wiki#配置代理时在代理在本机的情况下[/link]'
                '\n[#FCFF79]若[/#FCFF79][#FF4689]无法[/#FF4689][#FF7979]访问[/#FF7979][#79FCD4],[/#79FCD4]'
                '[#FCFF79]可[/#FCFF79][#d4fc79]查阅[/#d4fc79]'
                '[#FC79A5]软件压缩包所提供的[/#FC79A5][#79E2FC]"使用手册"[/#79E2FC]'
                '[#79FCD4]文件夹下的[/#79FCD4][#FFB579]"常见问题及解决方案汇总.pdf"[/#FFB579]'
                '[#79FCB5]中的[/#79FCB5][#D479FC]【问题14】里的【解决方案】[/#D479FC][#FCE679]进行操作[/#FCE679][#FC79A6]。[/#FC79A6]'
            )
            result: bool = True
        if any(advance_account_truth_table) and all(advance_account_truth_table) is False:
            log.warning('代理账号或密码未输入!')
            result: bool = True
        return result

    @staticmethod
    def get_proxy_info(proxy_config: dict) -> dict:
        return {
            'scheme': proxy_config.get('scheme', '未知'),
            'hostname': proxy_config.get('hostname', '未知'),
            'port': proxy_config.get('port', '未知')
        }


class GetStdioParams:
    UNDEFINED: str = '无'

    @staticmethod
    def __timeout_input(
            prompt: str = '',
            error_prompt: Union[str, None] = None,
            default: str = '',
            timeout: int = 5
    ) -> str:
        """跨平台的输入超时后自动设置为默认值,报错时返回默认input。"""

        def timeout_notice():
            console.print('\n输入超时,已自动设置为默认值。\n', style='#FF4689')

        if sys.platform == 'win32':
            try:
                import msvcrt
                console.print(prompt, end='')
                start_time: float = time.time()
                input_buffer: list = []
                last_second: int = timeout
                countdown_displayed: bool = False

                while True:
                    elapsed = time.time() - start_time
                    remaining = int(timeout - elapsed)

                    # 倒计时显示更新。
                    if remaining != last_second and remaining >= 0:
                        if countdown_displayed:
                            # 删除之前的倒计时（1位数字+1个空格）。
                            print('\b \b\b \b', end='', flush=True)
                        # 显示新的倒计时（输入时才显示）。
                        if not input_buffer and remaining >= 0:
                            console.print(f'{remaining} ', end='', style='dim')
                            countdown_displayed = True
                        last_second = remaining

                    if msvcrt.kbhit():  # 检测是否有键盘输入。
                        # 清除倒计时显示。
                        if countdown_displayed:
                            print('\b \b\b \b', end='', flush=True)
                            countdown_displayed = False

                        char = msvcrt.getwch()
                        if char == '\r':  # 回车键结束输入。
                            user_input = ''.join(input_buffer)
                            print('\n') if user_input in ('y', 'n', '') else None
                            return user_input.strip() or default
                        elif char in ('\x08', '\b'):  # Backspace键处理。
                            if input_buffer:
                                input_buffer.pop()
                                print('\b \b', end='', flush=True)  # 删除控制台上的最后一个字符。
                        elif char in ('\x00', '\xe0'):  # 上下左右键。
                            _ = msvcrt.getwch()
                        else:
                            input_buffer.append(char)
                            console.print(char, end='')
                        last_second = -1  # 输入开始后不再显示倒计时。
                    elif elapsed > timeout:
                        timeout_notice()
                        return default
                    time.sleep(0.1)
            except Exception as e:
                log.exception(f'无法自动设置!请手动进行设置,{_t(KeyWord.REASON)}:"{e}"')
                return console.input(error_prompt if error_prompt else prompt)
        else:
            import tty
            import select
            import termios

            console.print(prompt, end='')
            sys.stdout.flush()

            # 保存原始终端设置。
            old_settings = termios.tcgetattr(sys.stdin)
            elapsed = 0
            try:
                # 设置终端为原始模式,允许逐字符读取。
                tty.setraw(sys.stdin.fileno())

                start_time: float = time.time()
                input_buffer: list = []
                last_second: int = timeout
                countdown_displayed: bool = False
                while True:
                    elapsed = time.time() - start_time
                    remaining = int(timeout - elapsed)

                    # 倒计时显示更新。
                    if remaining != last_second and remaining >= 0:
                        if countdown_displayed:
                            # 删除之前的倒计时（数字+空格）。
                            backspace_count = len(str(last_second)) + 1
                            sys.stdout.write('\b \b' * backspace_count)
                            sys.stdout.flush()
                        # 显示新的倒计时（输入时才显示）。
                        if not input_buffer and remaining >= 0:
                            console.print(f'{remaining} ', end='', style='dim')
                            sys.stdout.flush()
                            countdown_displayed = True
                        last_second = remaining

                    # 使用select检测输入,超时0.1秒以便更新倒计时。
                    ready, _, _ = select.select([sys.stdin], [], [], 0.1)

                    if ready:
                        # 清除倒计时显示。
                        if countdown_displayed:
                            backspace_count = len(str(remaining)) + 1
                            sys.stdout.write('\b \b' * backspace_count)
                            sys.stdout.flush()
                            countdown_displayed = False

                        # 读取一个字符。
                        char = sys.stdin.read(1)

                        if char == '\r' or char == '\n':  # 回车键结束输入。
                            user_input = ''.join(input_buffer)
                            sys.stdout.write('\n')
                            sys.stdout.flush()
                            return user_input.strip() or default
                        elif char == '\x7f' or char == '\b':  # Backspace/Delete键处理。
                            if input_buffer:
                                input_buffer.pop()
                                sys.stdout.write('\b \b')
                                sys.stdout.flush()
                        elif char == '\x1b':  # 转义序列（上下左右键等）。
                            # 读取接下来的两个字符。
                            _ = sys.stdin.read(2)
                        elif ord(char) >= 32:  # 可打印字符。
                            input_buffer.append(char)
                            sys.stdout.write(char)
                            sys.stdout.flush()
                        last_second = -1  # 输入开始后不再显示倒计时。

                    elif elapsed > timeout:
                        # 清除倒计时显示。
                        if countdown_displayed:
                            backspace_count = len(str(remaining)) + 1
                            sys.stdout.write('\b \b' * backspace_count)
                            sys.stdout.flush()
                        return default
            except Exception as e:
                log.exception(f'无法自动设置!请手动进行设置,{_t(KeyWord.REASON)}:"{e}"')
                return console.input(error_prompt if error_prompt else prompt)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)  # 恢复终端设置。
                timeout_notice() if elapsed > timeout else print()

    @staticmethod
    def get_is_ki_save_config(valid_format: str = 'y|n') -> dict:
        while True:
            is_save_config: str = console.input(
                f'「退出提示」是否需要保存当前已填写的参数? - 「{valid_format}」:').strip().lower()
            if is_save_config == 'y':
                return {'is_ki_save_config': True}
            elif is_save_config == 'n':
                return {'is_ki_save_config': False}
            else:
                log.warning(f'意外的参数:"{is_save_config}",支持的参数 - 「{valid_format}」')

    @staticmethod
    def get_is_re_config(valid_format: str = 'y|n') -> dict:
        prompt: str = f'检测到已配置完成的配置文件,是否需要重新配置?(配置文件将自动备份) - 「{valid_format}」'
        timeout: int = 5
        while True:
            is_re_config: str = GetStdioParams.__timeout_input(
                prompt=f'{prompt}:',
                error_prompt=f'{prompt}(默认n):',
                default='n',
                timeout=timeout
            ).strip().lower()
            if is_re_config == 'y':
                return {'is_re_config': True}
            elif is_re_config in ('n', ''):
                return {'is_re_config': False}
            else:
                console.print('\n') if sys.platform == 'win32' else None
                log.warning(f'意外的参数:"{is_re_config}",支持的参数 - 「{valid_format}」(默认n)')

    @staticmethod
    def get_is_change_account(valid_format: str = 'y|n') -> dict:
        style: str = '#FF4689'
        while True:
            is_change_account = console.input(
                '是否需要切换账号? - 「y|n」(默认n):').strip().lower()
            if is_change_account in ('n', ''):
                console.print('用户不需要切换「账号」。', style=style)
                return {'is_change_account': False}
            elif is_change_account == 'y':
                console.print('用户需要切换「账号」。', style=style)
                return {'is_change_account': True}
            else:
                log.warning(f'意外的参数:"{is_change_account}",支持的参数 - 「{valid_format}」!')

    @staticmethod
    def get_session_directory():
        style: str = '#FF4689'
        while True:
            session_directory = console.input(
                '请输入「会话文件目录」(可为「空目录」,也可为「已登录的会话文件目录」):').strip()
            console.print(f'「会话文件夹的路径」设置为:{session_directory}。', style=style)
            return {'session_directory': session_directory}

    @staticmethod
    def get_api_id(last_record: str) -> dict:
        while True:
            api_id = console.input(
                f'请输入「api_id」上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」:').strip()
            if api_id == '' and last_record is not None:
                api_id = last_record
            if Validator.is_valid_api_id(api_id):
                console.print(f'已设置「api_id」为:「{api_id}」', style=ProcessConfig.stdio_style('api_id'))
                return {
                    'api_id': api_id,
                    'record_flag': True
                }

    @staticmethod
    def get_api_hash(last_record: str, valid_length: int = 32) -> dict:
        while True:
            api_hash = console.input(
                f'请输入「api_hash」上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」:').strip().lower()
            if api_hash == '' and last_record is not None:
                api_hash = last_record
            if Validator.is_valid_api_hash(api_hash, valid_length):
                console.print(f'已设置「api_hash」为:「{api_hash}」', style=ProcessConfig.stdio_style('api_hash'))
                return {
                    'api_hash': api_hash,
                    'record_flag': True
                }
            else:
                log.warning(f'意外的参数:"{api_hash}",不是一个「{valid_length}位」的「值」!请重新输入!')

    @staticmethod
    def get_enable_bot(valid_format: str = 'y|n') -> dict:
        while True:
            enable_bot = console.input('是否启用「机器人」(需要提供bot_token)? - 「y|n」(默认n):').strip().lower()
            if enable_bot in ('n', ''):
                console.print(f'已设置为不启用「机器人」。', style=ProcessConfig.stdio_style('bot_token'))
                return {'enable_bot': False}
            elif enable_bot == 'y':
                console.print(f'请配置「bot_token」。', style=ProcessConfig.stdio_style('bot_token'))
                return {'enable_bot': True}
            else:
                log.warning(f'意外的参数:"{enable_bot}",支持的参数 - 「{valid_format}」!')

    @staticmethod
    def get_bot_token(last_record: str, valid_format: str = ':') -> dict:
        while True:
            bot_token = console.input(
                f'请输入当前账号的「bot_token」上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」:').strip()
            if bot_token == '' and last_record is not None:
                bot_token = last_record
            if Validator.is_valid_bot_token(bot_token, valid_format):
                console.print(f'已设置「bot_token」为:「{bot_token}」', style=ProcessConfig.stdio_style('bot_token'))
                return {
                    'bot_token': bot_token,
                    'record_flag': True
                }
            else:
                log.warning(f'意外的参数:"{bot_token}",「bot_token」中需要包含":",请重新输入!')

    @staticmethod
    def get_links(last_record: str, valid_format: str = '.txt', enable_bot: bool = False) -> dict:
        # 输入需要下载的媒体链接文件路径,确保文件存在。
        links_file_path = None
        while True:
            try:
                bot_notice = '(检测到已配置机器人,此步骤可忽略)' if enable_bot else ''
                links_file_path = console.input(
                    f'请输入需要下载的媒体链接的「完整路径」。上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」'
                    f'格式 - 「{valid_format}」{bot_notice}:').strip()
                if links_file_path == '':
                    if last_record is not None:
                        links_file_path = last_record
                    elif bot_notice:
                        links_file_path = os.path.join(os.getcwd(), 'links.txt')
                if links_file_path and not os.path.exists(links_file_path):
                    try:
                        with open(file=links_file_path, mode='w', encoding='UTF-8'):
                            pass
                    except Exception as e:
                        log.warning(f'无法创建文件:"{links_file_path}"请排查权限问题,{_t(KeyWord.REASON)}:"{e}"')
                if Validator.is_valid_links_file(links_file_path, valid_format):
                    console.print(f'已设置「links」为:「{links_file_path}」', style=ProcessConfig.stdio_style('links'))
                    Validator.is_contain_chinese(links_file_path)
                    return {
                        'links': links_file_path,
                        'record_flag': True
                    }
                elif not os.path.normpath(links_file_path).lower().endswith('.txt'):
                    log.warning(f'意外的参数:"{links_file_path}",文件路径必须以「{valid_format}」结尾,请重新输入!')
                else:
                    log.warning(
                        f'意外的参数:"{links_file_path}",文件「必须存在」(区分大小写),请重新输入!')
            except Exception as e:
                log.warning(
                    f'意外的参数:"{links_file_path}",文件路径必须以「{valid_format}」结尾,并且「必须存在」,请重新输入!{_t(KeyWord.REASON)}:"{e}"')

    @staticmethod
    def get_save_directory(last_record) -> dict:
        # 输入媒体保存路径,确保是一个有效的目录路径。
        while True:
            save_directory = console.input(
                f'请输入媒体「保存路径」。上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」:').strip()
            if save_directory == '':
                if last_record is not None:
                    save_directory = last_record
                else:
                    save_directory = os.path.join(os.getcwd(), 'downloads')
                    log.warning('没有上一次的记录,已设置为默认目录。')
            if Validator.is_valid_save_directory(save_directory):
                console.print(f'已设置「save_directory」为:「{save_directory}」',
                              style=ProcessConfig.stdio_style('save_directory'))
                Validator.is_contain_chinese(save_directory)
                return {
                    'save_directory': save_directory,
                    'record_flag': True
                }
            elif os.path.isfile(save_directory):
                log.warning(f'意外的参数:"{save_directory}",指定的路径是一个文件并非目录,请重新输入!')
            else:
                log.warning(f'意外的参数:"{save_directory}",指定的路径无效或不是一个目录,请重新输入!')

    @staticmethod
    def get_max_download_task(last_record) -> dict:
        # 输入最大下载任务数,确保是一个整数且不超过特定限制。
        default_prompt: str = '(默认3)' if last_record is None else ''
        while True:
            try:
                max_download_task = console.input(
                    f'请输入「最大下载任务数」。上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」'
                    f',值过高可能会导致网络相关问题,建议默认{default_prompt}:').strip()
                if max_download_task == '' and last_record is not None:
                    max_download_task = last_record
                if max_download_task == '':
                    max_download_task = 1
                if Validator.is_valid_number(max_download_task):
                    console.print(f'已设置「max_download_task」为:「{max_download_task}」',
                                  style=ProcessConfig.stdio_style('max_download_task'))
                    return {
                        'max_download_task': int(max_download_task),
                        'record_flag': True
                    }
                else:
                    log.warning(f'意外的参数:"{max_download_task}",任务数必须是「正整数」,请重新输入!')
            except Exception as e:
                log.error(f'意外的错误,{_t(KeyWord.REASON)}:"{e}"')

    @staticmethod
    def get_max_retry_count(last_record) -> dict:
        default_prompt: str = '(默认5)' if last_record is None else ''
        while True:
            try:
                max_retry_count = console.input(
                    f'请输入任务失败时「最大重试次数」。上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」{default_prompt}:').strip()
                if max_retry_count == '' and last_record is not None:
                    max_retry_count = last_record
                if max_retry_count == '':
                    max_retry_count = 5
                if Validator.is_valid_number(max_retry_count):
                    console.print(f'已设置「max_retry_count」为:「{max_retry_count}」',
                                  style=ProcessConfig.stdio_style('max_retry_count'))
                    return {
                        'max_retry_count': int(max_retry_count),
                        'record_flag': True
                    }
                else:
                    log.warning(f'意外的参数:"{max_retry_count}",最大重试次数必须是「正整数」,请重新输入!')
            except Exception as e:
                log.error(f'意外的错误,{_t(KeyWord.REASON)}:"{e}"')

    @staticmethod
    def get_download_type(last_record: Union[list, None]) -> dict:
        if isinstance(last_record, list):
            meta: dict = ProcessConfig.get_dtype(download_dtype=last_record)
            record: list = []
            for i in meta.items():
                dtype, _ = i
                if meta.get(dtype) is True:
                    record.append(dtype)
            last_record: str = ' '.join(record)
        default_prompt: str = '(默认为所有已支持的下载类型)' if last_record is None else ''
        while True:
            download_type: Union[str, list] = console.input(
                f'输入需要下载的「媒体类型」(以空格分隔可多选)。上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」'
                f'格式 - 「video photo document audio voice animation video_note」{default_prompt}:').strip()
            if download_type == '' and last_record is not None:
                download_type = last_record
            if download_type == '':
                download_type = [_ for _ in DownloadType()]
            download_type: list = list(set(download_type.split())) if isinstance(download_type, str) else download_type
            if Validator.is_valid_download_type(download_type):
                dtype = ' '.join(download_type) if download_type else [_ for _ in DownloadType()]
                console.print(
                    f'已设置「download_type」为:「{dtype}」',
                    style=ProcessConfig.stdio_style('download_type')
                )
                return {
                    'download_type': ProcessConfig.set_dtype(_dtype=download_type),
                    'record_flag': True
                }
            else:
                prompt: str = f'意外的参数:"{download_type}"' if download_type else '请重新输入下载类型'
                log.warning(f'{prompt},支持的参数 - 「video photo document」(以空格分隔可多选)')

    @staticmethod
    def get_is_shutdown(last_record: str, valid_format: str = 'y|n') -> dict:
        _style: str = ProcessConfig.stdio_style('is_shutdown')
        if last_record:
            last_record: str = 'y'
        elif last_record is False:
            last_record: str = 'n'
        else:
            last_record = GetStdioParams.UNDEFINED
        t = f'已设置「is_shutdown」为:「y」,下载完成后将自动关机!'  # v1.3.0 修复配置is_shutdown参数时显示错误。
        f = f'已设置「is_shutdown」为:「n」'
        default_prompt: str = '(默认n)' if last_record == GetStdioParams.UNDEFINED else ''
        while True:
            try:
                is_shutdown = console.input(
                    f'下载完成后是否「自动关机」。上一次的记录是:「{last_record}」 - 「{valid_format}」'
                    f'{default_prompt}:').strip().lower()
                if is_shutdown == '' and last_record != GetStdioParams.UNDEFINED:
                    if last_record == 'y':
                        console.print(t, style=_style)
                        return {'is_shutdown': True, 'record_flag': True}
                    elif last_record == 'n':
                        console.print(f, style=_style)
                        return {'is_shutdown': False, 'record_flag': True}

                elif is_shutdown == 'y':
                    console.print(t, style=_style)
                    return {'is_shutdown': True, 'record_flag': True}
                elif is_shutdown in ('n', ''):
                    console.print(f, style=_style)
                    return {'is_shutdown': False, 'record_flag': True}
                else:
                    log.warning(f'意外的参数:"{is_shutdown}",支持的参数 - 「{valid_format}」')

            except Exception as e:
                log.error(f'意外的错误,{_t(KeyWord.REASON)}:"{e}"')

    @staticmethod
    def get_enable_proxy(last_record: Union[str, bool], valid_format: str = 'y|n') -> dict:
        if last_record:
            ep_notice: str = 'y' if last_record else 'n'
        else:
            ep_notice: str = GetStdioParams.UNDEFINED
        default_prompt: str = '(默认n)' if ep_notice == GetStdioParams.UNDEFINED else ''
        while True:  # 询问是否开启代理。
            enable_proxy = console.input(
                f'是否需要使用「代理」。上一次的记录是:「{ep_notice}」'
                f'格式 - 「{valid_format}」{default_prompt}:').strip().lower()
            if enable_proxy == '' and last_record is not None:
                if last_record is True:
                    enable_proxy = 'y'
                elif last_record is False:
                    enable_proxy = 'n'
            elif enable_proxy == '':
                enable_proxy = 'n'
            if Validator.is_valid_enable_proxy(enable_proxy):
                if enable_proxy == 'y':
                    console.print(f'已设置「enable_proxy」为:「{enable_proxy}」',
                                  style=ProcessConfig.stdio_style('enable_proxy'))
                    return {'enable_proxy': True, 'record_flag': True}
                elif enable_proxy == 'n':
                    console.print(f'已设置「enable_proxy」为:「{enable_proxy}」',
                                  style=ProcessConfig.stdio_style('enable_proxy'))
                    return {'enable_proxy': False, 'record_flag': True}
            else:
                log.error(f'意外的参数:"{enable_proxy}",请输入有效参数!支持的参数 - 「{valid_format}」!')

    @staticmethod
    @ProcessConfig.get_system_proxy('scheme')
    def get_scheme(last_record: str, valid_format: list) -> dict:
        if valid_format is None:
            valid_format: list = ['http', 'socks4', 'socks5']
        fmt_valid_format = '|'.join(valid_format)
        while True:  # v1.3.0 修复代理配置scheme参数配置抛出AttributeError。
            scheme = console.input(
                f'请输入「代理类型」。上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」'
                f'格式 - 「{fmt_valid_format}」:').strip().lower()
            if scheme == '' and last_record is not None:
                scheme = last_record
            if Validator.is_valid_scheme(scheme, valid_format):
                console.print(f'已设置「scheme」为:「{scheme}」', style=ProcessConfig.stdio_style('scheme'))
                return {
                    'scheme': scheme,
                    'record_flag': True
                }
            else:
                log.warning(
                    f'意外的参数:"{scheme}",请输入有效的代理类型!支持的参数 - 「{fmt_valid_format}」!')

    @staticmethod
    @ProcessConfig.get_system_proxy('hostname')
    def get_hostname(proxy_config: dict, last_record: str, valid_format: str = 'x.x.x.x'):
        hostname = None
        while True:
            scheme, _, __ = ProcessConfig.get_proxy_info(proxy_config).values()
            # 输入代理IP地址。
            try:
                hostname = console.input(
                    f'请输入代理类型为:"{scheme}"的「ip地址」。上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」'
                    f'格式 - 「{valid_format}」:').strip()
                if hostname == '' and last_record is not None:
                    hostname = last_record
                if Validator.is_valid_hostname(hostname):
                    console.print(f'已设置「hostname」为:「{hostname}」', style=ProcessConfig.stdio_style('hostname'))
                    return {
                        'hostname': hostname,
                        'record_flag': True
                    }
            except ValueError:
                log.warning(
                    f'"{hostname}"不是一个「ip地址」,请输入有效的ipv4地址!支持的参数 - 「{valid_format}」!')

    @staticmethod
    @ProcessConfig.get_system_proxy('port')
    def get_port(proxy_config: dict, last_record: str, valid_format: str = '0~65535'):
        port = None
        # 输入代理端口。
        while True:
            try:  # hostname,scheme可能出现None。
                scheme, hostname, __ = ProcessConfig.get_proxy_info(proxy_config).values()
                port = console.input(
                    f'请输入ip地址为:"{hostname}",代理类型为:"{scheme}"的「代理端口」。'
                    f'上一次的记录是:「{last_record if last_record else GetStdioParams.UNDEFINED}」'
                    f'格式 - 「{valid_format}」:').strip()
                if port == '' and last_record is not None:
                    port = last_record
                if Validator.is_valid_port(port):
                    console.print(f'已设置「port」为:「{port}」', style=ProcessConfig.stdio_style('port'))
                    return {
                        'port': int(port),
                        'record_flag': True
                    }
                else:
                    log.warning(f'意外的参数:"{port}",端口号必须在「{valid_format}」之间!')
            except ValueError:
                log.warning(f'意外的参数:"{port}",请输入一个有效的整数!支持的参数 - 「{valid_format}」')
            except Exception as e:
                log.error(f'意外的错误,{_t(KeyWord.REASON)}:"{e}"')

    @staticmethod
    def get_proxy_authentication():
        # 是否需要认证。
        style = ProcessConfig.stdio_style('proxy_authentication')
        valid_format: str = 'y|n'
        while True:
            is_proxy = console.input(f'代理是否需要「认证」? - 「{valid_format}」(默认n):').strip().lower()
            if is_proxy == 'y':
                username = console.input('请输入「账号」:').strip()
                password = console.input('请输入「密码」:').strip()
                console.print(f'已设置为:「代理需要认证」', style=style)
                return {'username': username, 'password': password, 'record_flag': True}
            elif is_proxy in ('n', ''):
                console.print(f'已设置为:「代理不需要认证」', style=style)
                return {'username': None, 'password': None, 'record_flag': True}
            else:
                log.warning(f'意外的参数:"{is_proxy}",支持的参数 - 「{valid_format}」!')


class BotCommandText:
    HELP: tuple = ('help', '展示可用命令。')
    DOWNLOAD: tuple = (
        'download', '分配新的下载任务(多种使用方式见使用说明)。\n`/download https://t.me/x/x 起始ID 结束ID`')
    TABLE: tuple = ('table', '在终端输出当前下载情况的统计信息。')
    FORWARD: tuple = (
        'forward',
        '从频道A转发至频道B 起始ID 结束ID，可追加 --include-comment 包含评论区。\n'
        '`/forward https://t.me/A https://t.me/B 1 100 --include-comment`'
    )
    EXIT: tuple = ('exit', '退出软件。')
    LISTEN_DOWNLOAD: tuple = ('listen_download',
                              '实时监听该链接的最新消息(视频和图片)进行下载。\n`/listen_download https://t.me/A https://t.me/B https://t.me/n`')
    LISTEN_FORWARD: tuple = (
        'listen_forward',
        '实时监听该链接的最新消息(任意消息)进行转发，可追加 --include-comment 包含评论区。\n'
        '`/listen_forward 监听频道 转发频道 --include-comment`')
    LISTEN_INFO: tuple = ('listen_info', '查看当前已经创建的监听信息。')
    UPLOAD: tuple = ('upload', '上传本地的文件到指定频道。`/upload 本地文件 目标频道`')
    UPLOAD_R: tuple = ('upload_r', '递归上传文件夹(包含子文件夹)到指定频道。`/upload_r 本地文件夹 目标频道`')
    DOWNLOAD_CHAT: tuple = ('download_chat', '下载指定频道并支持通过内联键盘自定义内容过滤。`/download_chat 频道链接`')

    @staticmethod
    def with_description(text: tuple) -> str:
        return f'/{text[0]} - {text[1]}'


class BotCallbackText:
    NULL: str = 'null'
    PAY: str = 'pay'
    LINK_TABLE: str = 'link_table'
    COUNT_TABLE: str = 'count_table'
    UPLOAD_TABLE: str = 'upload_table'
    BACK_HELP: str = 'back_help'
    BACK_TABLE: str = 'back_table'
    NOTICE: str = 'notice'
    DOWNLOAD: str = 'download'
    DOWNLOAD_UPLOAD: str = 'download_upload'
    REMOVE_LISTEN_DOWNLOAD: str = 'rld'
    REMOVE_LISTEN_FORWARD: str = 'rlf'
    LOOKUP_LISTEN_INFO: str = 'lookup_listen_info'
    EXPORT_LINK_TABLE: str = 'export_link_table'
    EXPORT_COUNT_TABLE: str = 'export_count_table'
    EXPORT_UPLOAD_TABLE: str = 'export_upload_table'
    TOGGLE_LINK_TABLE: str = 'toggle_link_table'
    TOGGLE_COUNT_TABLE: str = 'toggle_count_table'
    TOGGLE_UPLOAD_TABLE: str = 'toggle_upload_table'
    TOGGLE_FORWARD_VIDEO: str = 'toggle_forward_video'
    TOGGLE_FORWARD_PHOTO: str = 'toggle_forward_photo'
    TOGGLE_FORWARD_AUDIO: str = 'toggle_forward_audio'
    TOGGLE_FORWARD_VOICE: str = 'toggle_forward_voice'
    TOGGLE_FORWARD_ANIMATION: str = 'toggle_forward_animation'
    TOGGLE_FORWARD_DOCUMENT: str = 'toggle_forward_document'
    TOGGLE_FORWARD_TEXT: str = 'toggle_forward_text'
    TOGGLE_FORWARD_VIDEO_NOTE: str = 'toggle_forward_video_note'
    TOGGLE_DOWNLOAD_VIDEO: str = 'toggle_download_video'
    TOGGLE_DOWNLOAD_PHOTO: str = 'toggle_download_photo'
    TOGGLE_DOWNLOAD_AUDIO: str = 'toggle_download_audio'
    TOGGLE_DOWNLOAD_VOICE: str = 'toggle_download_voice'
    TOGGLE_DOWNLOAD_ANIMATION: str = 'toggle_download_animation'
    TOGGLE_DOWNLOAD_DOCUMENT: str = 'toggle_download_document'
    TOGGLE_DOWNLOAD_VIDEO_NOTE: str = 'toggle_download_video_note'
    EXPORT_TABLE: str = 'export_table'
    SHUTDOWN: str = 'shutdown'
    SETTING: str = 'setting'
    UPLOAD_SETTING: str = 'upload_setting'
    DOWNLOAD_SETTING: str = 'download_setting'
    FORWARD_SETTING: str = 'forward_setting'
    UPLOAD_DOWNLOAD: str = 'upload_download'
    UPLOAD_DOWNLOAD_DELETE: str = 'upload_download_delete'
    UPLOAD_PENDING_LIMIT: str = 'upload_pending_limit'
    DOWNLOAD_CHAT_ID: str = 'download_chat_id'
    DOWNLOAD_CHAT_ID_CANCEL: str = 'download_chat_id_cancel'
    DOWNLOAD_CHAT_FILTER: str = 'download_chat_filter'
    DOWNLOAD_CHAT_DATE_FILTER: str = 'download_chat_date_filter'
    DOWNLOAD_CHAT_DTYPE_FILTER: str = 'download_chat_dtype_filter'
    DOWNLOAD_CHAT_KEYWORD_FILTER: str = 'download_chat_keyword_filter'
    TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO: str = 'toggle_download_chat_video'
    TOGGLE_DOWNLOAD_CHAT_DTYPE_PHOTO: str = 'toggle_download_chat_photo'
    TOGGLE_DOWNLOAD_CHAT_DTYPE_AUDIO: str = 'toggle_download_chat_audio'
    TOGGLE_DOWNLOAD_CHAT_DTYPE_VOICE: str = 'toggle_download_chat_voice'
    TOGGLE_DOWNLOAD_CHAT_DTYPE_ANIMATION: str = 'toggle_download_chat_animation'
    TOGGLE_DOWNLOAD_CHAT_DTYPE_DOCUMENT: str = 'toggle_download_chat_document'
    TOGGLE_DOWNLOAD_CHAT_DTYPE_VIDEO_NOTE: str = 'toggle_download_chat_video_note'
    TOGGLE_DOWNLOAD_CHAT_COMMENT: str = 'toggle_download_chat_comment'
    CALENDAR_CONFIRM: str = 'calendar_confirm'
    FILTER_START_DATE: str = 'filter_start_date'
    FILTER_END_DATE: str = 'filter_end_date'
    DROP_KEYWORD: str = 'drop_keyword'
    IGNORE_KEYWORD: str = 'ignore_keyword'
    CONFIRM_KEYWORD: str = 'confirm_keyword'
    CANCEL_KEYWORD_INPUT: str = 'cancel_keyword_input'

    def __iter__(self):
        for key, value in vars(self.__class__).items():
            if not key.startswith('__') and not callable(value):  # 排除特殊方法和属性。
                yield value


class BotMessage:
    RIGHT: str = '✅以下链接已创建下载任务:\n'
    EXIST: str = '⚠️以下链接已存在已被移除:\n'
    INVALID: str = '🚫以下链接不合法已被移除:\n'


class BotButton:
    GITHUB: str = '📦GitHub'
    SUBSCRIBE_CHANNEL: str = '📌订阅频道'
    VIDEO_TUTORIAL: str = '🎬视频教程'
    PAY: str = '💰支持作者'
    OPEN_NOTICE: str = '📢启用通知'
    CLOSE_NOTICE: str = '🔕禁用通知'
    LINK_TABLE: str = '🔗链接统计表'
    COUNT_TABLE: str = '➕计数统计表'
    UPLOAD_TABLE: str = '📤上传统计表'
    HELP_PAGE: str = '🛎️帮助页面'
    CLICK_VIEW: str = '🖱点击查看'
    CLICK_DOWNLOAD: str = '🖱点击下载'
    DOWNLOAD: str = '⬇️下载'
    DOWNLOAD_UPLOAD: str = '↕️下载后上传'
    TASK_ASSIGN: str = '🌟任务已分配'
    RETRIEVE_MESSAGE: str = '🔎检索消息中'
    RETRIEVE_COMMENT: str = '🔎检索评论区中'
    ASSIGNING_TASK: str = '🚛分配任务中'
    TASK_CANCEL: str = '🗑️任务已取消'
    EXECUTE_TASK: str = '▶️执行任务'
    CANCEL_TASK: str = '⏹️取消任务'
    OK: str = '✅确定'
    CANCEL: str = '❌取消'
    DROP: str = '🗑️移除'
    IGNORE: str = '👁️‍🗨️忽略'
    RETURN: str = '🔙返回'
    CONFIRM_AND_RETURN: str = '↩️确定并返回'
    LOOKUP_LISTEN_INFO: str = '🔍查看监听信息'
    EXPORT_TABLE: str = '📊导出表格'
    RESELECT: str = '🔄重新选择'
    SETTING: str = '⚙️设置'
    OPEN_LINK_TABLE: str = '🔓启用导出链接表格'
    CLOSE_LINK_TABLE: str = '🔒禁用导出链接表格'
    OPEN_COUNT_TABLE: str = '🔓启用导出计数表格'
    CLOSE_COUNT_TABLE: str = '🔒禁用导出计数表格'
    OPEN_UPLOAD_TABLE: str = '🔓启用导出上传表格'
    CLOSE_UPLOAD_TABLE: str = '🔒禁用导出上传表格'
    OPEN_EXIT_SHUTDOWN: str = '✅启用退出后关机'
    CLOSE_EXIT_SHUTDOWN: str = '❌禁用退出后关机'
    ALREADY_REMOVE: str = '✅已移除'
    UPLOAD_SETTING: str = '📤上传设置'
    DOWNLOAD_SETTING: str = '📥下载设置'
    FORWARD_SETTING: str = '↗️转发设置'
    OPEN_UPLOAD_DOWNLOAD: str = '🔓启用下载后上传'
    CLOSE_UPLOAD_DOWNLOAD: str = '🔒禁用下载后上传'
    OPEN_UPLOAD_DOWNLOAD_DELETE: str = '🔓启用下载后上传并删除'
    CLOSE_UPLOAD_DOWNLOAD_DELETE: str = '🔒禁用下载后上传并删除'
    VIDEO_ON: str = '🎬视频 ✅'
    PHOTO_ON: str = '🖼️图片 ✅'
    AUDIO_ON: str = '🎵音频 ✅'
    VOICE_ON: str = '🎤语音 ✅'
    ANIMATION_ON: str = '🎨GIF ✅'
    DOCUMENT_ON: str = '📄文档 ✅'
    TEXT_ON: str = '💬文本消息 ✅'
    VIDEO_NOTE_ON: str = '📹视频笔记 ✅'
    VIDEO_OFF: str = '🎬视频 ❌'
    PHOTO_OFF: str = '🖼️图片 ❌'
    AUDIO_OFF: str = '🎵音频 ❌'
    VOICE_OFF: str = '🎤语音 ❌'
    ANIMATION_OFF: str = '🎨GIF ❌'
    DOCUMENT_OFF: str = '📄文档 ❌'
    TEXT_OFF: str = '💬文本消息 ❌'
    VIDEO_NOTE_OFF: str = '📹视频笔记 ❌'
    DATE_RANGE_SETTING: str = '📅设置日期范围'
    SELECT_START_DATE: str = '⏮️选择起始日期'
    SELECT_END_DATE: str = '⏭️选择结束日期'
    INPUT_KEYWORD: str = '⌨️请向我发送关键词'
    DOWNLOAD_DTYPE_SETTING: str = '📝设置下载类型'
    KEYWORD_FILTER_SETTING: str = '🔑设置匹配关键词'
    CONFIRM_KEYWORD: str = '✅确认关键词'
    INCLUDE_COMMENT: str = '✅包含评论区'
    IGNORE_COMMENT: str = '❌包含评论区'
