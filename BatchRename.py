import os
import re
import argparse

def batch_rename(directory, prefix='', suffix='', replace_from='', replace_to='', 
                sequence=False, recursive=False, preview=False):
    """
    批量重命名文件
    
    参数:
        directory: 要处理的目录路径
        prefix: 要添加的前缀
        suffix: 要添加的后缀
        replace_from: 要替换的字符串
        replace_to: 替换成的字符串
        sequence: 是否按序号重命名
        recursive: 是否递归处理子目录
        preview: 是否只预览不执行
    """
    renamed_files = 0
    
    for root, dirs, files in os.walk(directory):
        if not recursive and root != directory:
            continue
            
        for index, filename in enumerate(files, start=1):
            # 获取文件扩展名和基本名
            base, ext = os.path.splitext(filename)
            
            # 构建新文件名
            new_base = base
            
            # 替换字符串
            if replace_from:
                new_base = new_base.replace(replace_from, replace_to)
            
            # 添加前缀
            if prefix:
                new_base = f"{prefix}{new_base}"
            
            # 添加后缀
            if suffix:
                new_base = f"{new_base}{suffix}"
            
            # 按序号重命名
            if sequence:
                new_base = f"{index}"
            
            # 构建完整的新文件名
            new_filename = f"{new_base}{ext}"
            
            # 如果新旧文件名相同则跳过
            if new_filename == filename:
                continue
            
            # 构建完整路径
            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_filename)
            
            # 打印改名操作
            print(f"重命名: {filename} -> {new_filename}")
            
            # 如果不是预览模式则执行改名
            if not preview:
                try:
                    os.rename(old_path, new_path)
                    renamed_files += 1
                except Exception as e:
                    print(f"错误: 无法重命名 {filename}: {str(e)}")
    
    print(f"\n操作完成。共重命名 {renamed_files} 个文件")

def main():
    parser = argparse.ArgumentParser(description='批量文件重命名工具')
    parser.add_argument('directory', help='要处理的目录路径')
    parser.add_argument('--prefix', default='', help='要添加的前缀')
    parser.add_argument('--suffix', default='', help='要添加的后缀')
    parser.add_argument('--replace-from', default='', help='要替换的字符串')
    parser.add_argument('--replace-to', default='', help='替换成的字符串')
    parser.add_argument('--sequence', action='store_true', help='按序号重命名')
    parser.add_argument('--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('--preview', action='store_true', help='只预览不执行')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"错误: 目录 {args.directory} 不存在")
        return
    
    batch_rename(
        directory=args.directory,
        prefix=args.prefix,
        suffix=args.suffix,
        replace_from=args.replace_from,
        replace_to=args.replace_to,
        sequence=args.sequence,
        recursive=args.recursive,
        preview=args.preview
    )

if __name__ == '__main__':
    main()
