"""
文件重命名和组织脚本

功能说明：
1. 检查并验证必要的文件夹和文件
2. 创建版本化的文件夹结构
3. 从package文件夹复制文件并重命名
4. 复制帮助文档到相应文件夹
5. 生成升级包文件

更新历史：
- 20251230: 将预置路径改为相对路径
- 20250102: 添加pkg文件夹存在性检查
- 20250102: 添加目标文件夹存在性检查和删除功能
"""

import os
import re
import shutil
import subprocess
import sys


# ==================== 配置区域 ====================

# 路径配置（使用相对路径）
BASE_PATH = './'                    # 基础路径
HELP_PATH = './help_documentation'  # 帮助文档路径
UPGRADE_PATH = './upgrade_package'  # 升级包路径
PKG_PATH = './package'              # 包文件路径

# 文件名配置
SOURCE_ZIP_NAME = "灵犀·晓伴.zip"  # 源zip文件名


# ==================== 工具函数 ====================

def get_pkg_dirs(path):
    """
    获取指定路径下所有以'pkg'开头的文件夹列表
    
    参数:
        path (str): 要搜索的路径
        
    返回:
        list: 符合条件的文件夹名称列表
    """
    pkg_dirs = []
    if not os.path.exists(path):
        return pkg_dirs
        
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and re.match(r'^pkg.*', item):
            pkg_dirs.append(item)
    return pkg_dirs


def get_suxiaoban_setup_files(path):
    """
    获取指定路径下所有匹配'suxiaoban-*-setup.exe.zip'模式的文件列表
    
    参数:
        path (str): 要搜索的路径
        
    返回:
        list: 符合条件的文件名列表
    """
    setup_files = []
    if not os.path.exists(path):
        return setup_files
        
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)) and re.match(r'^suxiaoban-.*-setup.exe.zip', item):
            setup_files.append(item)
    return setup_files


def check_existing_target_folder():
    """
    检查当前目录下是否已存在目标文件夹（匹配'灵犀·晓伴.*--.*'模式）
    如果存在，询问用户是否删除
    
    返回:
        bool: 如果文件夹存在且用户选择不删除，返回False；否则返回True
    """
    for item in os.listdir(BASE_PATH):
        if os.path.isdir(os.path.join(BASE_PATH, item)) and re.match(r'^灵犀·晓伴.*--.*', item):
            print(f"检测到已存在的文件夹: {item}")
            print("是否删除整个文件夹？ 1. 删除 or 2. 不删除")
            choice = input("请输入你的选择：")
            
            if choice == "1":
                try:
                    # 使用Windows命令删除文件夹
                    subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', item], shell=True, check=True)
                    print(f"已成功删除文件夹: {item}")
                    return True
                except PermissionError as e:
                    print(f"删除文件夹时发生权限错误: {e}")
                    sys.exit(1)
                except Exception as e:
                    print(f"删除文件夹时发生错误: {e}")
                    sys.exit(1)
            elif choice == "2":
                print("用户选择不删除，程序退出")
                return False
    return True


def setup_upgrade_folder():
    """
    检查并设置升级包文件夹
    如果文件夹不存在则创建，如果存在则询问用户是否清空
    
    返回:
        bool: 如果用户选择不清空已存在的文件夹，返回False；否则返回True
    """
    if not os.path.exists(UPGRADE_PATH):
        os.mkdir(UPGRADE_PATH)
        print("upgrade_package文件夹创建成功！")
        return True
    else:
        print("upgrade_package文件夹已存在！")
        print("是否清空upgrade_package文件夹的所有内容？1. 清空 or 2. 不清空")
        choice = input("请输入你的选择：")
        
        if choice == "1":
            try:
                # 删除并重新创建文件夹
                subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', 'upgrade_package'], shell=True, check=True)
                os.mkdir(UPGRADE_PATH)
                print(f"已成功清空文件夹: {UPGRADE_PATH}")
                return True
            except PermissionError as e:
                print(f"清空文件夹时发生权限错误: {e}")
                sys.exit(1)
            except Exception as e:
                print(f"清空文件夹时发生错误: {e}")
                sys.exit(1)
        elif choice == "2":
            print("用户选择不清空，程序退出")
            return False


def get_user_input():
    """
    获取用户输入的版本信息和日期
    
    返回:
        tuple: (version, wps_version, date) 版本号和日期元组
    """
    version = input("请输入灵犀·晓伴的版本号：")
    wps_version = input("请输入wps的版本号：")
    date = input("请输入日期（格式：20210101）：")
    
    return version, wps_version, date


def create_folder_structure(version, date):
    """
    创建文件夹结构
    
    参数:
        version (str): 版本号
        date (str): 日期（格式：20210101）
        
    返回:
        tuple: (new_dir_name, mac_dir_name, win_dir_name, linux_dir_name) 文件夹名称元组
    """
    # 创建主文件夹名称：灵犀·晓伴_版本号 --日期
    new_dir_name = f"灵犀·晓伴_{version} --{date}"
    print(f"新的文件夹名称为：{new_dir_name}")
    
    # 创建主文件夹
    os.mkdir(new_dir_name)
    
    # 创建子文件夹名称
    mac_dir_name = f"灵犀·晓伴 {version} mac"
    win_dir_name = f"灵犀·晓伴 {version} win"
    linux_dir_name = f"灵犀·晓伴 {version} 统信+麒麟"
    
    # 打印文件夹名称
    print(f"mac文件夹名称为：{mac_dir_name}")
    print(f"win文件夹名称为：{win_dir_name}")
    print(f"linux文件夹名称为：{linux_dir_name}")
    
    # 创建子文件夹
    os.mkdir(os.path.join(new_dir_name, mac_dir_name))
    os.mkdir(os.path.join(new_dir_name, win_dir_name))
    os.mkdir(os.path.join(new_dir_name, linux_dir_name))
    
    print("mac文件夹创建成功！")
    print("win文件夹创建成功！")
    print("linux文件夹创建成功！")
    
    return new_dir_name, mac_dir_name, win_dir_name, linux_dir_name


def copy_linux_files(pkg_path, new_dir_name, linux_dir_name, version, date_suffix, upgrade_path):
    """
    复制Linux平台的文件并重命名
    
    参数:
        pkg_path (str): 包文件路径
        new_dir_name (str): 新主文件夹名称
        linux_dir_name (str): Linux子文件夹名称
        version (str): 版本号
        date_suffix (str): 日期后缀（后4位）
        upgrade_path (str): 升级包路径
    """
    # 处理 Linux ARM64 文件
    for item in os.listdir(pkg_path):
        item_path = os.path.join(pkg_path, item)
        if os.path.isdir(item_path) and re.match(r'^pkg-linux-arm64.*', item):
            source_file = os.path.join(item_path, SOURCE_ZIP_NAME)
            if not os.path.exists(source_file):
                print(f"警告：源文件不存在 {source_file}")
                continue
                
            # 生成新文件名：灵犀·晓伴-版本号-标准版-日期-linux-arm64.zip
            new_filename = f"灵犀·晓伴-{version}-标准版-{date_suffix}-linux-arm64.zip"
            dest_file = os.path.join(new_dir_name, linux_dir_name, new_filename)
            
            # 复制到目标文件夹
            shutil.copy(source_file, dest_file)
            print(f"复制文件成功，原文件路径：{source_file}")
            
            # 生成升级包文件名：gerenzhushou-版本号-standard-linux-arm64.zip
            upgrade_filename = f"gerenzhushou-{version}-standard-linux-arm64.zip"
            upgrade_file = os.path.join(upgrade_path, upgrade_filename)
            shutil.copy(source_file, upgrade_file)
    
    # 处理 Linux x64 文件
    for item in os.listdir(pkg_path):
        item_path = os.path.join(pkg_path, item)
        if os.path.isdir(item_path) and re.match(r'^pkg-linux-x64.*', item):
            source_file = os.path.join(item_path, SOURCE_ZIP_NAME)
            if not os.path.exists(source_file):
                print(f"警告：源文件不存在 {source_file}")
                continue
                
            # 生成新文件名：灵犀·晓伴-版本号-标准版-日期-linux-x64.zip
            new_filename = f"灵犀·晓伴-{version}-标准版-{date_suffix}-linux-x64.zip"
            dest_file = os.path.join(new_dir_name, linux_dir_name, new_filename)
            
            # 复制到目标文件夹
            shutil.copy(source_file, dest_file)
            print(f"复制文件成功，原文件路径：{source_file}")
            
            # 生成升级包文件名：gerenzhushou-版本号-standard-linux-x64.zip
            upgrade_filename = f"gerenzhushou-{version}-standard-linux-x64.zip"
            upgrade_file = os.path.join(upgrade_path, upgrade_filename)
            shutil.copy(source_file, upgrade_file)


def copy_mac_files(pkg_path, new_dir_name, mac_dir_name, version, date_suffix, upgrade_path):
    """
    复制Mac平台的文件并重命名
    
    参数:
        pkg_path (str): 包文件路径
        new_dir_name (str): 新主文件夹名称
        mac_dir_name (str): Mac子文件夹名称
        version (str): 版本号
        date_suffix (str): 日期后缀（后4位）
        upgrade_path (str): 升级包路径
    """
    # 处理 Mac ARM64 文件
    for item in os.listdir(pkg_path):
        item_path = os.path.join(pkg_path, item)
        if os.path.isdir(item_path) and re.match(r'^pkg-mac-arm64.*', item):
            source_file = os.path.join(item_path, SOURCE_ZIP_NAME)
            if not os.path.exists(source_file):
                print(f"警告：源文件不存在 {source_file}")
                continue
                
            # 生成新文件名：灵犀·晓伴-版本号-标准版-日期-mac-arm64.zip
            new_filename = f"灵犀·晓伴-{version}-标准版-{date_suffix}-mac-arm64.zip"
            dest_file = os.path.join(new_dir_name, mac_dir_name, new_filename)
            
            # 复制到目标文件夹
            shutil.copy(source_file, dest_file)
            print(f"复制文件成功，原文件路径：{source_file}")
            
            # 生成升级包文件名：gerenzhushou-版本号-standard-darwin-arm64.zip
            upgrade_filename = f"gerenzhushou-{version}-standard-darwin-arm64.zip"
            upgrade_file = os.path.join(upgrade_path, upgrade_filename)
            shutil.copy(source_file, upgrade_file)
    
    # 处理 Mac x64 (Intel) 文件
    for item in os.listdir(pkg_path):
        item_path = os.path.join(pkg_path, item)
        if os.path.isdir(item_path) and re.match(r'^pkg-mac-x64.*', item):
            source_file = os.path.join(item_path, SOURCE_ZIP_NAME)
            if not os.path.exists(source_file):
                print(f"警告：源文件不存在 {source_file}")
                continue
                
            # 生成新文件名：灵犀·晓伴-版本号-标准版-日期-mac-intel-x64.zip
            new_filename = f"灵犀·晓伴-{version}-标准版-{date_suffix}-mac-intel-x64.zip"
            dest_file = os.path.join(new_dir_name, mac_dir_name, new_filename)
            
            # 复制到目标文件夹
            shutil.copy(source_file, dest_file)
            print(f"复制文件成功，原文件路径：{source_file}")
            
            # 生成升级包文件名：gerenzhushou-版本号-standard-darwin-x64.zip
            upgrade_filename = f"gerenzhushou-{version}-standard-darwin-x64.zip"
            upgrade_file = os.path.join(upgrade_path, upgrade_filename)
            shutil.copy(source_file, upgrade_file)


def copy_windows_files(pkg_path, new_dir_name, win_dir_name, date_suffix, upgrade_path):
    """
    复制Windows平台的文件并重命名
    
    参数:
        pkg_path (str): 包文件路径
        new_dir_name (str): 新主文件夹名称
        win_dir_name (str): Windows子文件夹名称
        date_suffix (str): 日期后缀（后4位）
        upgrade_path (str): 升级包路径
    """
    setup_files = get_suxiaoban_setup_files(pkg_path)
    
    if not setup_files:
        print("未找到Windows安装文件")
        return
    
    print(f"找到Windows安装文件：{setup_files}")
    
    # 从文件名中提取版本号（格式：suxiaoban-1.2.28-setup.exe.zip）
    version_match = re.findall(r'\d+\.\d+\.\d+', setup_files[0])
    if not version_match:
        print(f"警告：无法从文件名中提取版本号：{setup_files[0]}")
        return
    
    win_version = version_match[0]
    print(f"Windows版本号为：{win_version}")
    
    source_file = os.path.join(pkg_path, setup_files[0])
    if not os.path.exists(source_file):
        print(f"警告：源文件不存在 {source_file}")
        return
    
    # 生成新文件名：灵犀·晓伴-版本号-标准版-日期-win-x64.zip
    new_filename = f"灵犀·晓伴-{win_version}-标准版-{date_suffix}-win-x64.zip"
    dest_file = os.path.join(new_dir_name, win_dir_name, new_filename)
    
    # 复制到目标文件夹
    print(f"源文件路径：{source_file}")
    shutil.copy(source_file, dest_file)
    print(f"复制文件成功，原文件路径：{source_file}")
    
    # 生成升级包文件名：gerenzhushou-版本号-standard-win32-x64.zip
    upgrade_filename = f"gerenzhushou-{win_version}-standard-win32-x64.zip"
    upgrade_file = os.path.join(upgrade_path, upgrade_filename)
    shutil.copy(source_file, upgrade_file)


def copy_help_documents(help_path, new_dir_name, mac_dir_name, win_dir_name, linux_dir_name):
    """
    复制帮助文档到各个平台文件夹
    
    参数:
        help_path (str): 帮助文档路径
        new_dir_name (str): 新主文件夹名称
        mac_dir_name (str): Mac子文件夹名称
        win_dir_name (str): Windows子文件夹名称
        linux_dir_name (str): Linux子文件夹名称
    """
    # 通用帮助文档：复制到所有平台文件夹
    common_help_file = os.path.join(help_path, "苏晓伴桌面版帮助说明.docx")
    if os.path.exists(common_help_file):
        shutil.copy(common_help_file, os.path.join(new_dir_name, mac_dir_name, "苏晓伴桌面版帮助说明.docx"))
        shutil.copy(common_help_file, os.path.join(new_dir_name, win_dir_name, "苏晓伴桌面版帮助说明.docx"))
        shutil.copy(common_help_file, os.path.join(new_dir_name, linux_dir_name, "苏晓伴桌面版帮助说明.docx"))
        print("已复制通用帮助文档到所有平台文件夹")
    else:
        print(f"警告：通用帮助文档不存在：{common_help_file}")
    
    # Mac专用帮助文档
    mac_help_file = os.path.join(help_path, "苏晓伴 mac 版安装说明.docx")
    if os.path.exists(mac_help_file):
        shutil.copy(mac_help_file, os.path.join(new_dir_name, mac_dir_name, "苏晓伴 mac 版安装说明.docx"))
        print("已复制Mac安装说明文档")
    else:
        print(f"警告：Mac安装说明文档不存在：{mac_help_file}")
    
    # Linux专用帮助文档
    linux_help_file = os.path.join(help_path, "国产电脑使用苏晓伴说明.docx")
    if os.path.exists(linux_help_file):
        shutil.copy(linux_help_file, os.path.join(new_dir_name, linux_dir_name, "国产电脑使用苏晓伴说明.docx"))
        print("已复制Linux使用说明文档")
    else:
        print(f"警告：Linux使用说明文档不存在：{linux_help_file}")
    
    # 复制releases.json到升级包文件夹
    releases_file = os.path.join(help_path, "releases.json")
    if os.path.exists(releases_file):
        shutil.copy(releases_file, os.path.join(UPGRADE_PATH, "releases.json"))
        print("已复制releases.json到升级包文件夹")
    else:
        print(f"警告：releases.json文件不存在：{releases_file}")


# ==================== 主程序 ====================

def main():
    """
    主函数：执行文件重命名和组织流程
    """
    print("=" * 50)
    print("文件重命名和组织脚本")
    print("=" * 50)
    
    # 1. 检查pkg文件夹是否存在
    print("\n[步骤1] 检查package文件夹...")
    pkg_dirs = get_pkg_dirs(PKG_PATH)
    if not pkg_dirs:
        print("错误：当前目录中未找到pkg开头的文件夹")
        print(f"请确保在 {PKG_PATH} 目录下存在pkg开头的文件夹")
        sys.exit(1)
    print(f"找到pkg文件夹：{pkg_dirs}")
    
    # 2. 检查并处理已存在的目标文件夹
    print("\n[步骤2] 检查已存在的目标文件夹...")
    if not check_existing_target_folder():
        sys.exit(0)
    
    # 3. 设置升级包文件夹
    print("\n[步骤3] 设置升级包文件夹...")
    if not setup_upgrade_folder():
        sys.exit(0)
    
    # 4. 获取用户输入
    print("\n[步骤4] 获取用户输入...")
    version, wps_version, date = get_user_input()
    print(f"版本号：{version}, WPS版本号：{wps_version}, 日期：{date}")
    
    # 5. 创建文件夹结构
    print("\n[步骤5] 创建文件夹结构...")
    new_dir_name, mac_dir_name, win_dir_name, linux_dir_name = create_folder_structure(version, date)
    
    # 6. 提取日期后缀（后4位）
    date_suffix = date[-4:]
    
    # 7. 复制Linux文件
    print("\n[步骤6] 复制Linux平台文件...")
    copy_linux_files(PKG_PATH, new_dir_name, linux_dir_name, version, date_suffix, UPGRADE_PATH)
    
    # 8. 复制Mac文件
    print("\n[步骤7] 复制Mac平台文件...")
    copy_mac_files(PKG_PATH, new_dir_name, mac_dir_name, version, date_suffix, UPGRADE_PATH)
    
    # 9. 复制Windows文件
    print("\n[步骤8] 复制Windows平台文件...")
    copy_windows_files(PKG_PATH, new_dir_name, win_dir_name, date_suffix, UPGRADE_PATH)
    
    # 10. 复制帮助文档
    print("\n[步骤9] 复制帮助文档...")
    copy_help_documents(HELP_PATH, new_dir_name, mac_dir_name, win_dir_name, linux_dir_name)
    
    # 完成
    print("\n" + "=" * 50)
    print("所有操作完成！")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
