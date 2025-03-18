import os
import re
from pathlib import Path
import argparse

def process_content(content):
    # 替换 Notion 链接格式为加粗文本
    # 匹配格式: [name](https://www.notion.so/任意字符) 或者 [name](任意字符.md)
    pattern = r'\[([^\]]+)\]\((https://www.notion.so/[^\)]+)\)|\[([^\]]+)\]\(([^\.]+\.md)\)'
    rep = re.sub(pattern, r'**\1**', content)
    # 调整首行标题 # 标题 为 ## 标题
    rep = re.sub(r'^#', r'##', rep, count=1, flags=re.MULTILINE)
    # 调整 {{f|name}} 为 `name`
    rep = re.sub(r'\{\{f\|([^\}]+)\}\}', r'`\1`', rep)
    return rep

def merge_md_files(features_dir, output_file):
    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 获取所有 md 文件并排序
    md_files = sorted([f for f in features_dir.glob('*.md')])
    
    # 合并内容
    with output_file.open('w', encoding='utf-8') as outfile:
        # 写入标题
        outfile.write(f'# {features_dir.name}\n\n')

        for i, md_file in enumerate(md_files):
            # 读取并处理内容
            with md_file.open('r', encoding='utf-8') as infile:
                content = infile.read()
                processed_content = process_content(content)
                
            # 写入处理后的内容
            outfile.write(processed_content)
            
            # 如果不是最后一个文件，添加分隔符
            if i < len(md_files) - 1:
                outfile.write('\n\n---\n\n')

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='Merge markdown files from directories')
    parser.add_argument('dirs', help='Comma-separated list of directories to process')
    
    args = parser.parse_args()
    
    # 设置路径
    current_dir = Path.cwd()
    dir_list = [d.strip() for d in args.dirs.split(',')]
    
    # 执行合并
    for dir_name in dir_list:
        features_dir = current_dir / dir_name
        output_file = current_dir / f'{dir_name}.md'
        if features_dir.exists():
            merge_md_files(features_dir, output_file)
            print(f'Successfully merged files from {dir_name} into {output_file}')
        else:
            print(f'Directory {dir_name} does not exist, skipping...')

if __name__ == '__main__':
    main()