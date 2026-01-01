# 说明：这个改名脚本，完成了创建文件夹和改名，
# 但是改的名字还是有点问题，问题在于需要根据WPS是否存在来判断改的名称中是否需要带WPS版本号
import os
import re
import shutil

# 预置变量
path = 'E:\\auto_Project\\gerenzhushou'
now_filelist = []

# 获取当前目录下的文件夹名称中包含“pkg”开头的列表
def get_pkg_dirs(path):
    pkg_dirs = []
    for file in os.listdir(path):
        if os.path.isdir(os.path.join(path, file)) and re.match(r'^pkg.*', file):
            pkg_dirs.append(file)
    return pkg_dirs

now_filelist = get_pkg_dirs('./')
# 判断如果now_filelist为空，则提示没有找到pkg开头的文件夹，并退出程序，如果存在则打印
if not now_filelist:
    print("当前目录中未找到pkg文件夹")
    exit()

# 打印所有pkg开头的文件夹名称
print(now_filelist)

# 检查当前目录下名称包含“晓伴·灵犀_*wps_*--*”的文件夹，如果有，则退出程序，并提示“文件夹已存在”
for file in os.listdir('./'):
    if re.match(r'^灵犀·晓伴.*wps.*--.*', file):
        print("文件夹已经存在了")
        exit()

# 接收输入灵犀·晓伴的版本号，并打印
version = input("请输入灵犀·晓伴的版本号：")
# 接受输入wps的版本号，并打印
wps_version = input("请输入wps的版本号：")
# 接收输入日期
date = input("请输入日期（格式：20210101）：")

# 将两个版本号拼接成新的文件夹名称
new_dir_name = "灵犀·晓伴_"+version+" "+"wps_"+wps_version+" "+"--"+date
print("新的文件夹名称为："+new_dir_name)

# 使用new_dir_name创建文件夹
os.mkdir(new_dir_name)

# 在new_dir_name的文件夹下创建三个文件夹，首先拼接名称
mac_dir_name = "灵犀·晓伴"+" "+version+" "+"wps"+" "+wps_version+" "+"mac"
win_dir_name = "灵犀·晓伴"+" "+version+" "+"wps"+" "+wps_version+" "+"win"
linux_dir_name = "灵犀·晓伴"+" "+version+" "+"wps"+" "+wps_version+" "+"统信+麒麟"
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

# 遍历检查每个pkg开头的文件夹下是否包含名称为“灵犀·晓伴.zip”的文件



# 截取date的后四位
new_date = date[-4:]

# 开始分别从pkg开头的文件夹下复制文件并改名，最后移动到相关文件夹下
# 将文件开头为pkg-linux-arm64下的"灵犀·晓伴.zip"文件，复制到灵犀·晓伴 1.1.31 wps 1.1.6 统信+麒麟文件夹下
for file in os.listdir('./'):
    if os.path.isdir(os.path.join(path, file)) and re.match(r'^pkg-linux-arm64.*', file):

        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-linux-arm64.zip
        new_linux_arm64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-linux-arm64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(path, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, linux_dir_name, new_linux_arm64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(path, file, "灵犀·晓伴.zip"))

    if os.path.isdir(os.path.join(path, file)) and re.match(r'^pkg-linux-x64.*', file):
        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-linux-x64.zip
        new_linux_x64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-linux-x64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(path, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, linux_dir_name, new_linux_x64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(path, file, "灵犀·晓伴.zip"))

    if os.path.isdir(os.path.join(path, file)) and re.match(r'^pkg-mac-arm64.*', file):
        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-mac-arm64.zip
        new_mac_arm64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-mac-arm64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(path, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, mac_dir_name, new_mac_arm64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(path, file, "灵犀·晓伴.zip"))

    if os.path.isdir(os.path.join(path, file)) and re.match(r'^pkg-mac-x64.*', file):
        # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-mac-x64.zip
        new_mac_x64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-mac-intel-x64.zip"
        # 复制文件"灵犀·晓伴.zip"文件
        shutil.copy(os.path.join(path, file, "灵犀·晓伴.zip"), os.path.join(new_dir_name, mac_dir_name, new_mac_x64))
        # 打印文件路径
        print("复制文件成功，原文件路径：" + os.path.join(path, file, "灵犀·晓伴.zip"))

# 获取当前目录下的文件中包含“suxiaoban-*-setup.exe.zip”开头的列表
def get_suxiaoban_setup_files(path):
    suxiaoban_setup_files = []
    for winfile in os.listdir(path):
        if re.match(r'^suxiaoban-.*-setup.exe.zip', winfile):
            suxiaoban_setup_files.append(winfile)
    return suxiaoban_setup_files

# 打印所有suxiaoban-*-setup.exe.zip文件名称
print(get_suxiaoban_setup_files('./'))

# 如果get_suxiaoban_setup_files('./')不为空，则将其复制到win文件夹下
if get_suxiaoban_setup_files('./'):
    # 获取'suxiaoban-1.2.28-setup.exe.zip'中1.2.28的版本号
    win_version = re.findall(r'\d+\.\d+\.\d+', get_suxiaoban_setup_files('./')[0])[0]
    print("win版本号为：" + win_version)
    # 拼接名称，灵犀·晓伴-1.2.27-标准版-1216-win-x64.zip
    new_win_x64 = "灵犀·晓伴-" + win_version + "-标准版-" + new_date + "-win-x64.zip"
    # 复制文件"灵犀·晓伴.zip"文件
    shutil.copy(os.path.join(path, get_suxiaoban_setup_files('./')[0]), os.path.join(new_dir_name, win_dir_name, new_win_x64))
    # 打印文件路径
    print("复制文件成功，原文件路径：" + os.path.join(path, get_suxiaoban_setup_files('./')[0]))

