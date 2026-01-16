# 说明：这个改名脚本，完成了创建文件夹和改名，添加了帮助文档的功能
# 但是改的名字还是有点问题，问题在于需要根据WPS是否存在来判断改的名称中是否需要带WPS版本号
# 新增了对升级包的改名
# 20251230更新：将预置路径改为了相对路径
# 20250102更新：判断pkg文件夹是否存在，如果不存在则提示没有找到pkg文件夹，并退出程序，如果存在则打印
# 20250102更新：检查当前目录下名称包含“灵犀·晓伴_*--*”的文件夹，如果有，则提示“文件夹已存在”，并询问用户是否删除整个文件夹
import os
import re
import shutil

# 预置路径
path = './'
helppath = './help_documentation'
uppath = './upgrade_package'
pkgpath = './package'

# 申明变量
# now_filelist = []

# 获取当前目录下的文件夹名称中包含“pkg”开头的列表
def get_pkg_dirs(path):
    pkg_dirs = []
    for file in os.listdir(path):
        if os.path.isdir(os.path.join(path, file)) and re.match(r'^pkg.*', file):
            pkg_dirs.append(file)
    return pkg_dirs

now_filelist = get_pkg_dirs('./package')
# 判断如果now_filelist为空，则提示没有找到pkg开头的文件夹，并退出程序，如果存在则打印
if not now_filelist:
    print("当前目录中未找到pkg文件夹")
    exit()

# 打印所有pkg开头的文件夹名称
print("所有pkg开头的文件夹名称为：" + str(now_filelist))

# 检查当前目录下名称包含“灵犀·晓伴_*--*”的文件夹，如果有，则退出程序，并提示“文件夹已存在”
for file in os.listdir('./'):
    if re.match(r'^灵犀·晓伴.*--.*', file):
        print("文件夹已经存在了")
        # 询问用户是否删除整个文件夹
        print("是否删除整个文件夹？ 1. 删除 or 2. 不删除")
        choice = input("请输入你的选择：")
        if choice == "1":
            try:
                # 使用管理员权限删除文件夹
                import subprocess
                subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', file], shell=True)
                print(f"已成功删除文件夹: {file}")
            except PermissionError as e:
                print(f"删除文件夹时发生权限错误: {e}")
                exit(1)
            except Exception as e:
                print(f"删除文件夹时发生错误: {e}")
                exit(1)
        elif choice == "2":
            exit()

# 检查upgrade_package文件夹是否存在，如果不存在则创建，如果存在则提示已存在，则询问用户是否清空这个文件夹的所有内容
if not os.path.exists(uppath):
    os.mkdir(uppath)
    print("upgrade_package文件夹创建成功！")
else:
    print("upgrade_package文件夹已存在！")
    print("是否清空upgrade_package文件夹的所有内容？1. 清空 or 2. 不清空")
    choice = input("请输入你的选择：")
    if choice == "1":
        try:
            # 使用管理员权限清空文件夹内容
            import subprocess
            subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', 'upgrade_package'], shell=True)
            os.mkdir(uppath)
            print(f"已成功清空文件夹: {uppath}")
        except PermissionError as e:
            print(f"删除文件夹时发生权限错误: {e}")
    elif choice == "2":
        exit(1)

# 接收输入灵犀·晓伴的版本号，并打印
version = input("请输入灵犀·晓伴的版本号：")
# 接受输入wps的版本号，并打印
wps_version = input("请输入wps的版本号：")
# 接收输入日期
date = input("请输入日期（格式：20210101）：")

# 将两个版本号拼接成新的文件夹名称
new_dir_name = "灵犀·晓伴_"+version+" "+"--"+date
print("新的文件夹名称为："+new_dir_name)

# 使用new_dir_name创建文件夹
os.mkdir(new_dir_name)

# 在new_dir_name的文件夹下创建三个文件夹，首先拼接名称
mac_dir_name = "灵犀·晓伴"+" "+version+" "+"mac"
win_dir_name = "灵犀·晓伴"+" "+version+" "+"win"
linux_dir_name = "灵犀·晓伴"+" "+version+" "+"统信+麒麟"
# 打印文件夹名称
print("mac文件夹名称为："+mac_dir_name)
print("win文件夹名称为："+win_dir_name)
print("linux文件夹名称为："+linux_dir_name)

# 在new_dir_name的文件夹下创建三个名称的文件夹
os.mkdir(os.path.join(new_dir_name, mac_dir_name))
os.mkdir(os.path.join(new_dir_name, win_dir_name))
os.mkdir(os.path.join(new_dir_name, linux_dir_name))

# 打印创建成功的提示信息
print("mac文件夹创建成功！")
print("win文件夹创建成功！")
print("linux文件夹创建成功！")

# 截取date的后四位
new_date = date[-4:]

# 开始分别从pkg开头的文件夹下复制文件并改名，最后移动到相关文件夹下
# 将文件开头为pkg-linux-arm64下的"灵犀·晓伴.zip"文件，复制到灵犀·晓伴 1.1.31 wps 1.1.6 统信+麒麟文件夹下
for file in os.listdir(pkgpath):
    if os.path.isdir(os.path.join(pkgpath, file)) and re.match(r'^pkg-linux-arm64.*', file):

        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-linux-arm64.zip
        new_linux_arm64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-linux-arm64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, linux_dir_name, new_linux_arm64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(pkgpath, file, "灵犀·晓伴.zip"))
        # 拼接名称gerenzhushou-1.2.27-standard-linux-arm64
        new2_linux_arm64 = "gerenzhushou-" + version + "-standard-linux-arm64.zip"
        # 复制文件"灵犀·晓伴.zip"文件到uppath文件夹下
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(uppath, new2_linux_arm64))

    if os.path.isdir(os.path.join(pkgpath, file)) and re.match(r'^pkg-linux-x64.*', file):
        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-linux-x64.zip
        new_linux_x64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-linux-x64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, linux_dir_name, new_linux_x64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(pkgpath, file, "灵犀·晓伴.zip"))
        # 拼接名称gerenzhushou-1.2.27-standard-linux-x64
        new2_linux_x64 = "gerenzhushou-" + version + "-standard-linux-x64.zip"
        # 复制文件"灵犀·晓伴.zip"文件到uppath文件夹下
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(uppath, new2_linux_x64))

    if os.path.isdir(os.path.join(pkgpath, file)) and re.match(r'^pkg-mac-arm64.*', file):
        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-mac-arm64.zip
        new_mac_arm64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-mac-arm64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, mac_dir_name, new_mac_arm64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(pkgpath, file, "灵犀·晓伴.zip"))
        # 拼接名称gerenzhushou-1.2.27-standard-darwin-arm64
        new2_mac_arm64 = "gerenzhushou-" + version + "-standard-darwin-arm64.zip"
        # 复制文件"灵犀·晓伴.zip"文件到uppath文件夹下
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(uppath, new2_mac_arm64))

    if os.path.isdir(os.path.join(pkgpath, file)) and re.match(r'^pkg-mac-x64.*', file):
        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-mac-x64.zip
        new_mac_x64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-mac-intel-x64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, mac_dir_name, new_mac_x64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(pkgpath, file, "灵犀·晓伴.zip"))
        # 拼接名称gerenzhushou-1.2.27-standard-darwin-x64
        new2_mac_x64 = "gerenzhushou-" + version + "-standard-darwin-x64.zip"
        # 复制文件"灵犀·晓伴.zip"文件到uppath文件夹下
        shutil.copy(os.path.join(pkgpath, file, "灵犀·晓伴.zip"), os.path.join(uppath, new2_mac_x64))

# 获取当前目录下的文件中包含“suxiaoban-*-setup.exe.zip”开头的列表
def get_suxiaoban_setup_files(path):
    suxiaoban_setup_files = []
    for winfile in os.listdir(path):
        if re.match(r'^suxiaoban-.*-setup.exe.zip', winfile):
            suxiaoban_setup_files.append(winfile)
    return suxiaoban_setup_files

# 打印所有suxiaoban-*-setup.exe.zip文件名称
print(get_suxiaoban_setup_files(pkgpath))

# 如果get_suxiaoban_setup_files('./')不为空，则将其复制到win文件夹下
if get_suxiaoban_setup_files(pkgpath):
    # 获取'suxiaoban-1.2.28-setup.exe.zip'中1.2.28的版本号
    win_version = re.findall(r'\d+\.\d+\.\d+', get_suxiaoban_setup_files(pkgpath)[0])[0]
    print("win版本号为：" + win_version)
    # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-win-x64.zip
    new_win_x64 = "灵犀·晓伴-" + win_version + "-标准版-" + new_date + "-win-x64.zip"
    # 复制文件"灵犀·晓伴.zip"文件
    print(os.path.join(pkgpath, get_suxiaoban_setup_files(pkgpath)[0]))
    shutil.copy(os.path.join(pkgpath, get_suxiaoban_setup_files(pkgpath)[0]), os.path.join(new_dir_name, win_dir_name, new_win_x64))
    # 打印文件路径
    print("复制文件成功，原文件路径：" + os.path.join(pkgpath, get_suxiaoban_setup_files(pkgpath)[0]))
    # 拼接名称gerenzhushou-1.2.27-standard-win32-x64
    new2_win_x64 = "gerenzhushou-" + win_version + "-standard-win32-x64.zip"
    # 复制文件"灵犀·晓伴.zip"文件到uppath文件夹下
    shutil.copy(os.path.join(pkgpath, get_suxiaoban_setup_files(pkgpath)[0]), os.path.join(uppath, new2_win_x64))

# 将help_documentation路径下的帮助说明文档“苏晓伴桌面版帮助说明.docx”分别复制到mac_dir_name和win_dir_name和linux_dir_name三个文件夹下
shutil.copy(os.path.join(helppath, "苏晓伴桌面版帮助说明.docx"), os.path.join(new_dir_name, mac_dir_name, "苏晓伴桌面版帮助说明.docx"))
shutil.copy(os.path.join(helppath, "苏晓伴桌面版帮助说明.docx"), os.path.join(new_dir_name, win_dir_name, "苏晓伴桌面版帮助说明.docx"))
shutil.copy(os.path.join(helppath, "苏晓伴桌面版帮助说明.docx"), os.path.join(new_dir_name, linux_dir_name, "苏晓伴桌面版帮助说明.docx"))

# 将help_documentation路径下的帮助说明文档“苏晓伴 mac 版安装说明.docx”复制到mac_dir_name文件夹下
shutil.copy(os.path.join(helppath, "苏晓伴 mac 版安装说明.docx"), os.path.join(new_dir_name, mac_dir_name, "苏晓伴 mac 版安装说明.docx"))

# 将help_documentation路径下的帮助说明文档“国产电脑使用苏晓伴说明.docx”复制到linux_dir_name文件夹下
shutil.copy(os.path.join(helppath, "国产电脑使用苏晓伴说明.docx"), os.path.join(new_dir_name, linux_dir_name, "国产电脑使用苏晓伴说明.docx"))

# 将help_documentation路径下“releases.json”文件，复制到uppath路径下
shutil.copy(os.path.join(helppath, "releases.json"), os.path.join(uppath, "releases.json"))







