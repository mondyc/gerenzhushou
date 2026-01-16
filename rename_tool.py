"""
Single-file release tool with GUI.
- Reimplements the core behavior of the original script in an independent module
- Provides a Tkinter GUI with: inputs, platform selection, dry-run, progress, logs, stop

Run: python rename_tool.py

说明（中文）:
本文件包含两个主要部分：
 1) 发布核心函数 create_release(...)：负责扫描 package 目录、创建输出目录、按平台复制并重命名安装包、生成升级包、复制帮助文档等。
    - 提供 dry_run 模式（只记录动作，不写磁盘）。
    - 提供 log_callback(progress_callback) 回调用于把日志/进度发送给上层（例如 GUI）。
    - 支持 stop_event（threading.Event），用于在长操作中优雅中止。
    - 在 Windows 上，当清空 upgrade_package 遇到权限问题，会尝试清除只读并使用 takeown/icacls 进行权限恢复并重试删除一次。
 2) GUI（ReleaseGUI）：基于 Tkinter 的桌面界面，包含左侧参数面板和右侧日志/进度区，能够启动后台线程运行 create_release，并以线程安全的方式更新 UI。

备注：本文件独立于原 `Rename_v4.py`，不会导入或调用原脚本，便于在不修改历史文件的情况下提供更友好的交互界面。
"""

import os
import re
import shutil
import subprocess
import threading
import tempfile
from datetime import datetime
from typing import Callable, Iterable, Optional
import stat

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext, filedialog
except Exception:
    # 如果 tkinter 不可用，GUI 将无法运行
    raise

# ---------------------- Core functions (no dependency on Rename_v4.py) ----------------------


def get_pkg_dirs(path: str) -> list:
    """返回指定路径下名称以 'pkg' 开头的子目录列表。

    如果路径不存在则返回空列表。此函数用于发现不同平台的 pkg-* 目录。
    """
    if not os.path.exists(path):
        return []
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and re.match(r'^pkg', d)]


def get_suxiaoban_setup_files(path: str) -> list:
    """在指定目录中查找 Windows 安装包（suxiaoban-*-setup.exe.zip）。

    返回匹配文件名的列表（可能为空）。
    """
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if re.match(r'^suxiaoban-.*-setup.exe.zip', f)]


def safe_copy(src: str, dst: str, dry_run: bool, log: Optional[Callable[[str, str], None]] = None) -> bool:
    """安全复制文件并记录日志。

    - 如果 dry_run 为 True，则不实际写盘，只记录计划动作到日志回调。
    - 若目标目录不存在则自动创建。
    - 返回 True 表示成功或模拟成功，False 表示复制失败。
    """
    if dry_run:
        if log:
            log(f"[DRY] COPY: {src} -> {dst}", 'info')
        return True
    # Ensure destination directory exists
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
    except Exception as e:
        if log:
            log(f"ERROR creating dir for {dst}: {e}", 'error')
        return False

    # Try a safe two-step copy: copy to temp file in destination dir then replace
    try:
        dst_dir = os.path.dirname(dst)
        tmp_name = None
        try:
            # Create a temp filename in same directory to ensure replace is on same filesystem
            tmp_fd, tmp_path = tempfile.mkstemp(dir=dst_dir, prefix='.tmp_copy_')
            os.close(tmp_fd)
            tmp_name = tmp_path
            shutil.copy2(src, tmp_name)
            # Attempt atomic replace
            try:
                os.replace(tmp_name, dst)
                if log:
                    log(f"COPY (via tmp) {src} -> {dst}", 'success')
                return True
            except Exception as e_replace:
                # if replace fails, remove tmp and fall through to fallback logic
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass
                raise
        except Exception:
            # If tmp-based copy failed, fall back to direct copy & permission-handling below
            if tmp_name and os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass
            raise
    except PermissionError as pe:
        # 权限被拒：尝试移除目标文件的只读位并删除后重试
        if log:
            log(f"PermissionError copying {src} -> {dst}: {pe}", 'warning')
        try:
            if os.path.exists(dst):
                try:
                    os.chmod(dst, stat.S_IWRITE)
                except Exception:
                    pass
                try:
                    os.remove(dst)
                    if log:
                        log(f"Removed existing destination file {dst} to retry copy", 'info')
                except Exception as e_remove:
                    if log:
                        log(f"Failed removing existing file {dst}: {e_remove}", 'warning')
        except Exception:
            pass

        # Retry copy after removal attempt
        try:
            shutil.copy(src, dst)
            if log:
                log(f"COPY after remove: {src} -> {dst}", 'success')
            return True
        except Exception as e2:
            # 如果仍失败，在 Windows 上尝试 takeown/icacls 对单个文件恢复权限并重试一次
            if os.name == 'nt':
                try:
                    user = os.environ.get('USERNAME') or os.getlogin()
                    cmd_takeown = f'takeown /f "{dst}"'
                    proc1 = subprocess.run(cmd_takeown, shell=True, capture_output=True, text=True)
                    if log and proc1.stdout:
                        log(f'takeown stdout: {proc1.stdout.strip()}', 'info')
                    if log and proc1.stderr:
                        log(f'takeown stderr: {proc1.stderr.strip()}', 'warning')
                    cmd_icacls = f'icacls "{dst}" /grant {user}:F'
                    proc2 = subprocess.run(cmd_icacls, shell=True, capture_output=True, text=True)
                    if log and proc2.stdout:
                        log(f'icacls stdout: {proc2.stdout.strip()}', 'info')
                    if log and proc2.stderr:
                        log(f'icacls stderr: {proc2.stderr.strip()}', 'warning')
                    # 再次尝试删除目标并复制
                    try:
                        if os.path.exists(dst):
                            try:
                                os.chmod(dst, stat.S_IWRITE)
                            except Exception:
                                pass
                            os.remove(dst)
                    except Exception as e_rem2:
                        if log:
                            log(f'二次尝试删除目标失败: {e_rem2}', 'warning')
                    try:
                        shutil.copy(src, dst)
                        if log:
                            log(f"COPY after takeown/icacls: {src} -> {dst}", 'success')
                        return True
                    except Exception as e3:
                        if log:
                            log(f"最终复制失败 {src} -> {dst}: {e3}", 'error')
                        return False
                except Exception as e_win:
                    if log:
                        log(f"Windows 权限恢复尝试失败: {e_win}", 'error')
                    return False
            else:
                if log:
                    log(f"复制失败（非 Windows，无权限恢复）：{e2}", 'error')
                return False
    except Exception as e:
        # 其他错误（例如文件被占用、IOError 等），记录并返回 False
        if log:
            log(f"ERROR copying {src} -> {dst}: {e}", 'error')
        return False


def create_release(version: str,
                   wps_version: str,
                   date: str,
                   platforms: Optional[Iterable[str]] = None,
                   pkgpath: str = './package',
                   helppath: str = './help_documentation',
                   uppath: str = './upgrade_package',
                   output_base: str = './',
                   delete_existing: bool = False,
                   clear_upgrade: bool = False,
                   dry_run: bool = False,
                   log_callback: Optional[Callable[[str, str], None]] = None,
                   progress_callback: Optional[Callable[[int, str], None]] = None,
                   stop_event: Optional[threading.Event] = None) -> dict:
    """
    执行发布流程的核心函数。

    参数说明（简要）:
      - version, wps_version, date: 用户输入的版本与日期（date 格式 YYYYMMDD）
      - platforms: 要处理的平台列表（例如 'linux-arm64','win-x64' 等）
      - pkgpath / helppath / uppath / output_base: 各类路径（可使用默认）
      - delete_existing: 若输出目录已存在，是否删除
      - clear_upgrade: 是否清空 upgrade_package 目录
      - dry_run: 是否为模拟运行（不改磁盘）
      - log_callback: 回调 (msg, level)，用于把日志送到 UI 或其他消费端
      - progress_callback: 回调 (percent, message)，用于更新进度条
      - stop_event: threading.Event，用于中途停止操作

    返回：summary dict（包含 out_dir、platforms、dry_run 等信息）或抛出异常
    """

    # 内部回调包装：避免在回调中抛异常影响主流程
    def _log(msg: str, level: str = 'info'):
        if log_callback:
            try:
                log_callback(msg, level)
            except Exception:
                pass

    def _progress(p: int, msg: str = ''):
        if progress_callback:
            try:
                progress_callback(p, msg)
            except Exception:
                pass

    def _should_stop():
        # 检查是否收到了停止信号
        return stop_event is not None and stop_event.is_set()

    # 默认平台
    if platforms is None:
        platforms = ['linux-arm64', 'linux-x64', 'mac-arm64', 'mac-x64', 'win-x64']

    _log('开始执行发布流程', 'info')
    _progress(0, '开始')

    # ========== 输入校验 ==========
    if not version:
        raise ValueError('版本号不能为空')
    if not re.match(r'^\d{8}$', date):
        raise ValueError('日期格式应为 YYYYMMDD')

    # ========== 扫描 pkg 目录 ==========
    _log(f'扫描 pkg 目录: {pkgpath}', 'info')
    pkg_dirs = get_pkg_dirs(pkgpath)
    _log(f'发现 pkg 文件夹: {pkg_dirs}', 'info')
    if not pkg_dirs:
        # 无 pkg 文件夹无法继续
        raise FileNotFoundError(f'未在 {pkgpath} 发现任何 pkg-* 文件夹')
    _progress(5, '扫描完成')

    # 如果用户勾选了删除已存在的发布主文件夹，则在当前工作目录下删除匹配的文件夹
    if delete_existing:
        try:
            # pattern: 名称以 '灵犀·晓伴_' 开头并包含 ' --'（与旧格式匹配）
            pattern = r'^灵犀·晓伴_.* --.*'
            num = delete_matching_release_dirs('.', pattern, dry_run, _log)
            _log(f'已尝试删除匹配的发布文件夹数量: {num}', 'info')
        except Exception as e:
            _log(f'删除已存在发布文件夹时出错: {e}', 'error')
            # 不阻止后续流程，但记录错误

    if _should_stop():
        _log('被中止（扫描后）', 'warning')
        return {'status': 'stopped'}

    # ========== 处理 upgrade_package（可选清空） ==========
    # 注意：在 Windows 上清空文件夹可能会因为文件被占用或权限问题失败
    if clear_upgrade:
        _log(f'将清空 {uppath}' if not dry_run else f'[DRY] 将清空 {uppath}', 'warning')
        if not dry_run:
            if os.path.exists(uppath):
                # onerror handler: 当 shutil.rmtree 遇到权限问题时，尝试清除只读属性并重试
                def _on_rm_error(func, path, excinfo):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                    except Exception:
                        pass
                    try:
                        func(path)
                    except PermissionError as pe:
                        # 抛出更清晰的异常信息，提示用户可能需要释放占用或提升权限
                        raise PermissionError(f"无法删除文件或目录: {path}. 原因: {pe}. 请关闭占用该文件的程序或以管理员身份运行后重试.")

                try:
                    shutil.rmtree(uppath, onerror=_on_rm_error)
                except PermissionError:
                    # 首次删除失败后，尝试 Windows 下的 takeown/icacls 策略（提升权限并重试）
                    _log(f'权限错误：首次删除 {uppath} 失败，尝试使用 takeown/icacls 恢复权限（仅 Windows）', 'warning')
                    tried = False
                    try:
                        if os.name == 'nt':
                            user = os.environ.get('USERNAME') or os.getlogin()
                            # 尝试 takeown 恢复所有权（非阻塞）
                            try:
                                # 捕获 takeown 输出并记录，以便在 GUI 中查看详细信息
                                cmd = f'takeown /f "{uppath}" /r /d Y'
                                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                                if proc.stdout:
                                    _log(f'takeown stdout: {proc.stdout.strip()}', 'info')
                                if proc.stderr:
                                    _log(f'takeown stderr: {proc.stderr.strip()}', 'warning')
                                _log('已尝试 takeown', 'info')
                            except Exception as e:
                                _log(f'takeown 失败: {e}', 'warning')
                            # 尝试授予完全控制权限（非阻塞）
                            try:
                                # 捕获 icacls 输出并记录
                                cmd2 = f'icacls "{uppath}" /grant {user}:F /T'
                                proc2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
                                if proc2.stdout:
                                    _log(f'icacls stdout: {proc2.stdout.strip()}', 'info')
                                if proc2.stderr:
                                    _log(f'icacls stderr: {proc2.stderr.strip()}', 'warning')
                                _log('已尝试 icacls 授权', 'info')
                            except Exception as e:
                                _log(f'icacls 失败: {e}', 'warning')
                            # 再次尝试删除
                            try:
                                shutil.rmtree(uppath, onerror=_on_rm_error)
                                tried = True
                                _log(f'已通过 takeown/icacls 成功删除 {uppath}', 'success')
                            except Exception as e:
                                _log(f'再次尝试删除失败: {e}', 'error')
                        else:
                            # 非 Windows 平台不支持 takeown/icacls 的自动恢复
                            _log('非 Windows 系统，无法使用 takeown/icacls，删除失败。', 'error')
                    finally:
                        if not tried:
                            _log(f'权限错误：无法清空 {uppath}，请关闭占用该文件/文件夹的程序或以管理员身份运行。', 'error')
                            raise
                # 确保目录存在（即使被删除后也要重建）
                os.makedirs(uppath, exist_ok=True)
    else:
        # 确保升级包目录存在
        os.makedirs(uppath, exist_ok=True)

    _progress(15, '准备输出目录')

    # ========== 输出目录与子文件夹 ==========
    new_dir_name = f"灵犀·晓伴_{version} --{date}"
    out_main = os.path.join(output_base, new_dir_name)
    if os.path.exists(out_main):
        _log(f'已存在输出文件夹: {out_main}', 'warning')
        if not delete_existing:
            # 如果不允许删除，则抛出异常交由调用者处理
            raise FileExistsError(f'输出文件夹已存在: {out_main}')
        else:
            _log(f'删除已存在输出文件夹: {out_main}' if not dry_run else f'[DRY] 删除 {out_main}', 'warning')
            if not dry_run:
                shutil.rmtree(out_main)

    mac_dir_name = f"灵犀·晓伴 {version} mac"
    win_dir_name = f"灵犀·晓伴 {version} win"
    linux_dir_name = f"灵犀·晓伴 {version} 统信+麒麟"

    # 创建平台子文件夹（或在 dry-run 中记录）
    targets = [os.path.join(out_main, mac_dir_name), os.path.join(out_main, win_dir_name), os.path.join(out_main, linux_dir_name)]
    for t in targets:
        if dry_run:
            _log(f'[DRY] MKDIR {t}', 'info')
        else:
            os.makedirs(t, exist_ok=True)
            _log(f'MKDIR {t}', 'success')

    if _should_stop():
        _log('被中止（创建目录后）', 'warning')
        return {'status': 'stopped'}

    _progress(30, '目录创建完成')

    # ========== 复制各平台安装包并生成升级包 ==========
    selected_platforms = [p for p in platforms]
    total_plats = len(selected_platforms)
    if total_plats == 0:
        raise ValueError('没有选择任何平台')

    # 分配进度区间（30% - 80%）给平台处理
    start_pct = 30
    end_pct = 80

    for i, platform in enumerate(selected_platforms, start=1):
        if _should_stop():
            _log('被中止（平台复制中）', 'warning')
            return {'status': 'stopped'}

        frac = (i - 1) / total_plats
        pct = int(start_pct + frac * (end_pct - start_pct))
        _progress(pct, f'处理平台 {platform}...')
        _log(f'处理平台: {platform}', 'info')

        # Windows 特殊处理：使用 suxiaoban 的安装包
        if platform == 'win-x64':
            wins = get_suxiaoban_setup_files(pkgpath)
            if wins:
                win_file = wins[0]
                m = re.findall(r'\d+\.\d+\.\d+', win_file)
                win_version = m[0] if m else version
                new_win_x64 = f"灵犀·晓伴-{win_version}-标准版-{date[-4:]}-win-x64.zip"
                src = os.path.join(pkgpath, win_file)
                dst = os.path.join(out_main, win_dir_name, new_win_x64)
                safe_copy(src, dst, dry_run, log_callback)
                # 同时生成升级包放到 uppath
                upgrade_name = f"gerenzhushou-{win_version}-standard-win32-x64.zip"
                safe_copy(src, os.path.join(uppath, upgrade_name), dry_run, log_callback)
            else:
                _log('未找到 Windows 安装包', 'warning')
        else:
            # 非 Windows 平台，查找 pkg-<arch> 目录
            arch_map = {
                'linux-arm64': ('linux', 'linux-arm64', linux_dir_name),
                'linux-x64': ('linux', 'linux-x64', linux_dir_name),
                'mac-arm64': ('mac', 'mac-arm64', mac_dir_name),
                'mac-x64': ('mac', 'mac-intel-x64', mac_dir_name),
            }
            if platform not in arch_map:
                _log(f'未知平台: {platform}', 'warning')
                continue
            _, arch, target_dir = arch_map[platform]
            # 在 pkgpath 下查找匹配的目录并复制 "灵犀·晓伴.zip"
            for d in os.listdir(pkgpath):
                if os.path.isdir(os.path.join(pkgpath, d)) and re.match(fr'^pkg-{arch}.*', d):
                    src = os.path.join(pkgpath, d, '灵犀·晓伴.zip')
                    if os.path.exists(src):
                        new_filename = f"灵犀·晓伴-{version}-标准版-{date[-4:]}-{arch}.zip"
                        dst = os.path.join(out_main, target_dir, new_filename)
                        safe_copy(src, dst, dry_run, log_callback)
                        # 生成并复制升级包到 uppath
                        upgrade_arch = arch
                        if arch.startswith('mac'):
                            upgrade_arch = arch.replace('mac-', 'darwin-')
                        upgrade_name = f"gerenzhushou-{version}-standard-{upgrade_arch}.zip"
                        safe_copy(src, os.path.join(uppath, upgrade_name), dry_run, log_callback)
                    else:
                        _log(f'源文件不存在: {src}', 'warning')
                    break

    _progress(85, '平台复制完成')

    # ========== 复制帮助文档 ==========
    help_items = [
        ("苏晓伴桌面版帮助说明.docx", [mac_dir_name, win_dir_name, linux_dir_name]),
        ("苏晓伴 mac 版安装说明.docx", [mac_dir_name]),
        ("国产电脑使用苏晓伴说明.docx", [linux_dir_name]),
    ]
    for hf, targets in help_items:
        src = os.path.join(helppath, hf)
        if os.path.exists(src):
            for t in targets:
                dst = os.path.join(out_main, t, hf)
                safe_copy(src, dst, dry_run, log_callback)
        else:
            _log(f'帮助文档不存在: {hf}', 'warning')

    # ========== 复制 releases.json 到 upgrade_package ==========
    releases_src = os.path.join(helppath, 'releases.json')
    if os.path.exists(releases_src):
        safe_copy(releases_src, os.path.join(uppath, 'releases.json'), dry_run, log_callback)

    _progress(95, '复制帮助完成')

    # ========== 完成 ==========
    _progress(100, '完成')
    _log('发布流程完成', 'success')

    summary = {
        'out_dir': out_main,
        'platforms': list(selected_platforms),
        'dry_run': bool(dry_run)
    }
    return summary


# ---------------------- GUI ----------------------

class ReleaseGUI:
    def __init__(self, root):
        # 初始化 GUI 状态和最小窗口大小
        self.root = root
        self.root.title('灵犀·晓伴 发布工具')
        self.root.minsize(1000, 700)
        self.stop_event = None
        self.worker = None
        self.create_widgets()

    def create_widgets(self):
        # 构建主界面布局：顶部 header、操作行、主内容（左输入、右日志）
        base_pad = 12
        self.main_frame = tk.Frame(self.root, bg='#f5f6fa')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=base_pad, pady=base_pad)

        # header（标题）
        header = tk.Frame(self.main_frame, bg='white', relief='raised', bd=1)
        header.grid(row=0, column=0, columnspan=2, sticky='ew')
        header.columnconfigure(0, weight=1)
        title = tk.Label(header, text='灵犀·晓伴 版本发布系统', font=('Microsoft YaHei UI', 18, 'bold'), bg='white')
        title.grid(row=0, column=0, sticky='w', padx=20, pady=10)

        # exec row：独立的一行，放置开始/停止/检查按钮，避免与 header 重叠
        exec_frame = tk.Frame(self.main_frame, bg='#f5f6fa')
        exec_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10, 10))
        exec_frame.columnconfigure(0, weight=1)

        self.start_btn = tk.Button(exec_frame, text='开始执行发布', bg='#27ae60', fg='white', font=('Microsoft YaHei UI', 12, 'bold'), command=self.on_start)
        self.start_btn.grid(row=0, column=0, sticky='ew', padx=10)
        self.stop_btn = tk.Button(exec_frame, text='停止', bg='#e74c3c', fg='white', font=('Microsoft YaHei UI', 12), command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=8)
        self.check_btn = tk.Button(exec_frame, text='检查pkg', command=self.on_check_pkg)
        self.check_btn.grid(row=0, column=2, padx=8)

        # 主内容区域：使用 PanedWindow 将左侧输入区与右侧日志区分隔，避免遮挡
        # PanedWindow 允许用户拖动调整大小，并保证两个区域互不重叠
        paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        paned.grid(row=2, column=0, columnspan=2, sticky='nsew')
        self.main_frame.rowconfigure(2, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # 左侧输入区（可滚动）——设定请求宽度，绑定调整事件以保证最小宽度
        left = tk.Frame(paned, bg='white')
        # 请求一个初始宽度，PanedWindow 通常会尊重子控件的请求尺寸作为初始 sash 位置
        left.update_idletasks()
        left.config(width=600)
        # 防止子控件自动缩放 left 的请求大小（让 paned 控制 sash）
        left.pack_propagate(False)
        paned.add(left, weight=3)

        # 右侧日志区（设置请求宽度，便于初始布局）
        right = tk.Frame(paned, bg='white')
        right.config(width=200)
        right.pack_propagate(False)
        paned.add(right, weight=1)

        # Ensure left pane never becomes narrower than min_left by adjusting requested width on resize
        min_left = 480
        def _ensure_min_left(event=None):
            try:
                total = paned.winfo_width()
                # if total is smaller than required, don't change
                if total <= 0:
                    return
                left_w = left.winfo_width()
                if left_w < min_left:
                    # Request a larger width for left; PanedWindow will relocate sash accordingly
                    left.config(width=min_left)
                    paned.update_idletasks()
            except Exception:
                pass

        paned.bind('<Configure>', _ensure_min_left)

        canvas = tk.Canvas(left, bg='white', highlightthickness=0)
        vscroll = tk.Scrollbar(left, orient=tk.VERTICAL, command=canvas.yview)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=vscroll.set)
        left_inner = tk.Frame(canvas, bg='white')
        canvas.create_window((0,0), window=left_inner, anchor='nw')
        left_inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # 输入字段：版本、WPS、发布日期、平台选择、选项、路径选择
        lbl_font = ('Microsoft YaHei UI', 11)
        tk.Label(left_inner, text='版本号', font=lbl_font, bg='white').grid(row=0, column=0, sticky='w', padx=12, pady=(12,6))
        self.version_entry = tk.Entry(left_inner, font=lbl_font)
        self.version_entry.grid(row=0, column=1, sticky='ew', padx=12)
        left_inner.columnconfigure(1, weight=1)

        tk.Label(left_inner, text='WPS 版本号 (可选)', font=lbl_font, bg='white').grid(row=1, column=0, sticky='w', padx=12, pady=(8,6))
        self.wps_entry = tk.Entry(left_inner, font=lbl_font)
        self.wps_entry.grid(row=1, column=1, sticky='ew', padx=12)

        tk.Label(left_inner, text='发布日期 (YYYYMMDD)', font=lbl_font, bg='white').grid(row=2, column=0, sticky='w', padx=12, pady=(8,6))
        self.date_entry = tk.Entry(left_inner, font=lbl_font)
        self.date_entry.grid(row=2, column=1, sticky='ew', padx=12)
        self.date_entry.insert(0, datetime.now().strftime('%Y%m%d'))

        tk.Label(left_inner, text='目标平台', font=lbl_font, bg='white').grid(row=3, column=0, sticky='w', padx=12, pady=(10,6))
        self.platform_vars = {}
        platforms = [('linux-arm64', 'Linux ARM64'), ('linux-x64','Linux x64'), ('mac-arm64','Mac ARM64'), ('mac-x64','Mac x64'), ('win-x64','Windows x64')]
        for i, (key, text) in enumerate(platforms, start=4):
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(left_inner, text=text, variable=var, bg='white')
            cb.grid(row=i, column=0, columnspan=2, sticky='w', padx=20)
            self.platform_vars[key] = var

        tk.Label(left_inner, text='选项', font=lbl_font, bg='white').grid(row=10, column=0, sticky='w', padx=12, pady=(12,6))
        # 选项：是否删除已存在的发布主文件夹（匹配“灵犀·晓伴_*--*”）
        self.delete_existing_var = tk.BooleanVar(value=False)
        tk.Checkbutton(left_inner, text='是否删除“灵犀·晓伴_*--*”的文件夹', variable=self.delete_existing_var, bg='white').grid(row=11, column=0, columnspan=2, sticky='w', padx=20)
        # 选项：是否清空 upgrade_package 文件夹
        self.clear_upgrade_var = tk.BooleanVar(value=False)
        tk.Checkbutton(left_inner, text='是否清空upgrade_package文件夹', variable=self.clear_upgrade_var, bg='white').grid(row=12, column=0, columnspan=2, sticky='w', padx=20)
        self.dry_run_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left_inner, text='模拟运行（dry-run，不做实际拷贝）', variable=self.dry_run_var, bg='white').grid(row=13, column=0, columnspan=2, sticky='w', padx=20)

        tk.Label(left_inner, text='路径（可选，留空使用默认）', font=lbl_font, bg='white').grid(row=14, column=0, sticky='w', padx=12, pady=(12,6))
        tk.Button(left_inner, text='选择 package 路径', command=self.choose_pkg).grid(row=15, column=0, padx=12, sticky='w')
        self.pkg_label = tk.Label(left_inner, text='', bg='white')
        self.pkg_label.grid(row=15, column=1, sticky='w')
        tk.Button(left_inner, text='选择 help_documentation 路径', command=self.choose_help).grid(row=16, column=0, padx=12, sticky='w')
        self.help_label = tk.Label(left_inner, text='', bg='white')
        self.help_label.grid(row=16, column=1, sticky='w')

        # 右侧日志与进度（right 已由 PanedWindow 包含）
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        # 限制日志显示宽度并按单词换行，避免日志区过宽
        self.log_text = scrolledtext.ScrolledText(right, bg='#1e1e1e', fg='#d4d4d4', font=('Consolas', 11), width=60, wrap='word')
        self.log_text.grid(row=0, column=0, sticky='nsew', padx=6, pady=6)

        btn_frame = tk.Frame(right, bg='white')
        btn_frame.grid(row=1, column=0, sticky='ew')
        tk.Button(btn_frame, text='清空日志', command=self.clear_log).pack(side=tk.LEFT, padx=6, pady=6)
        tk.Button(btn_frame, text='导出日志', command=self.export_log).pack(side=tk.LEFT, padx=6, pady=6)
        # 管理员删除（可选择文件或文件夹）
        tk.Button(btn_frame, text='管理员删除', command=self.on_elevated_remove).pack(side=tk.LEFT, padx=6, pady=6)
        # 使用 subprocess 删除匹配前缀的发布文件夹（尝试 takeown/icacls + rmdir）
        tk.Button(btn_frame, text='删除 灵犀·晓伴_*（subprocess）', command=self.on_subprocess_remove_prefix).pack(side=tk.LEFT, padx=6, pady=6)
        tk.Button(btn_frame, text='强制删除（结束占用）', command=self.on_force_delete).pack(side=tk.LEFT, padx=6, pady=6)

        self.progress = ttk.Progressbar(right, mode='determinate', maximum=100)
        self.progress.grid(row=2, column=0, sticky='ew', padx=6, pady=(0,6))
        self.progress_label = tk.Label(right, text='进度: 0%', bg='white')
        self.progress_label.grid(row=3, column=0, sticky='w', padx=6, pady=(0,12))

    def choose_pkg(self):
        p = filedialog.askdirectory(title='选择 package 文件夹')
        if p:
            self.pkg_label.config(text=p)

    def choose_help(self):
        p = filedialog.askdirectory(title='选择 help_documentation 文件夹')
        if p:
            self.help_label.config(text=p)

    def on_check_pkg(self):
        path = self.pkg_label.cget('text') or './package'
        dirs = get_pkg_dirs(path)
        if dirs:
            messagebox.showinfo('检查结果', f'找到 {len(dirs)} 个 pkg 文件夹:\n{dirs}')
        else:
            messagebox.showwarning('检查结果', '未找到 pkg 开头的文件夹')

    def log(self, message: str, level: str = 'info'):
        def _append():
            tag = 'info'
            if level == 'error':
                tag = 'error'
            elif level == 'warning':
                tag = 'warning'
            elif level == 'success':
                tag = 'success'
            self.log_text.insert(tk.END, message + '\n', tag)
            self.log_text.see(tk.END)
        self.root.after(0, _append)

    def clear_log(self):
        self.log_text.delete('1.0', tk.END)

    def export_log(self):
        content = self.log_text.get('1.0', tk.END)
        fname = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
        if fname:
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo('导出', f'日志已导出到: {fname}')

    def on_start(self):
        version = self.version_entry.get().strip()
        wps = self.wps_entry.get().strip()
        date = self.date_entry.get().strip()
        if not version:
            messagebox.showerror('输入错误', '请输入版本号')
            return
        if not re.match(r'^\d{8}$', date):
            messagebox.showerror('输入错误', '日期格式应为 YYYYMMDD')
            return
        platforms = [k for k, v in self.platform_vars.items() if v.get()]
        if not platforms:
            messagebox.showerror('输入错误', '请至少选择一个平台')
            return

        pkgpath = self.pkg_label.cget('text') or './package'
        helppath = self.help_label.cget('text') or './help_documentation'
        delete_existing = self.delete_existing_var.get()
        clear_upgrade = self.clear_upgrade_var.get()
        dry_run = self.dry_run_var.get()

        if not messagebox.askyesno('确认', f'开始发布?\n版本: {version}\n日期: {date}\n平台: {platforms}\nDry-run: {dry_run}'):
            return

        # disable
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.progress_label.config(text='进度: 0%')
        self.clear_log()

        self.stop_event = threading.Event()

        def _progress_cb(pct, msg):
            def _update():
                self.progress['value'] = pct
                self.progress_label.config(text=f'进度: {pct}% {msg}')
            self.root.after(0, _update)

        def _log_cb(msg, level='info'):
            self.log(msg, level)

        def _target():
            try:
                res = create_release(version, wps, date, platforms=platforms, pkgpath=pkgpath, helppath=helppath, uppath='./upgrade_package', output_base='./', delete_existing=delete_existing, clear_upgrade=clear_upgrade, dry_run=dry_run, log_callback=_log_cb, progress_callback=_progress_cb, stop_event=self.stop_event)
                # Prepare a fixed message string and schedule it on the main thread
                done_msg = f'发布完成: {res.get("out_dir")}'
                self.root.after(0, lambda m=done_msg: messagebox.showinfo('完成', m))
            except Exception as e:
                self.log(f'执行失败: {e}', 'error')
                err_msg = str(e)
                self.root.after(0, lambda m=err_msg: messagebox.showerror('失败', m))
            finally:
                self.root.after(0, self._on_finish)

        # 启动后台线程执行发布任务
        self.worker = threading.Thread(target=_target, daemon=True)
        self.worker.start()

    def _on_finish(self):
        # 任务结束时恢复 UI 状态
        try:
            self.progress['value'] = 100
            self.progress_label.config(text='进度: 100%')
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
        except Exception:
            pass

    def on_stop(self):
        # 发送停止信号给后台任务（若在运行）
        if self.stop_event:
            self.stop_event.set()
            self.log('已发送停止信号，正在等待任务结束...', 'warning')

    def elevated_remove(self, path: str, log: Optional[Callable[[str, str], None]] = None) -> bool:
        """在 Windows 上以管理员权限启动 PowerShell 删除指定路径（文件或文件夹）。

        说明：此函数会使用 Start-Process -Verb RunAs 打开一个提升的 PowerShell 窗口来执行删除。
        因为提升过程会触发 UAC，脚本无法直接捕获提升进程内命令的 stdout/stderr；
        我们只能启动该进程并在 GUI 日志中记录已发起的操作。
        """
        if not os.path.exists(path):
            if log:
                log(f'路径不存在，无法删除: {path}', 'warning')
            return False
        if os.name != 'nt':
            if log:
                log('管理员删除仅在 Windows 上支持', 'error')
            return False
        try:
            # PowerShell 字符串中的单引号通过重复单引号来转义
            escaped = path.replace("'", "''")
            inner = f"-NoProfile -Command \"Remove-Item -LiteralPath '{escaped}' -Recurse -Force; exit\""
            start_cmd = f"Start-Process powershell -Verb RunAs -ArgumentList \"{inner}\""
            # Launch elevated PowerShell which runs the Remove-Item and exits
            subprocess.Popen(['powershell', '-Command', start_cmd], shell=False)
            if log:
                log(f'已启动管理员 PowerShell 来删除: {path}（请在弹出的 UAC 窗口中确认）', 'info')
            return True
        except Exception as e:
            if log:
                log(f'启动管理员删除失败: {e}', 'error')
            return False

    def on_elevated_remove(self):
        # 先让用户选择要删除的文件或文件夹（优先选择文件）
        f = filedialog.askopenfilename(title='选择要管理员删除的文件（取消可选择文件夹）')
        path = f
        if not path:
            d = filedialog.askdirectory(title='选择要管理员删除的文件夹')
            path = d
        if not path:
            return
        if not os.path.exists(path):
            messagebox.showerror('错误', '指定的路径不存在')
            return
        if not messagebox.askyesno('确认', f'确认要以管理员权限删除此路径及其内容吗?\n\n{path}'):
            return

        # 在后台线程中启动提升删除（UAC 窗口会出现，需要用户确认）
        def _run_elevated_remove():
            ok = self.elevated_remove(path, log=lambda msg, level: self.log(msg, level))
            if ok:
                self.log('管理员删除操作已发起，请在弹出的窗口中确认并观察结果。', 'info')
            else:
                self.log('管理员删除操作无法发起或失败，请手动以管理员 PowerShell 执行删除。', 'error')

        threading.Thread(target=_run_elevated_remove, daemon=True).start()

    def on_subprocess_remove_prefix(self):
        """GUI handler: find folders starting with '灵犀·晓伴_' in workspace root and attempt to delete using subprocess commands."""
        base = filedialog.askdirectory(title='选择要搜索并删除灵犀·晓伴_*的父目录（通常为项目根目录）')
        if not base:
            return
        if not os.path.isdir(base):
            messagebox.showerror('错误', '请选择有效的目录')
            return
        if not messagebox.askyesno('确认', f'将在目录下查找并尝试删除以 "灵犀·晓伴_" 开头的文件夹：\n\n{base}\n\n继续吗？'):
            return

        def _run():
            n = remove_prefix_dirs_subprocess(base, '灵犀·晓伴_', log=lambda m, lvl: self.log(m, lvl))
            self.log(f'共处理 {n} 个匹配项（见上方日志）', 'info')

        threading.Thread(target=_run, daemon=True).start()

    def on_force_delete(self):
        """Handler for force delete button: find and kill handles, then delete directory."""
        path = filedialog.askdirectory(title='选择要强制删除的文件夹')
        if not path:
            return
        if not os.path.exists(path):
            messagebox.showerror('错误', '指定的路径不存在')
            return
        if not messagebox.askyesno('确认', f'确认要强制删除此文件夹及其内容吗?\n\n{path}'):
            return

        def _run_force_delete():
            # 尝试查找并终止占用进程
            killed = find_and_kill_handles(path, log=lambda msg, lvl: self.log(msg, lvl))
            if killed:
                self.log('已终止占用进程，尝试删除文件夹', 'info')
            else:
                self.log('未找到占用进程或终止失败，将安排重启后删除', 'warning')
            # 尝试删除文件夹
            if not schedule_delete_on_reboot(path, log=lambda msg, lvl: self.log(msg, lvl)):
                self.log('重启后删除安排失败，请手动删除或重启后清理', 'error')

        threading.Thread(target=_run_force_delete, daemon=True).start()


def remove_prefix_dirs_subprocess(base_dir: str, prefix: str, log: Optional[Callable[[str, str], None]] = None) -> int:
    """Find directories under base_dir with names starting with prefix and attempt to delete them.

    For each directory:
      - First try shutil.rmtree (normal Python delete)
      - If that fails, on Windows try: takeown /f <dir> /r /d Y ; icacls <dir> /grant %USERNAME%:F /T ; rmdir /s /q <dir>
      - Log outputs (stdout/stderr) from subprocess calls to provided log callback.

    Returns the number of directories attempted.
    """
    tried = 0
    try:
        names = os.listdir(base_dir)
    except Exception as e:
        if log:
            log(f'无法列出目录 {base_dir}: {e}', 'error')
        return 0

    for name in names:
        if not name.startswith(prefix):
            continue
        path = os.path.join(base_dir, name)
        if not os.path.isdir(path):
            continue
        tried += 1
        if log:
            log(f'尝试删除: {path}', 'info')
        # Try Python rmtree first
        try:
            shutil.rmtree(path)
            if log:
                log(f'已使用 shutil.rmtree 删除: {path}', 'success')
            continue
        except Exception as e:
            if log:
                log(f'shutil.rmtree 失败: {e}', 'warning')

        # If we reach here, try Windows-specific subprocess approach
        if os.name == 'nt':
            user = os.environ.get('USERNAME') or os.getlogin()
            try:
                # takeown
                cmd1 = f'takeown /f "{path}" /r /d Y'
                p1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
                if log and p1.stdout:
                    log(f'takeown stdout: {p1.stdout.strip()}', 'info')
                if log and p1.stderr:
                    log(f'takeown stderr: {p1.stderr.strip()}', 'warning')

                # icacls
                cmd2 = f'icacls "{path}" /grant {user}:F /T'
                p2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
                if log and p2.stdout:
                    log(f'icacls stdout: {p2.stdout.strip()}', 'info')
                if log and p2.stderr:
                    log(f'icacls stderr: {p2.stderr.strip()}', 'warning')

                # rmdir via cmd
                cmd3 = f'cmd /c rmdir /s /q "{path}"'
                p3 = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
                if log and p3.stdout:
                    log(f'rmdir stdout: {p3.stdout.strip()}', 'info')
                if log and p3.stderr:
                    log(f'rmdir stderr: {p3.stderr.strip()}', 'warning')

                if not os.path.exists(path):
                    if log:
                        log(f'通过 subprocess 删除成功: {path}', 'success')
                else:
                    if log:
                        log(f'通过 subprocess 删除后路径仍存在: {path}', 'error')
            except Exception as e:
                if log:
                    log(f'通过 subprocess 删除发生异常: {e}', 'error')
        else:
            # Non-Windows fallback: try rm -rf via shell
            try:
                cmd = f'rm -rf "{path}"'
                p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if log and p.stdout:
                    log(f'rm stdout: {p.stdout.strip()}', 'info')
                if log and p.stderr:
                    log(f'rm stderr: {p.stderr.strip()}', 'warning')
                if not os.path.exists(path):
                    if log:
                        log(f'已删除: {path}', 'success')
                else:
                    if log:
                        log(f'删除失败，路径仍然存在: {path}', 'error')
            except Exception as e:
                if log:
                    log(f'非 Windows 下删除失败: {e}', 'error')

    return tried


def schedule_delete_on_reboot(path: str, log: Optional[Callable[[str, str], None]] = None) -> bool:
    """Schedule a file or directory to be deleted on next reboot (Windows only) using MoveFileExW.

    Returns True if scheduling succeeded.
    """
    if os.name != 'nt':
        if log:
            log('仅 Windows 支持在重启时删除', 'error')
        return False
    try:
        import ctypes
        MoveFileEx = ctypes.windll.kernel32.MoveFileExW
        MOVEFILE_DELAY_UNTIL_REBOOT = 0x4
        # Use MoveFileExW with NULL new name to schedule deletion
        res = MoveFileEx(str(path), None, MOVEFILE_DELAY_UNTIL_REBOOT)
        if res == 0:
            if log:
                log(f'安排在重启时删除失败: {path}', 'error')
            return False
        if log:
            log(f'已安排在下次重启时删除: {path}', 'info')
        return True
    except Exception as e:
        if log:
            log(f'安排重启删除时出错: {e}', 'error')
        return False


def find_handles_with_handleexe(path: str, log: Optional[Callable[[str, str], None]] = None) -> list:
    """Try to run handle.exe to find processes locking path. Returns list of PIDs found (ints).

    Requires handle.exe available in PATH or in current working directory. Logs output if provided.
    """
    # Try common locations: current dir or PATH
    exe_name = 'handle.exe'
    candidates = [exe_name, os.path.join(os.getcwd(), exe_name)]
    found = None
    for c in candidates:
        try:
            p = subprocess.run([c, '-accepteula', path], shell=False, capture_output=True, text=True)
            # If returncode is 0 or non-zero, it may still print results
            out = p.stdout + '\n' + p.stderr
            if out.strip():
                found = out
                break
        except FileNotFoundError:
            continue
        except Exception as e:
            if log:
                log(f'运行 handle.exe 时出错: {e}', 'warning')
            continue
    if not found:
        if log:
            log('未在 PATH 或当前目录找到 handle.exe', 'warning')
        return []

    # Parse PIDs from handle output. Look for 'pid: 1234' or patterns like 'explorer.exe pid: 1234'
    pids = set()
    for line in found.splitlines():
        m = re.search(r'pid:\s*(\d+)', line, re.IGNORECASE)
        if m:
            try:
                pids.add(int(m.group(1)))
            except Exception:
                pass
        else:
            # fallback: match ' 1234: ' patterns
            m2 = re.search(r'\s(\d{2,6})\s', line)
            if m2:
                try:
                    pids.add(int(m2.group(1)))
                except Exception:
                    pass
    if log:
        log(f'handle.exe 输出检测到 PID: {sorted(pids)}', 'info')
    return list(pids)


def find_and_kill_handles(path: str, log: Optional[Callable[[str, str], None]] = None) -> bool:
    """Find PIDs locking path using handle.exe and kill them via taskkill. Returns True if any were killed."""
    pids = find_handles_with_handleexe(path, log)
    if not pids:
        if log:
            log('没有检测到使用 handle.exe 的占用进程（或 handle.exe 不可用）', 'warning')
        return False
    killed_any = False
    for pid in pids:
        try:
            cmd = f'taskkill /PID {pid} /F'
            p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if p.stdout:
                if log:
                    log(f'taskkill stdout: {p.stdout.strip()}', 'info')
            if p.stderr:
                if log:
                    log(f'taskkill stderr: {p.stderr.strip()}', 'warning')
            if p.returncode == 0:
                killed_any = True
                if log:
                    log(f'已终止进程 PID={pid}', 'success')
            else:
                if log:
                    log(f'无法终止 PID={pid}（taskkill 返回码 {p.returncode}）', 'warning')
        except Exception as e:
            if log:
                log(f'终止 PID={pid} 时发生异常: {e}', 'error')
    return killed_any


def delete_matching_release_dirs(base_dir: str, pattern: str, dry_run: bool, log: Optional[Callable[[str, str], None]] = None) -> int:
    """删除 base_dir 下名称匹配正则 pattern 的目录。

    返回尝试删除的目录数量。支持 dry_run（仅记录日志，不实际删除）。
    在删除失败时，在 Windows 上尝试 takeown/icacls + rmdir 回退策略，并记录输出。
    """
    try:
        names = os.listdir(base_dir)
    except Exception as e:
        if log:
            log(f'无法列出目录 {base_dir}: {e}', 'error')
        return 0

    regex = re.compile(pattern)
    count = 0
    for name in names:
        if not regex.match(name):
            continue
        path = os.path.join(base_dir, name)
        if not os.path.isdir(path):
            continue
        count += 1
        if dry_run:
            if log:
                log(f'[DRY] 将删除文件夹: {path}', 'info')
            continue

        if log:
            log(f'尝试删除文件夹: {path}', 'info')

        # Try normal delete first
        try:
            shutil.rmtree(path)
            if log:
                log(f'已删除: {path}', 'success')
            continue
        except Exception as e:
            if log:
                log(f'shutil.rmtree 失败: {e}', 'warning')

        # Windows fallback: takeown + icacls + rmdir
        if os.name == 'nt':
            user = os.environ.get('USERNAME') or os.getlogin()
            try:
                cmd1 = f'takeown /f "{path}" /r /d Y'
                p1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
                if log and p1.stdout:
                    log(f'takeown stdout: {p1.stdout.strip()}', 'info')
                if log and p1.stderr:
                    log(f'takeown stderr: {p1.stderr.strip()}', 'warning')

                cmd2 = f'icacls "{path}" /grant {user}:F /T'
                p2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
                if log and p2.stdout:
                    log(f'icacls stdout: {p2.stdout.strip()}', 'info')
                if log and p2.stderr:
                    log(f'icacls stderr: {p2.stderr.strip()}', 'warning')

                cmd3 = f'cmd /c rmdir /s /q "{path}"'
                p3 = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
                if log and p3.stdout:
                    log(f'rmdir stdout: {p3.stdout.strip()}', 'info')
                if log and p3.stderr:
                    log(f'rmdir stderr: {p3.stderr.strip()}', 'warning')

                if not os.path.exists(path):
                    if log:
                        log(f'通过 subprocess 删除成功: {path}', 'success')
                else:
                    if log:
                        log(f'通过 subprocess 删除后路径仍存在: {path}', 'error')
            except Exception as e:
                if log:
                    log(f'通过 subprocess 删除发生异常: {e}', 'error')
        else:
            # Non-Windows fallback
            try:
                cmd = f'rm -rf "{path}"'
                p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if log and p.stdout:
                    log(f'rm stdout: {p.stdout.strip()}', 'info')
                if log and p.stderr:
                    log(f'rm stderr: {p.stderr.strip()}', 'warning')
                if not os.path.exists(path):
                    if log:
                        log(f'已删除: {path}', 'success')
                else:
                    if log:
                        log(f'删除失败，路径仍然存在: {path}', 'error')
            except Exception as e:
                if log:
                    log(f'非 Windows 下删除失败: {e}', 'error')

    return count


if __name__ == '__main__':
    root = tk.Tk()
    app = ReleaseGUI(root)

    # 配置日志颜色标签
    try:
        app.log_text.tag_config('info', foreground='#4fc1ff')
        app.log_text.tag_config('success', foreground='#4ec9b0')
        app.log_text.tag_config('warning', foreground='#dcdcaa')
        app.log_text.tag_config('error', foreground='#f14c4c')
    except Exception:
        pass

    root.mainloop()
