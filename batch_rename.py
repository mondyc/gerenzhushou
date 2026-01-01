#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用批量文件重命名工具
支持功能：
1. 添加前缀/后缀
2. 替换特定字符
3. 按序号重命名
4. 正则表达式替换
5. 递归处理子目录
6. 预览模式
"""

import os
import re
import argparse
from typing import List

def get_files(directory: str, recursive: bool = False, ext_filter: str = None) -> List[str]:
    """获取目录下的文件列表"""
    file_list = []
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if ext_filter and not file.endswith(ext_filter):
                    continue
                file_list.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                if ext_filter and not file.endswith(ext_filter):
                    continue
                file_list.append(file_path)
    return file_list

def generate_new_name(file_path: str, args) -> str:
    """生成新文件名"""
    dirname, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    
    # 应用各种改名规则
    new_name = name
    
    if args.replace:
        new_name = new_name.replace(args.replace[0], args.replace[1])
    
    if args.regex:
        new_name = re.sub(args.regex[0], args.regex[1], new_name)
    
    if args.prefix:
        new_name = args.prefix + new_name
    
    if args.suffix:
        new_name = new_name + args.suffix
    
    if args.numbering:
        global counter
        new_name = f"{counter:0{args.digits}d}_{new_name}"
        counter += 1
    
    return os.path.join(dirname, new_name + ext)

def main():
    parser = argparse.ArgumentParser(description="通用批量文件重命名工具")
    parser.add_argument("directory", help="要处理的目录路径")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归处理子目录")
    parser.add_argument("-e", "--ext", help="文件扩展名过滤器(如:.txt)")
    
    # 改名模式
    group = parser.add_argument_group("改名模式")
    group.add_argument("--prefix", help="添加前缀")
    group.add_argument("--suffix", help="添加后缀")
    group.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"), 
                      help="替换字符串 OLD 为 NEW")
    group.add_argument("--regex", nargs=2, metavar=("PATTERN", "REPL"), 
                      help="使用正则表达式替换")
    group.add_argument("-n", "--numbering", action="store_true", 
                      help="按序号重命名")
    group.add_argument("-d", "--digits", type=int, default=3,
                      help="序号位数(默认:3)")
    
    # 其他选项
    parser.add_argument("-p", "--preview", action="store_true",
                       help="预览模式(不实际执行重命名)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="显示详细信息")
    
    args = parser.parse_args()
    
    if not any([args.prefix, args.suffix, args.replace, args.regex, args.numbering]):
        parser.error("至少需要指定一种改名模式")
    
    global counter
    counter = 1
    
    try:
        file_list = get_files(args.directory, args.recursive, args.ext)
        if not file_list:
            print("没有找到符合条件的文件")
            return
        
        print(f"找到 {len(file_list)} 个文件")
        
        for file_path in file_list:
            new_path = generate_new_name(file_path, args)
            
            if args.verbose or args.preview:
                print(f"{file_path} -> {new_path}")
            
            if not args.preview:
                os.rename(file_path, new_path)
        
        if args.preview:
            print("\n预览模式: 未实际执行重命名操作")
        else:
            print("\n重命名操作完成")
    
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
