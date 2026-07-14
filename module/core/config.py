# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/2/25 1:32
# File:config.py
import os
import sys
import logging
import datetime
import subprocess
from copy import deepcopy

from typing import Union

from module import (
    yaml,
    CustomDumper,
    GLOBAL_CONFIG_NAME,
    GLOBAL_CONFIG_PATH,
    FILE_LOG_LEVEL,
    CONSOLE_LOG_LEVEL,
    log,
    console,
    PLATFORM
)
from module.language import _t
from module.parser import PARSE_ARGS
from module.path_tool import (
    gen_backup_config,
    safe_scan_directory_file
)
from module.core.target_profiles import DEFAULT_TARGET_PROFILES
from module.enums import (
    KeyWord,
    GetStdioParams,
    ProcessConfig
)


class BaseConfig:
    FILE_NAME: str = 'base_config.yaml'
    PATH: str = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), FILE_NAME)
    TEMPLATE: dict = {}

    def __init__(self):
        self.config: dict = deepcopy(self.TEMPLATE)
        self.config_path: str = self.PATH

    @staticmethod
    def add_missing_keys(target, template, log_message) -> None:
        """添加缺失的配置文件参数。"""
        for key, value in template.items():
            if key not in target:
                target[key] = deepcopy(value)
                console.log(log_message.format(key))

    @staticmethod
    def remove_extra_keys(target, template, log_message) -> None:
        """删除多余的配置文件参数。"""
        keys_to_remove: list = [key for key in target.keys() if key not in template]
        for key in keys_to_remove:
            target.pop(key)
            console.log(log_message.format(key))

    def process_nesting(self, param_name: Union[str, dict], config):
        param_template = self.TEMPLATE.get(param_name)
        if param_name in config:
            param_template = self.TEMPLATE.get(param_name)
            param_config = config.get(param_name)
            if not isinstance(param_config, dict):
                param_config: dict = {}
                config[param_name] = param_config
            self.add_missing_keys(
                target=param_config,
                template=param_template,
                log_message='"{}"'
                            f'不在{param_name}配置文件中,已添加。'
            )
            self.remove_extra_keys(
                target=param_config,
                template=param_template,
                log_message='"{}"'
                            f'不在{param_name}配置文件中,已删除。'
            )

    def __check_params(self, config: dict) -> None:
        """检查配置文件的参数是否完整。"""
        # 如果 config 为 None，初始化为一个空字典。
        if config is None:
            config = {}

        # 处理父级参数。
        self.add_missing_keys(target=config, template=self.TEMPLATE, log_message='"{}"不在全局配置文件中,已添加。')
        # 删除父级模板中没有的字段。
        self.remove_extra_keys(config, self.TEMPLATE, '"{}"不在模板中,已删除。')

        if config != self.config:
            self.config = config
            self.save_config(self.config)

    def load_config(self) -> None:
        """加载全局配置文件。"""
        try:
            if not os.path.exists(self.PATH):
                with open(file=self.PATH, mode='w', encoding='UTF-8') as f:
                    yaml.dump(self.TEMPLATE, f, Dumper=CustomDumper)
                return
            with open(file=self.PATH, mode='r', encoding='UTF-8') as f:
                config = yaml.safe_load(f)
                if config:
                    self.config = config
                else:
                    raise ValueError('The file is empty or has invalid format.')
        except Exception as e:
            log.error(f'检测到无效或损坏的全局配置文件。已生成新的模板文件. . .{_t(KeyWord.REASON)}:"{e}"')
            self.config: dict = deepcopy(self.TEMPLATE)
            self.save_config(self.config)

    def save_config(self, config: dict) -> None:
        """保存配置文件。"""
        try:
            with open(file=self.config_path, mode='w', encoding='UTF-8') as f:
                yaml.dump(config, f)
            log.info('全局配置文件已保存。')
        except Exception as e:
            log.error(f'保存全局配置文件失败,{_t(KeyWord.REASON)}:"{e}"')
        finally:
            self.config = config

    def get_config(self, param, error_param=None) -> Union[str, None]:
        """获取实时的配置文件。"""
        self.load_config()
        return self.config.get(param, error_param)


class UserConfig(BaseConfig):
    DIRECTORY_NAME: str = os.path.dirname(os.path.abspath(sys.argv[0]))  # 获取软件工作绝对目录。
    FILE_NAME: str = 'config.yaml'  # 配置文件名。
    PATH: str = os.path.join(DIRECTORY_NAME, FILE_NAME)
    TEMPLATE: dict = {
        'api_id': None,
        'api_hash': None,
        'bot_token': None,
        'session_directory': None,
        'proxy': {
            'enable_proxy': None,
            'scheme': None,
            'hostname': None,
            'port': None,
            'username': None,
            'password': None
        },
        'links': None,
        'save_directory': None,  # v1.3.0 将配置文件中save_path的参数名修改为save_directory。
        'temp_directory': None,
        'max_tasks': {
            'download': 1,
            'upload': 1
        },
        'is_shutdown': None,
        'download_type': None,
        'max_retries': {
            'download': None,
            'upload': None
        }
    }
    TEMP_DIRECTORY: str = os.path.join(os.getcwd(), 'temp')
    BACKUP_DIRECTORY: str = 'ConfigBackup'
    ABSOLUTE_BACKUP_DIRECTORY: str = os.path.join(DIRECTORY_NAME, BACKUP_DIRECTORY)
    WORK_DIRECTORY: str = os.path.join(os.getcwd(), 'sessions')

    @staticmethod
    def _positive_int(value, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @classmethod
    def normalize_runtime_numbers(cls, config: dict) -> dict:
        if not isinstance(config, dict):
            return config
        max_tasks = config.get('max_tasks')
        if not isinstance(max_tasks, dict):
            max_tasks = {}
            config['max_tasks'] = max_tasks
        max_retries = config.get('max_retries')
        if not isinstance(max_retries, dict):
            max_retries = {}
            config['max_retries'] = max_retries
        max_tasks['download'] = cls._positive_int(max_tasks.get('download'), 1)
        max_tasks['upload'] = cls._positive_int(max_tasks.get('upload'), 1)
        max_retries['download'] = cls._positive_int(max_retries.get('download'), 5)
        max_retries['upload'] = cls._positive_int(max_retries.get('upload'), 3)
        return config

    def __init__(self):
        super().__init__()
        self.config_path: str = PARSE_ARGS.config if PARSE_ARGS.config.endswith('.yaml') else UserConfig.PATH
        self.platform: str = PLATFORM
        self.history_timestamp: dict = {}
        self.input_link: list = []
        self.last_record: dict = {}
        self.difference_timestamp: dict = {}
        self.download_type: list = []
        self.record_dtype: set = set()
        self.record_flag: bool = False
        self.modified: bool = False
        self.get_last_history_record()
        self.is_change_account: bool = True
        self.re_config: bool = False
        self.config_guide()
        self.config: dict = self.load_config()  # v1.3.0 修复重复询问重新配置文件。
        self.config = self.normalize_runtime_numbers(self.config)
        self.api_hash = self.config.get('api_hash')
        self.api_id = self.config.get('api_id')
        self.bot_token = self.config.get('bot_token')
        self.download_type: list = self.config.get('download_type')
        self.is_shutdown: bool = self.config.get('is_shutdown')
        self.links: str = self.config.get('links')
        self.max_download_task: int = (self.config.get('max_tasks') or {}).get('download', 1)
        self.max_download_retries: int = (self.config.get('max_retries') or {}).get('download', 5)
        self.max_upload_task: int = (self.config.get('max_tasks') or {}).get('upload', 1)
        self.max_upload_retries: int = (self.config.get('max_retries') or {}).get('upload', 3)
        self.proxy: dict = self.config.get('proxy', {})
        self.enable_proxy: bool = self.proxy.get('enable_proxy', False)
        self.save_directory: str = self.config.get('save_directory')
        self.work_directory: str = PARSE_ARGS.session or (
                self.config.get('session_directory') or UserConfig.WORK_DIRECTORY)
        self.temp_directory: str = PARSE_ARGS.temp or (self.config.get('temp_directory') or UserConfig.TEMP_DIRECTORY)

    def get_last_history_record(self) -> None:
        """获取最近一次保存的历史配置文件。"""
        # 首先判断是否存在目录文件。
        try:
            res: list = safe_scan_directory_file(UserConfig.ABSOLUTE_BACKUP_DIRECTORY)
        except FileNotFoundError:
            return
        except Exception as e:
            log.error(f'读取历史文件时发生错误,{_t(KeyWord.REASON)}:"{e}"')
            return
        file_start: str = 'history_'
        file_end: str = '_config.yaml'

        now_timestamp: float = datetime.datetime.now().timestamp()  # 获取当前的时间戳。
        if res:
            for i in res:  # 找出离当前时间最近的配置文件。
                try:
                    if i.startswith(file_start) and i.endswith(file_end):
                        format_date_str = i.replace(file_start, '').replace(file_end, '').replace('_', ' ')
                        to_datetime_obj = datetime.datetime.strptime(format_date_str, '%Y-%m-%d %H-%M-%S')
                        timestamp = to_datetime_obj.timestamp()
                        self.history_timestamp[timestamp] = i
                except ValueError:
                    pass
                except Exception as _:
                    pass
            for i in self.history_timestamp.keys():
                self.difference_timestamp[now_timestamp - i] = i
            if self.history_timestamp:  # 如果有符合条件的历史配置文件。
                self.last_record: dict = self.__find_history_config()

        else:
            return

    def __find_history_config(self) -> dict:
        """找到历史配置文件。"""
        if not self.history_timestamp:
            return {}
        if not self.difference_timestamp:
            return {}
        try:
            min_key: int = min(self.difference_timestamp.keys())
            min_diff_timestamp: str = self.difference_timestamp.get(min_key)
            min_config_file: str = self.history_timestamp.get(min_diff_timestamp)
            if not min_config_file:
                return {}
            last_config_file: str = os.path.join(UserConfig.ABSOLUTE_BACKUP_DIRECTORY, min_config_file)  # 拼接文件路径。
            with open(file=last_config_file, mode='r', encoding='UTF-8') as f:
                config: dict = yaml.safe_load(f)
            last_record: dict = self.__check_params(config, history=True)  # v1.1.6修复读取历史如果缺失字段使得flag置True。

            if last_record == UserConfig.TEMPLATE:
                # 从字典中删除当前文件。
                self.history_timestamp.pop(min_diff_timestamp, None)
                self.difference_timestamp.pop(min_key, None)
                # 递归调用。
                return self.__find_history_config()
            else:
                return last_record
        except Exception as _:
            return {}

    def add_missing_keys(self, target, template, log_message, history=False) -> None:
        """添加缺失的配置文件参数。"""
        for key, value in template.items():
            if key not in target:
                target[key] = value
                if not history:
                    console.log(log_message.format(key))
                    self.modified = True
                    self.record_flag = True

    def remove_extra_keys(self, target, template, log_message, history=False) -> None:
        """删除多余的配置文件参数。"""
        keys_to_remove: list = [key for key in target.keys() if key not in template]
        for key in keys_to_remove:
            target.pop(key)
            if not history:
                console.log(log_message.format(key))
                self.record_flag = True

    def __check_params(self, config: dict, history=False) -> dict:
        """检查配置文件的参数是否完整。"""
        # 如果 config 为 None，初始化为一个空字典。
        if config is None:
            config = {}

        # 处理父级参数。
        self.add_missing_keys(
            target=config,
            template=UserConfig.TEMPLATE,
            log_message='"{}"不在配置文件中,已添加。',
            history=history
        )

        self.process_nesting(param_name='proxy', config=config)
        self.process_nesting(param_name='max_tasks', config=config)
        self.process_nesting(param_name='max_retries', config=config)

        # 删除父级模板中没有的字段。
        self.remove_extra_keys(
            target=config,
            template=UserConfig.TEMPLATE,
            log_message='"{}"不在模板中,已删除。',
            history=history
        )

        return config

    def load_config(self) -> dict:
        """加载一次当前的配置文件,并附带合法性验证、缺失参数的检测以及各种异常时的处理措施。"""
        config: dict = deepcopy(UserConfig.TEMPLATE)
        try:
            if not os.path.exists(self.config_path):
                with open(file=self.config_path, mode='w', encoding='UTF-8') as f:
                    yaml.dump(UserConfig.TEMPLATE, f, Dumper=CustomDumper)
                console.log('未找到配置文件,已生成新的模板文件. . .')
                self.re_config = True  # v1.3.4 修复配置文件不存在时,无法重新生成配置文件的问题。
            with open(self.config_path, 'r', encoding='UTF-8') as f:
                config: dict = yaml.safe_load(f)  # v1.1.4 加入对每个字段的完整性检测。
            compare_config: dict = deepcopy(config) if config else {}
            config: dict = self.__check_params(config) if compare_config else None
            if config != compare_config or config == UserConfig.TEMPLATE:  # v1.3.4 修复配置文件所有参数都为空时报错问题。
                self.re_config = True
        except UnicodeDecodeError as e:  # v1.1.3 加入配置文件路径是中文或特殊字符时的错误提示,由于nuitka打包的性质决定,
            # 中文路径无法被打包好的二进制文件识别,故在配置文件时无论是链接路径还是媒体保存路径都请使用英文命名。
            self.re_config = True
            log.error(
                f'读取配置文件遇到编码错误,可能保存路径中包含中文或特殊字符的文件夹。已生成新的模板文件. . .{_t(KeyWord.REASON)}:"{e}"')
            self.backup_config(config, error_config=self.re_config)
        except Exception as e:
            self.re_config = True
            console.print('「注意」链接路径和保存路径不能有引号!', style='#B1DB74')
            log.error(f'检测到无效或损坏的配置文件。已生成新的模板文件. . .{_t(KeyWord.REASON)}:"{e}"')
            self.backup_config(config, error_config=self.re_config)
        finally:
            if config is None:
                self.re_config = True
                log.warning('检测到空的配置文件。已生成新的模板文件. . .')
                config: dict = deepcopy(UserConfig.TEMPLATE)
        return config

    def backup_config(
            self,
            backup_config: dict,
            error_config: bool = False,
            force: bool = False
    ) -> None:  # v1.2.9 更正backup_config参数类型。
        """备份当前的配置文件。"""
        if backup_config != UserConfig.TEMPLATE or force:  # v1.2.9 修复比较变量错误的问题。
            backup_path: str = gen_backup_config(
                old_path=self.config_path,
                absolute_backup_dir=UserConfig.ABSOLUTE_BACKUP_DIRECTORY,
                error_config=error_config
            )
            console.log(f'原来的配置文件已备份至"{backup_path}"', style='#B1DB74')
        else:
            console.log('配置文件与模板文件完全一致,无需备份。')

    def config_guide(self) -> None:
        """引导用户以交互式的方式修改、保存配置文件。"""
        # --web: never block on stdin; First-run Setup Wizard fills API later (ADR-0012).
        if PARSE_ARGS.web is not None:
            from module.adapters.webui.setup import apply_web_safe_user_defaults
            pre_load_config: dict = apply_web_safe_user_defaults(self.load_config())
            if PARSE_ARGS.session:
                pre_load_config['session_directory'] = PARSE_ARGS.session
            if PARSE_ARGS.temp:
                pre_load_config['temp_directory'] = PARSE_ARGS.temp
            pre_load_config = self.normalize_runtime_numbers(pre_load_config)
            self.save_config(pre_load_config)
            return
        exit_flag: bool = False
        pre_load_config: dict = self.load_config()
        gsp = GetStdioParams()
        # v1.1.0 更替api_id和api_hash位置,与telegram申请的api位置对应以免输错。
        try:
            if not self.modified and pre_load_config != UserConfig.TEMPLATE:
                re_config: bool = False if PARSE_ARGS.quiet else gsp.get_is_re_config().get('is_re_config')
                if re_config:
                    self.re_config = re_config
                    # 缓存原有的session_directory，防止重新配置时丢失。
                    origin_session_directory = pre_load_config.get('session_directory')
                    pre_load_config: dict = deepcopy(UserConfig.TEMPLATE)
                    self.backup_config(backup_config=pre_load_config, error_config=False, force=True)
                    self.get_last_history_record()  # 更新到上次填写的记录。
                    if not PARSE_ARGS.session:
                        self.is_change_account = gsp.get_is_change_account(valid_format='y|n').get(
                            'is_change_account')
                        if self.is_change_account:
                            pre_load_config['session_directory'] = gsp.get_session_directory().get('session_directory')
                        else:
                            pre_load_config['session_directory'] = origin_session_directory
            _api_id: Union[str, None] = pre_load_config.get('api_id')
            _api_hash: Union[str, None] = pre_load_config.get('api_hash')
            _bot_token: Union[str, None] = pre_load_config.get('bot_token')
            _links: Union[str, None] = pre_load_config.get('links')
            _save_directory: Union[str, None] = pre_load_config.get('save_directory')
            _max_download_task: Union[int, None] = pre_load_config.get('max_tasks', {'download': 1}).get('download')
            _max_download_retries: Union[int, None] = pre_load_config.get('max_retries', {'download': 5}).get(
                'download')
            _download_type: Union[list, None] = pre_load_config.get('download_type')
            _is_shutdown: Union[bool, None] = pre_load_config.get('is_shutdown')
            _proxy_config: dict = pre_load_config.get('proxy', {})
            _enable_proxy: Union[str, bool] = _proxy_config.get('enable_proxy', False)
            _proxy_scheme: Union[str, bool] = _proxy_config.get('scheme', False)
            _proxy_hostname: Union[str, bool] = _proxy_config.get('hostname', False)
            _proxy_port: Union[str, bool] = _proxy_config.get('port', False)
            _proxy_username: Union[str, bool] = _proxy_config.get('username', False)
            _proxy_password: Union[str, bool] = _proxy_config.get('password', False)
            proxy_record: dict = self.last_record.get('proxy', {})  # proxy的历史记录。
            enable_bot: bool = False  # 是否打开机器人。
            if any([not _api_id, not _api_hash, not _save_directory, not _max_download_task, not _download_type]):
                console.print('「注意」直接回车代表使用上次的记录。',
                              style='#B1DB74')
            if self.is_change_account or _api_id is None or _api_hash is None or self.re_config:
                if not _api_id:
                    api_id, record_flag = gsp.get_api_id(
                        last_record=self.last_record.get('api_id')).values()
                    if record_flag:
                        self.record_flag = record_flag
                        pre_load_config['api_id'] = api_id
                if not _api_hash:
                    api_hash, record_flag = gsp.get_api_hash(
                        last_record=self.last_record.get('api_hash'),
                        valid_length=32).values()
                    if record_flag:
                        self.record_flag = record_flag
                        pre_load_config['api_hash'] = api_hash
            if not _bot_token and self.re_config:
                enable_bot: bool = gsp.get_enable_bot(valid_format='y|n').get('enable_bot')
                if enable_bot:
                    bot_token, record_flag = gsp.get_bot_token(
                        last_record=self.last_record.get('bot_token'),
                        valid_format=':').values()
                    if record_flag:
                        self.record_flag = record_flag
                        pre_load_config['bot_token'] = bot_token
            if (not _links or not _bot_token and self.re_config) and PARSE_ARGS.web is None:
                links, record_flag = gsp.get_links(
                    last_record=self.last_record.get('links'),
                    valid_format='.txt',
                    enable_bot=True if enable_bot else False).values()
                if record_flag:
                    self.record_flag = record_flag
                    pre_load_config['links'] = links
            if not _save_directory or self.re_config:
                save_directory, record_flag = gsp.get_save_directory(
                    last_record=self.last_record.get('save_directory')).values()
                if record_flag:
                    self.record_flag = record_flag
                    pre_load_config['save_directory'] = save_directory
            if not _max_download_task or self.re_config:
                max_download_task, record_flag = gsp.get_max_download_task(
                    last_record=self.last_record.get('max_tasks', {'download': 1}).get('download')).values()
                if record_flag:
                    self.record_flag = record_flag
                    pre_load_config.get('max_tasks')['download'] = max_download_task
            if not _max_download_retries or self.re_config:
                max_retry_count, record_flag = gsp.get_max_retry_count(
                    last_record=self.last_record.get('max_retries', {'download': 5}).get('download')).values()
                if record_flag:
                    self.record_flag = record_flag
                    pre_load_config.get('max_retries')['download'] = max_retry_count
            if not _download_type or self.re_config:
                download_type, record_flag = gsp.get_download_type(
                    last_record=self.last_record.get('download_type')).values()
                if record_flag:
                    self.record_flag = record_flag
                    pre_load_config['download_type'] = download_type
            if _is_shutdown is None or self.re_config:
                is_shutdown, _is_shutdown_record_flag = gsp.get_is_shutdown(
                    last_record=self.last_record.get('is_shutdown'),
                    valid_format='y|n').values()
                if _is_shutdown_record_flag:
                    self.record_flag = True
                    pre_load_config['is_shutdown'] = is_shutdown
            # 是否开启代理
            if not _enable_proxy and self.re_config:
                valid_format: str = 'y|n'
                is_enable_proxy, is_ep_record_flag = gsp.get_enable_proxy(
                    last_record=proxy_record.get('enable_proxy', False),
                    valid_format=valid_format).values()
                if is_ep_record_flag:
                    self.record_flag = True
                    _proxy_config['enable_proxy'] = is_enable_proxy
            # 如果需要使用代理。
            # 如果上面配置的enable_proxy为True或本来配置文件中的enable_proxy就为True。
            if _proxy_config.get('enable_proxy') is True or _enable_proxy is True:
                if ProcessConfig.is_proxy_input(proxy_config=_proxy_config):
                    if not _proxy_scheme:
                        scheme, record_flag = gsp.get_scheme(
                            last_record=proxy_record.get('scheme'),
                            valid_format=['http', 'socks4',
                                          'socks5']
                        ).values()
                        if record_flag:
                            self.record_flag = True
                            _proxy_config['scheme'] = scheme
                    if not _proxy_hostname:
                        hostname, record_flag = gsp.get_hostname(
                            proxy_config=_proxy_config,
                            last_record=proxy_record.get('hostname'),
                            valid_format='x.x.x.x').values()
                        if record_flag:
                            self.record_flag = True
                            _proxy_config['hostname'] = hostname
                    if not _proxy_port:
                        port, record_flag = gsp.get_port(
                            proxy_config=_proxy_config,
                            last_record=proxy_record.get('port'),
                            valid_format='0~65535').values()
                        if record_flag:
                            self.record_flag = True
                            _proxy_config['port'] = port
                    if not all([_proxy_username, _proxy_password]):
                        username, password, record_flag = gsp.get_proxy_authentication().values()
                        if record_flag:
                            self.record_flag = True
                            _proxy_config['username'] = username
                            _proxy_config['password'] = password
        except KeyboardInterrupt:
            n: bool = True
            try:
                if self.record_flag:
                    print('\n')
                    if gsp.get_is_ki_save_config().get('is_ki_save_config'):
                        self.save_config(pre_load_config)
                        console.log('配置已保存!')
                    else:
                        console.log('不保存当前填写参数。')
                else:
                    raise SystemExit(0)
            except KeyboardInterrupt:
                n: bool = False
                print('\n')
                console.log('不保存当前填写参数(用户手动终止配置参数)。')
            finally:
                if n:
                    print('\n')
                    console.log('用户手动终止配置参数。')
                self.ctrl_c()
                exit_flag: bool = True
        if exit_flag:
            raise SystemExit(0)
        pre_load_config.get(
            'max_tasks',
            {
                'download': _max_download_task,
                'upload': 1
            }
        )['download'] = (pre_load_config.get('max_tasks') or {}).get('download', 1) or 1
        pre_load_config.get(
            'max_tasks',
            {
                'download': 1,
                'upload': 1
            }
        )['upload'] = (pre_load_config.get('max_tasks') or {}).get('upload', 1) or 1
        pre_load_config.get(
            'max_retries',
            {
                'download': _max_download_retries,
                'upload': 3}
        )['upload'] = (pre_load_config.get('max_retries') or {}).get('upload', 3) or 3
        pre_load_config = self.normalize_runtime_numbers(pre_load_config)
        if not PARSE_ARGS.session:
            _session_directory = pre_load_config.get(
                'session_directory',
                UserConfig.WORK_DIRECTORY) or UserConfig.WORK_DIRECTORY
            pre_load_config['session_directory'] = _session_directory
        else:
            pre_load_config['session_directory'] = PARSE_ARGS.session

        if not PARSE_ARGS.temp:
            _temp_directory = pre_load_config.get(
                'temp_directory',
                UserConfig.TEMP_DIRECTORY) or UserConfig.TEMP_DIRECTORY
            pre_load_config['temp_directory'] = _temp_directory
        else:
            pre_load_config['temp_directory'] = PARSE_ARGS.temp
        self.save_config(pre_load_config)  # v1.3.0 修复不保存配置文件时,配置文件仍然保存的问题。

    def save_config(self, config: dict) -> None:
        """保存配置文件。"""
        try:
            with open(file=self.config_path, mode='w', encoding='UTF-8') as f:
                yaml.dump(config, f)
            log.info('配置文件已保存。')
        except Exception as e:
            log.error(f'保存配置文件失败,{_t(KeyWord.REASON)}:"{e}"')

    def ctrl_c(self):
        if self.platform == 'Windows':
            subprocess.run('pause', shell=True)
        else:
            try:
                console.input('请按「Enter」键继续. . .')
            except KeyboardInterrupt:
                pass


class GlobalConfig(BaseConfig):
    FILE_NAME: str = GLOBAL_CONFIG_NAME
    PATH: str = GLOBAL_CONFIG_PATH
    TEMPLATE: dict = {
        'notice': True,
        'file_log_level': logging.getLevelName(FILE_LOG_LEVEL),
        'console_log_level': logging.getLevelName(CONSOLE_LOG_LEVEL),
        'export_table': {
            'link': False,
            'count': False,
            'upload': False
        },
        'upload':
            {
                'download_upload': True,
                'delete': False,
                'pending_limit': 3,
                'local_storage_reserve_bytes': 1073741824
            },
        'target_profiles': deepcopy(DEFAULT_TARGET_PROFILES),
        'forward_type':
            {
                'video': True,
                'photo': True,
                'audio': True,
                'document': True,
                'voice': True,
                'text': True,
                'animation': True,
                'video_note': True
            },
        'message_filter': {
            'enabled': True,
            'media_types': {
                'video': True,
                'photo': True,
                'audio': True,
                'document': True,
                'voice': True,
                'text': True,
                'animation': True,
                'video_note': True
            },
            'date_range': {
                'enabled': False,
                'start_date': None,
                'end_date': None
            },
            'keywords': {
                'enabled': False,
                'words': ['广告', '推广', '赞助']
            }
        },
        'live_watch': {
            'comment_delay_minutes': 20,
        },
        'deep_link': {
            'bot_whitelist': [],
            'timeout_seconds': 60,
            'min_interval_seconds': 30,
            'settle_seconds': 3,
        },
    }

    def __init__(self):
        super().__init__()
        self.default_upload_nesting = self.TEMPLATE.get('upload')
        self.default_target_profiles_nesting = self.TEMPLATE.get('target_profiles')
        self.default_forward_type_nesting = self.TEMPLATE.get('forward_type')
        self.default_message_filter_nesting = self.TEMPLATE.get('message_filter')
        self.default_live_watch_nesting = self.TEMPLATE.get('live_watch')
        self.default_deep_link_nesting = self.TEMPLATE.get('deep_link')
        self.load_config()
        self.__check_params(deepcopy(self.config))
        self.download_upload: bool = self.get_nesting_config(
            default_nesting=self.default_upload_nesting,
            param='upload',
            nesting_param='download_upload'
        )
        self.upload_delete: bool = self.get_nesting_config(
            default_nesting=self.default_upload_nesting,
            param='upload',
            nesting_param='delete'
        )
        self.upload_pending_limit: int = self.get_upload_pending_limit()
        self.local_storage_reserve_bytes: int = self.get_local_storage_reserve_bytes()
        self.target_profiles: dict = self.config.get('target_profiles', self.default_target_profiles_nesting)
        self.forward_type: dict = self._resolve_forward_type()
        self.message_filter: dict = self.config.get('message_filter', self.default_message_filter_nesting)
        self.live_watch: dict = self.config.get('live_watch', self.default_live_watch_nesting)
        self.comment_delay_minutes: int = self.get_comment_delay_minutes()
        self.deep_link: dict = self.config.get('deep_link', self.default_deep_link_nesting)
        self.deep_link_bot_whitelist: list = self.get_deep_link_bot_whitelist()
        self.deep_link_timeout_seconds: int = self.get_deep_link_timeout_seconds()
        self.deep_link_min_interval_seconds: int = self.get_deep_link_min_interval_seconds()
        self.deep_link_settle_seconds: int = self.get_deep_link_settle_seconds()

    def get_nesting_config(self, default_nesting, param, nesting_param):
        return self.config.get(param, default_nesting).get(nesting_param)

    def _resolve_forward_type(self) -> dict:
        """解析 forward_type，优先从 message_filter.media_types 读取。

        向后兼容：如果 message_filter.media_types 是首次创建的默认值（用户未自定义过），
        则回退到旧 forward_type，避免覆盖用户升级前的自定义设置。
        """
        mf = self.config.get('message_filter')
        if isinstance(mf, dict) and mf.get('media_types'):
            mf_media = mf.get('media_types')
            default_media = self.default_message_filter_nesting.get('media_types', {})
            if mf_media != default_media:
                # 用户自定义过 message_filter → 以它为准
                return dict(mf_media)
        # message_filter 是默认值或不存在 → 回退到 forward_type
        return self.config.get('forward_type', self.default_forward_type_nesting)

    def _sync_message_filter_media_types(self) -> None:
        """双向同步 message_filter.media_types ↔ forward_type（双写兼容）。

        规则：
        1. 如果 message_filter.media_types 与模板默认值不同 → 用户自定义过 → 同步到 forward_type
        2. 如果 message_filter.media_types 是模板默认值（首次创建）→ 从 forward_type 回填
        3. 这种设计保护用户在升级前的 forward_type 自定义设置不被默认值覆盖
        """
        ft = self.config.get('forward_type')
        mf = self.config.get('message_filter')
        if not isinstance(mf, dict):
            mf = {}
            self.config['message_filter'] = mf
        mf_media = mf.get('media_types')
        default_media = self.default_message_filter_nesting.get('media_types', {})
        is_default = isinstance(mf_media, dict) and mf_media == default_media
        if isinstance(mf_media, dict) and not is_default:
            # message_filter.media_types 被用户自定义过 → 同步到 forward_type
            self.config['forward_type'] = dict(mf_media)
        elif ft and isinstance(ft, dict):
            # forward_type 有值，message_filter 还是默认值 → 从 forward_type 回填
            mf['media_types'] = dict(ft)
        elif not isinstance(mf_media, dict):
            # 都没有 → 用默认值
            mf['media_types'] = dict(default_media)

    def get_upload_pending_limit(self) -> int:
        try:
            limit = int(self.get_nesting_config(
                default_nesting=self.default_upload_nesting,
                param='upload',
                nesting_param='pending_limit'
            ))
        except (TypeError, ValueError):
            limit = self.default_upload_nesting.get('pending_limit', 3)
        return min(max(limit, 1), 5)

    def get_local_storage_reserve_bytes(self) -> int:
        default_value = self.default_upload_nesting.get('local_storage_reserve_bytes', 1073741824)
        try:
            value = int(self.get_nesting_config(
                default_nesting=self.default_upload_nesting,
                param='upload',
                nesting_param='local_storage_reserve_bytes'
            ))
        except (TypeError, ValueError):
            value = default_value
        return max(0, value)

    def get_comment_delay_minutes(self) -> int:
        default_value = int(self.default_live_watch_nesting.get('comment_delay_minutes', 20))
        try:
            value = int(self.get_nesting_config(
                default_nesting=self.default_live_watch_nesting,
                param='live_watch',
                nesting_param='comment_delay_minutes'
            ))
        except (TypeError, ValueError, AttributeError):
            value = default_value
        return min(max(value, 0), 1440)

    def get_deep_link_bot_whitelist(self) -> list:
        try:
            raw = self.get_nesting_config(
                default_nesting=self.default_deep_link_nesting,
                param='deep_link',
                nesting_param='bot_whitelist'
            )
        except (TypeError, AttributeError):
            return []
        if isinstance(raw, str):
            raw = [p.strip() for p in raw.replace('\n', ',').split(',')]
        if not isinstance(raw, list):
            return []
        from module.transfer.deep_link import normalize_bot_username
        out = []
        seen = set()
        for item in raw:
            name = normalize_bot_username(item)
            if name and name not in seen:
                seen.add(name)
                out.append(name)
        return out

    def get_deep_link_timeout_seconds(self) -> int:
        default_value = int(self.default_deep_link_nesting.get('timeout_seconds', 60))
        try:
            value = int(self.get_nesting_config(
                default_nesting=self.default_deep_link_nesting,
                param='deep_link',
                nesting_param='timeout_seconds'
            ))
        except (TypeError, ValueError, AttributeError):
            value = default_value
        return min(max(value, 1), 600)

    def get_deep_link_min_interval_seconds(self) -> int:
        default_value = int(self.default_deep_link_nesting.get('min_interval_seconds', 30))
        try:
            value = int(self.get_nesting_config(
                default_nesting=self.default_deep_link_nesting,
                param='deep_link',
                nesting_param='min_interval_seconds'
            ))
        except (TypeError, ValueError, AttributeError):
            value = default_value
        return min(max(value, 0), 600)

    def get_deep_link_settle_seconds(self) -> int:
        default_value = int(self.default_deep_link_nesting.get('settle_seconds', 3))
        try:
            value = int(self.get_nesting_config(
                default_nesting=self.default_deep_link_nesting,
                param='deep_link',
                nesting_param='settle_seconds'
            ))
        except (TypeError, ValueError, AttributeError):
            value = default_value
        return min(max(value, 0), 60)

    def save_config(self, config: dict) -> None:
        super().save_config(config)
        self.download_upload = self.get_nesting_config(
            default_nesting=self.default_upload_nesting,
            param='upload',
            nesting_param='download_upload'
        )
        self.upload_delete = self.get_nesting_config(
            default_nesting=self.default_upload_nesting,
            param='upload',
            nesting_param='delete'
        )
        self.upload_pending_limit = self.get_upload_pending_limit()
        self.local_storage_reserve_bytes = self.get_local_storage_reserve_bytes()
        self.target_profiles = self.config.get('target_profiles', self.default_target_profiles_nesting)
        self._sync_message_filter_media_types()
        self.forward_type: dict = self._resolve_forward_type()
        self.message_filter: dict = self.config.get('message_filter', self.default_message_filter_nesting)
        self.live_watch = self.config.get('live_watch', self.default_live_watch_nesting)
        self.comment_delay_minutes = self.get_comment_delay_minutes()
        self.deep_link = self.config.get('deep_link', self.default_deep_link_nesting)
        self.deep_link_bot_whitelist = self.get_deep_link_bot_whitelist()
        self.deep_link_timeout_seconds = self.get_deep_link_timeout_seconds()
        self.deep_link_min_interval_seconds = self.get_deep_link_min_interval_seconds()
        self.deep_link_settle_seconds = self.get_deep_link_settle_seconds()
        p = '全局配置文件已重新加载。'
        console.log(p, style='#FF4689')
        log.info(f'{p}{self.config}')

    def process_target_profiles(self, config: dict) -> None:
        target_profiles = config.get('target_profiles')
        if not isinstance(target_profiles, dict):
            target_profiles = {}
            config['target_profiles'] = target_profiles
        self.add_missing_keys(
            target=target_profiles,
            template=self.TEMPLATE.get('target_profiles'),
            log_message='"{}"不在target_profiles配置文件中,已添加。'
        )
        for profile_name, profile_template in self.TEMPLATE.get('target_profiles', {}).items():
            profile_config = target_profiles.get(profile_name)
            if not isinstance(profile_config, dict):
                profile_config = {}
                target_profiles[profile_name] = profile_config
            self.add_missing_keys(
                target=profile_config,
                template=profile_template,
                log_message=f'"{{}}"不在target_profiles.{profile_name}配置文件中,已添加。'
            )
            for nested_name, nested_template in profile_template.items():
                if not isinstance(nested_template, dict):
                    continue
                nested_config = profile_config.get(nested_name)
                if not isinstance(nested_config, dict):
                    nested_config = {}
                    profile_config[nested_name] = nested_config
                self.add_missing_keys(
                    target=nested_config,
                    template=nested_template,
                    log_message=f'"{{}}"不在target_profiles.{profile_name}.{nested_name}配置文件中,已添加。'
                )
                self.remove_extra_keys(
                    target=nested_config,
                    template=nested_template,
                    log_message=f'"{{}}"不在target_profiles.{profile_name}.{nested_name}模板中,已删除。'
                )
            self.remove_extra_keys(
                target=profile_config,
                template=profile_template,
                log_message=f'"{{}}"不在target_profiles.{profile_name}模板中,已删除。'
            )

    def process_message_filter(self, config: dict) -> None:
        """处理 message_filter 嵌套配置，确保子段完整。"""
        mf_template = self.TEMPLATE.get('message_filter', {})
        mf = config.get('message_filter')
        if not isinstance(mf, dict):
            mf = {}
            config['message_filter'] = mf
        self.add_missing_keys(
            target=mf,
            template=mf_template,
            log_message='"{}"不在message_filter配置文件中,已添加。'
        )
        # 处理 media_types 子嵌套
        for nested_key in ('media_types', 'date_range', 'keywords'):
            nested_template = mf_template.get(nested_key, {})
            if isinstance(nested_template, dict):
                nested_config = mf.get(nested_key)
                if not isinstance(nested_config, dict):
                    nested_config = {}
                    mf[nested_key] = nested_config
                self.add_missing_keys(
                    target=nested_config,
                    template=nested_template,
                    log_message=f'"{{}}"不在message_filter.{nested_key}配置文件中,已添加。'
                )
                self.remove_extra_keys(
                    target=nested_config,
                    template=nested_template,
                    log_message=f'"{{}}"不在message_filter.{nested_key}模板中,已删除。'
                )
        self.remove_extra_keys(
            target=mf,
            template=mf_template,
            log_message='"{}"不在message_filter模板中,已删除。'
        )

    def __check_params(self, config: dict) -> None:
        if config is None:
            config = {}

        # 处理父级参数。
        self.add_missing_keys(
            target=config,
            template=self.TEMPLATE,
            log_message='"{}"不在全局配置文件中,已添加。'
        )
        # 处理嵌套参数。
        self.process_nesting(param_name='export_table', config=config)
        self.process_nesting(param_name='upload', config=config)
        self.process_target_profiles(config=config)
        self.process_nesting(param_name='forward_type', config=config)
        self.process_message_filter(config=config)
        self.process_nesting(param_name='live_watch', config=config)
        self.process_nesting(param_name='deep_link', config=config)
        # 删除父级模板中没有的字段。
        self.remove_extra_keys(
            target=config,
            template=self.TEMPLATE,
            log_message='"{}"不在模板中,已删除。'
        )

        if config != self.config:
            self.config = config
            self.save_config(self.config)
