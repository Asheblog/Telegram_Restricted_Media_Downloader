# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2025/2/25 1:11
# File:stdio.py
import os
import sys
import csv
import datetime

from typing import Union

from rich.style import Style
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    SpinnerColumn
)
from enum import Enum
from pyrogram import __version__ as pyrogram_version

from module import (
    log,
    console,
    README,
    __version__,
    __copyright__,
    __license__
)
from module.language import _t
from module.util import (
    get_terminal_width,
    is_docker
)
from module.enums import (
    DownloadType,
    UploadStatus,
    KeyWord,
    GradientColor,
    ProcessConfig,
    Banner
)


class StatisticalTable:
    def __init__(self):
        self.skip_video, self.skip_photo, self.skip_document, self.skip_audio, self.skip_voice, self.skip_animation, self.skip_video_note = set(), set(), set(), set(), set(), set(), set()
        self.success_video, self.success_photo, self.success_document, self.success_audio, self.success_voice, self.success_animation, self.success_video_note = set(), set(), set(), set(), set(), set(), set()
        self.failure_video, self.failure_photo, self.failure_document, self.failure_audio, self.failure_voice, self.failure_animation, self.failure_video_note = set(), set(), set(), set(), set(), set(), set()

    def print_count_table(
            self,
            export: bool = False,
            only_export: bool = False,
            export_directory: str = os.path.join(
                os.path.dirname(os.path.abspath(sys.argv[0])),
                'DownloadRecordForm',
                'CountForm'
            )
    ) -> Union[bool, None]:
        """打印统计的下载信息的表格。"""
        success_video: int = len(self.success_video)
        failure_video: int = len(self.failure_video)
        skip_video: int = len(self.skip_video)
        success_photo: int = len(self.success_photo)
        failure_photo: int = len(self.failure_photo)
        skip_photo: int = len(self.skip_photo)
        success_document: int = len(self.success_document)
        failure_document: int = len(self.failure_document)
        skip_document: int = len(self.skip_document)
        success_audio: int = len(self.success_audio)
        failure_audio: int = len(self.failure_audio)
        skip_audio: int = len(self.skip_audio)
        success_voice: int = len(self.success_voice)
        failure_voice: int = len(self.failure_voice)
        skip_voice: int = len(self.skip_voice)
        success_animation: int = len(self.success_animation)
        failure_animation: int = len(self.failure_animation)
        skip_animation: int = len(self.skip_animation)
        success_video_note: int = len(self.success_video_note)
        failure_video_note: int = len(self.failure_video_note)
        skip_video_note: int = len(self.skip_video_note)
        total_video: int = sum([success_video, failure_video, skip_video])
        total_photo: int = sum([success_photo, failure_photo, skip_photo])
        total_document: int = sum([success_document, failure_document, skip_document])
        total_audio: int = sum([success_audio, failure_audio, skip_audio])
        total_voice: int = sum([success_voice, failure_voice, skip_voice])
        total_animation: int = sum([success_animation, failure_animation, skip_animation])
        total_video_note: int = sum([success_video_note, failure_video_note, skip_video_note])
        table_data = [
            [_t(DownloadType.VIDEO), success_video, failure_video, skip_video, total_video],
            [_t(DownloadType.PHOTO), success_photo, failure_photo, skip_photo, total_photo],
            [_t(DownloadType.DOCUMENT), success_document, failure_document, skip_document, total_document],
            [_t(DownloadType.AUDIO), success_audio, failure_audio, skip_audio, total_audio],
            [_t(DownloadType.VOICE), success_voice, failure_voice, skip_voice, total_voice],
            [_t(DownloadType.ANIMATION), success_animation, failure_animation, skip_animation, total_animation],
            [_t(DownloadType.VIDEO_NOTE), success_video_note, failure_video_note, skip_video_note, total_video_note],
            ['合计',
             sum([success_video, success_photo, success_document, success_audio, success_voice, success_animation,
                  success_video_note]),
             sum([failure_video, failure_photo, failure_document, failure_audio, failure_voice, failure_animation,
                  failure_video_note]),
             sum([skip_video, skip_photo, skip_document, skip_audio, skip_voice, skip_animation, skip_video_note]),
             sum([total_video, total_photo, total_document, total_audio, total_voice, total_animation,
                  total_video_note]),
             ]
        ]
        if len(table_data) < 3:
            log.error(f'无法输出计数表格,{_t(KeyWord.REASON)}:"表格数据非法"')
            return False
        check_count: int = 0
        for row in table_data:
            for count in row:
                if isinstance(count, int):
                    check_count += count
        if check_count == 0:
            log.info(f'无法生成计数统计表,{_t(KeyWord.REASON)}:"没有任何下载"')
            return False
        title: str = '媒体下载统计'
        header: tuple = ('类型&状态', '成功下载', '失败下载', '跳过下载', '合计')
        if export:
            try:
                export_directory: str = '/app/form/CountForm' if is_docker() else export_directory
                os.makedirs(export_directory, exist_ok=True)
                with open(
                        file=os.path.join(
                            export_directory,
                            f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_媒体下载统计表.csv'
                        ),
                        mode='w',
                        newline='',
                        encoding='utf-8-sig'
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(table_data)
            except Exception as e:
                log.error(f'导出媒体计数统计表时出错,{_t(KeyWord.REASON)}:"{e}"')
                if only_export:
                    return None
        try:
            if only_export is False:
                PanelTable(
                    title=title,
                    header=header,
                    data=table_data
                ).print_meta()
            return True
        except Exception as e:
            log.error(f'打印媒体计数统计表时出错,{_t(KeyWord.REASON)}:"{e}"')
            return None

    @staticmethod
    def print_link_table(
            link_info: dict,
            export: bool = False,
            only_export: bool = False,
            export_directory: str = os.path.join(
                os.path.dirname(os.path.abspath(sys.argv[0])),
                'DownloadRecordForm',
                'LinkForm'
            )
    ) -> Union[bool, None]:
        """打印统计的下载链接信息的表格。"""
        try:
            data: list = []
            for index, (link, info) in enumerate(link_info.items(), start=1):
                complete_num = int(info.get('complete_num'))
                member_num = int(info.get('member_num'))
                try:
                    rate = round(complete_num / member_num * 100, 2)
                except ZeroDivisionError:
                    rate = 0
                complete_rate = f'{complete_num}/{member_num}[{rate}%]'
                file_names: Union[set, str] = info.get('file_name', set())
                error_msg = info.get('error_msg')
                if not error_msg:
                    error_info = ''
                elif 'all_member' in error_msg:
                    error_info = str(error_msg.get('all_member'))
                else:
                    for fn in error_msg.keys():
                        file_names.add(fn)
                    error_info = '\n'.join([f'{fn}: {err}' for fn, err in error_msg.items()])
                file_names = '\n'.join(sorted(file_names))
                data.append([index, link, file_names, complete_rate, error_info])

            if not data:
                log.info(f'无法生成下载链接统计表,{_t(KeyWord.REASON)}:"没有任何下载"')
                return False
            title: str = '下载链接统计'
            header: tuple = ('编号', '链接', '文件名', '完成率', '错误信息')
            if export:
                try:
                    export_directory: str = '/app/form/LinkForm' if is_docker() else export_directory
                    os.makedirs(export_directory, exist_ok=True)
                    with open(file=os.path.join(
                            export_directory,
                            f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_下载链接统计表.csv'
                    ),
                            mode='w',
                            newline='',
                            encoding='utf-8-sig'
                    ) as f:
                        writer = csv.writer(f)
                        writer.writerow(header)
                        writer.writerows(data)
                except Exception as e:
                    log.error(f'导出下载链接统计表时出错,{_t(KeyWord.REASON)}:"{e}"')
                    if only_export:
                        return None
            if only_export is False:
                PanelTable(
                    title=title,
                    header=header,
                    data=data,
                    show_lines=True
                ).print_meta()
            return True
        except Exception as e:
            log.error(f'打印下载链接统计表时出错,{_t(KeyWord.REASON)}:"{e}"')
            return None

    @staticmethod
    def print_upload_table(
            upload_tasks: set,
            export: bool = False,
            only_export: bool = False,
            export_directory: str = os.path.join(
                os.path.dirname(os.path.abspath(sys.argv[0])),
                'UploadRecordForm',
                'Normal'
            )
    ):
        """打印统计的上传信息的表格。"""
        tasks = list(upload_tasks)
        if not tasks:
            log.info(f'无法生成上传统计表,{_t(KeyWord.REASON)}:"没有任何上传"')
            return False
        meta_table_title: str = '上传任务统计'
        meta_table_header: tuple = (
            '编号',
            '频道',
            '文件',
            '文件大小',
            '状态',
            '上传后自动删除',
            '错误信息'
        )
        meta_table_data = []
        for index, task in enumerate(tasks, start=1):
            if isinstance(task.status, Enum):
                status = _t(str(task.status.value))
            else:
                status = _t(str(task.status))
            delete = '是' if getattr(task, 'with_delete', False) else '否'
            error_msg = getattr(task, 'error_msg', False) or ''
            row = [
                index,
                str(task.chat_id) if task.chat_id else '未知',
                task.file_path,
                MetaData.suitable_units_display(task.file_size),
                status,
                delete,
                error_msg
            ]
            meta_table_data.append(row)

        # 检查数据有效性。
        if len(meta_table_data) < 1:
            return False
        count_table_title = '媒体上传统计'
        count_table_header: tuple = ('状态', '数量')
        pending_tasks = len([t for t in tasks if t.status == UploadStatus.PENDING])
        uploading_tasks = len([t for t in tasks if t.status == UploadStatus.UPLOADING])
        success_tasks = len([t for t in tasks if t.status == UploadStatus.SUCCESS])
        failure_tasks = len([t for t in tasks if t.status == UploadStatus.FAILURE])
        sent_tasks = len([t for t in tasks if t.status == UploadStatus.SENT])
        delete_tasks = len([t for t in tasks if getattr(t, 'with_delete', False)])
        total_tasks = len(tasks)
        total_size = sum(task.file_size for task in tasks)
        count_table_data = [
            [_t(UploadStatus.PENDING), pending_tasks],
            [_t(UploadStatus.UPLOADING), uploading_tasks],
            [_t(UploadStatus.SUCCESS), success_tasks],
            [_t(UploadStatus.FAILURE), failure_tasks],
            [_t(UploadStatus.SENT), sent_tasks],
            ['自动删除', delete_tasks],
            ['合计', total_tasks]
        ]

        if export:
            try:
                export_directory: str = '/app/form/Normal' if is_docker() else export_directory
                os.makedirs(export_directory, exist_ok=True)
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                filename = f'{timestamp}_上传任务统计表.csv'

                with open(
                        file=os.path.join(export_directory, filename),
                        mode='w',
                        newline='',
                        encoding='utf-8-sig'
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow([meta_table_title])
                    writer.writerow(meta_table_header)
                    for row in meta_table_data:
                        writer.writerow(row)

                    writer.writerow([])
                    writer.writerow([count_table_title])
                    for row in count_table_data:
                        writer.writerow(row)

                    writer.writerow([])
                    writer.writerow(
                        ['平均大小', MetaData.suitable_units_display(
                            total_size / total_tasks if total_tasks > 0 else 0)]
                    )
                    writer.writerow(
                        ['总大小', MetaData.suitable_units_display(
                            total_size)]
                    )

                log.info(f'上传任务统计表已导出:{os.path.join(export_directory, filename)}')

            except Exception as e:
                log.error(f'导出上传任务统计表时出错,{_t(KeyWord.REASON)}:"{e}"')
                if only_export:
                    return None

        try:
            if only_export is False:
                PanelTable(
                    title=meta_table_title,
                    header=meta_table_header,
                    data=meta_table_data,
                    show_lines=True
                ).print_meta()
                PanelTable(
                    title=count_table_title,
                    header=count_table_header,
                    data=count_table_data,
                    show_lines=False
                ).print_meta()
            return True

        except Exception as e:
            log.error(f'打印上传任务统计表时出错,{_t(KeyWord.REASON)}:"{e}"')
            return None

    @staticmethod
    def print_config_table(app) -> None:
        """打印用户所填写配置文件的表格。"""
        try:
            if app.enable_proxy:
                proxy_key: list = []
                proxy_value: list = []
                for i in app.proxy.items():
                    if i[0] not in ['enable_proxy', 'username', 'password']:
                        key, value = i
                        proxy_key.append(key)
                        proxy_value.append(value)
                proxy_table = PanelTable(title='代理配置', header=tuple(proxy_key), data=[proxy_value])
                proxy_table.print_meta()
        except Exception as e:
            log.error(f'打印代理配置表时出错,{_t(KeyWord.REASON)}:"{e}"')
        try:
            # 展示链接内容表格。
            with open(file=app.links, mode='r', encoding='UTF-8') as _:
                res: list = [content.strip() for content in _.readlines() if content.strip()]
            if res:
                format_res: list = []
                for i in enumerate(res, start=1):
                    format_res.append(list(i))
                link_table = PanelTable(
                    title='链接内容',
                    header=('编号', '链接'),
                    data=format_res
                )
                link_table.print_meta()
        except FileNotFoundError:
            log.warning('无法读取媒体链接文件,可能已被删除。')
        except (PermissionError, AttributeError) as e:  # v1.1.3 用户错误填写路径提示。
            log.error(f'读取"{app.links}"时出错,{_t(KeyWord.REASON)}:"{e}"')
        except Exception as e:
            log.error(f'打印链接内容统计表时出错,{_t(KeyWord.REASON)}:"{e}"')
        try:
            _dtype: list = app.download_type.copy()  # 浅拷贝赋值给_dtype,避免传入函数后改变原数据。
            data: list = [
                [_t(DownloadType.VIDEO),
                 ProcessConfig.get_dtype(_dtype).get('video', False)
                 ],
                [_t(DownloadType.PHOTO),
                 ProcessConfig.get_dtype(_dtype).get('photo', False)
                 ],
                [_t(DownloadType.DOCUMENT),
                 ProcessConfig.get_dtype(_dtype).get('document', False)
                 ],
                [_t(DownloadType.AUDIO),
                 ProcessConfig.get_dtype(_dtype).get('audio', False)
                 ],
                [_t(DownloadType.VOICE),
                 ProcessConfig.get_dtype(_dtype).get('voice', False)
                 ],
                [_t(DownloadType.ANIMATION),
                 ProcessConfig.get_dtype(_dtype).get('animation', False)
                 ],
                [_t(DownloadType.VIDEO_NOTE),
                 ProcessConfig.get_dtype(_dtype).get('video_note', False)
                 ]
            ]
            download_type_table = PanelTable(title='下载类型', header=('类型', '是否下载'), data=data)
            download_type_table.print_meta()
        except Exception as e:
            log.error(f'打印下载类型统计表时出错,{_t(KeyWord.REASON)}:"{e}"')

    @staticmethod
    def print_env_table(app):
        log.debug(
            {
                'platform': app.platform,
                'python_version': sys.version.split()[0],
                'TRMD_version': __version__,
                'pyrogram_version': pyrogram_version,
                'user_config_path': app.config_path,
                'session_directory': app.work_directory,
                'temp_directory': app.temp_directory,
                'enable_proxy': app.enable_proxy
            }
        )
        PanelTable(
            title='运行环境',
            header=('名称', '值'),
            data=[
                ['平台', app.platform],
                ['Python版本', sys.version.split()[0]],
                ['TRMD版本', __version__],
                ['Pyrogram版本', pyrogram_version],
                ['用户配置文件', app.config_path],
                ['保存目录', app.save_directory],
                ['会话目录', app.work_directory],
                ['缓存目录', app.temp_directory],
                ['使用系统代理', app.enable_proxy]
            ],
            show_lines=True
        ).print_meta()


class PanelTable:
    def __init__(self, title: str, header: tuple, data: list, styles: dict = None, show_lines: bool = False):
        self.table = Table(title=title, highlight=True, show_lines=show_lines)
        self.table.title_style = Style(color='white', bold=True)
        # 添加列。
        for _, col in enumerate(header):
            style = styles.get(col, {}) if styles else {}
            self.table.add_column(col, **style)

        # 添加数据行。
        for row in data:
            self.table.add_row(*map(str, row))  # 确保数据项是字符串类型，防止类型错误。

    def print_meta(self):
        console.print(self.table, justify='center')


class MetaData:
    @staticmethod
    def print_current_task_num(
            prompt: str,
            num: int
    ) -> None:
        console.log(f'{prompt}:{num}。', justify='right', style='#B1DB74')

    @staticmethod
    def print_meta():
        console.print(
            GradientColor.gen_gradient_text(
                text=Banner.TRMD,
                gradient_color=GradientColor.generate_gradient(
                    start_color='#fa709a',
                    end_color='#fee140',
                    steps=10)),
            style='bold',
            highlight=False
        )
        MetaData.print_about()
        MetaData.print_disclaimer()

    @staticmethod
    def print_about():
        console.print(f'[i]{__copyright__}[/i]')
        console.print(f'Licensed under the terms of the {__license__}.', end='\n')

    @staticmethod
    def print_disclaimer():
        console.print(GradientColor.gen_gradient_text(
            '\t所有使用本软件的行为及其后果均由使用者自行承担全部法律责任，开发者不对任何使用行为及其后果负责。',
            gradient_color=GradientColor.BLUE2PURPLE_14)
        )

    @staticmethod
    def suitable_units_display(number: int, unit=None, mebibyte=False) -> str:
        result: dict = MetaData.__determine_suitable_units(number, unit, mebibyte)
        return result.get('number') + result.get('unit')

    @staticmethod
    def __determine_suitable_units(number, unit=None, mebibyte=False) -> dict:
        if mebibyte:
            units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']  # 二进制单位。
            base = 1024
        else:
            units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']  # 十进制单位。
            base = 1000

        if unit in units:  # 如果指定了单位,直接计算。
            index = units.index(unit)
            value = number / (base ** index)
            return {'number': '{:.2f}'.format(value), 'unit': unit}

        else:  # 否则自动计算最合适的单位。
            values = [number]
            for i in range(len(units) - 1):
                if values[i] >= base:
                    values.append(values[i] / base)
                else:
                    break
            return {
                'number': '{:.2f}'.format(values[-1]),
                'unit': units[len(values) - 1]
            }

    @staticmethod
    def print_helper():
        console.print(Markdown('# 配置文件说明'))
        console.print(Markdown(README))


class ProgressBar:
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description} [bold blue]{task.fields[filename]}', justify='right'),
            BarColumn(bar_width=max(int(get_terminal_width() * 0.2), 1)),
            '[progress.percentage]{task.percentage:>3.1f}%',
            '•',
            '[bold green]{task.fields[info]}',
            '•',
            TransferSpeedColumn(),
            '•',
            TimeRemainingColumn(),
            console=console
        )

    @staticmethod
    def download(current, total, progress, task_id) -> None:
        progress.update(
            task_id,
            completed=current,
            info=f'{MetaData.suitable_units_display(current)}/{MetaData.suitable_units_display(total)}',
            total=total
        )

    @staticmethod
    def upload(current, total, progress, task_id, upload_manager) -> None:
        if current > 0:
            upload_manager.update_file_part(
                file_part=(current - 1) // (512 * 1024)
            )
        progress.update(
            task_id,
            completed=current,
            info=f'{MetaData.suitable_units_display(current)}/{MetaData.suitable_units_display(total)}',
            total=total
        )

    @staticmethod
    def bot(completed, total, display_width=20):
        if total == 0:
            return '░' * display_width
        if completed > total:
            completed = total
        ratio = completed / total
        completed_bars = int(ratio * display_width)
        remaining_bars = display_width - completed_bars
        return '█' * completed_bars + '░' * remaining_bars
