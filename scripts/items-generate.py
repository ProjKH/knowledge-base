import json
import os
import re
from pathlib import Path
from urllib.parse import quote

def extract_rule_name_and_path(full_name):
    # Extract name and path from 'name (path_to_file.md)' or 'name (http...)' format
    match = re.match(r'(.+?)\s*\(([^)]+)\)', full_name)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return full_name.strip(), None

def process_markdown_content(content, rule_name):
    # Remove metadata section after title
    lines = content.split('\n')
    processed_lines = []
    metadata = {}
    in_metadata = False
    found_title = False
    
    for line in lines:
        # Skip Notion icon lines
        if line.strip().startswith('<img src="https://www.notion.so/icons/'):
            continue
            
        if line.startswith('# '):
            processed_lines.append(line)
            found_title = True
            continue
            
        if found_title and line.strip() == '':
            processed_lines.append(line)
            in_metadata = True
            found_title = False
            continue
            
        if in_metadata:
            if line.strip() == '':
                in_metadata = False
            elif 'Glossary' in line:
                metadata['glossary'] = line.split(':')[1].strip()
            elif '规格' in line:
                metadata['规格'] = line.split(':')[1].strip()
            elif '类型' in line:
                metadata['类型'] = line.split(':')[1].strip()
            elif '价值' in line:
                metadata['价值'] = line.split(':')[1].strip()
            elif '设定' in line:
                # Extract rule names and convert to [name] format
                rule_names = []
                value = line.partition('设定:')[2].strip()
                for full_name in value.split(','):
                    name, _ = extract_rule_name_and_path(full_name.strip())
                    rule_names.append(f'{name}')
                metadata['设定'] = ', '.join(rule_names)
                continue
            elif ('Creator' in line) or ("carry." in line):
                continue

        processed_lines.append(line)
    
    # Process links in content
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    processed_content = []
    
    for line in processed_lines:
        matches = re.finditer(link_pattern, line)
        for match in matches:
            name, _ = match.groups()
            line = line.replace(match.group(0), f'[{name}]')
        processed_content.append(line)
    
    return '\n'.join(processed_content), metadata

def generate_metadata_table(all_metadata):
    if not all_metadata:
        return ""
    
    # Prepare table header
    table_content = ['\n\n----\n\n# 道具基础属性表\n', '| Name | Glossary | 规格 | 类型 | 价值 | 设定 |', '|------|----------|-------|-------|--------|-------|']
    
    # Sort items by name
    sorted_items = sorted(all_metadata.keys())
    
    for name in sorted_items:
        metadata = all_metadata[name]
        row = [f'[{name}]']
        
        # Add Metadata
        row.append(metadata.get('glossary', ''))
        row.append(metadata.get('规格', ''))
        row.append(metadata.get('类型', ''))
        row.append(metadata.get('价值', ''))
        row.append(metadata.get('设定', ''))

        # Join row with | and add to table
        table_content.append('|' + '|'.join(row) + '|')
    
    return '\n'.join(table_content)

def generate_link_references(links, rule_id):
    if not links:
        return ""
    
    references = ['\n']
    rules_dir = f'Rules/物品库 {rule_id}'
    
    # Sort links by name
    sorted_links = sorted(links.items(), key=lambda x: x[0])
    
    for name, path in sorted_links:
        # Add rules library path and URL encode only non-Chinese characters
        full_path = os.path.join(rules_dir, path)
        # Process each character individually
        encoded_chars = []
        for char in full_path:
            if '\u4e00' <= char <= '\u9fff':
                encoded_chars.append(char)
            else:
                encoded_chars.append(quote(char))
        encoded_path = ''.join(encoded_chars)
        references.append(f'[{name}]: {encoded_path}')
    
    return '\n'.join(references)

def main():
    # Read config.json
    with open('Items/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    rule_id = config['id']
    
    # Read CSV file
    csv_path = f'Items/物品库 {rule_id}_all.csv'
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return
    
    # Scan directory
    md_dir = f'Items/物品库 {rule_id}'
    if not os.path.exists(md_dir):
        print(f"Error: Directory {md_dir} not found")
        return
    
    # Get all markdown files and generate links
    md_files = {}
    links = {}
    for file in os.listdir(md_dir):
        if file.endswith('.md'):
            name = file.split(' ')[0]
            md_files[name] = os.path.join(md_dir, file)
            links[name] = file
    
    # Process all files and collect metadata
    all_metadata = {}
    processed_contents = []
    
    for file_name in md_files:
        with open(md_files[file_name], 'r', encoding='utf-8') as f:
            content = f.read()
            processed_content, metadata = process_markdown_content(content, file_name)
            processed_contents.append(processed_content)
            all_metadata[file_name] = metadata
    
    # Generate Items.md
    with open('Items.md', 'w', encoding='utf-8') as output:
        # Write all processed contents
        output.write('\n\n----\n\n'.join(processed_contents))
        
        # Add metadata table
        metadata_table = generate_metadata_table(all_metadata)
        if metadata_table:
            output.write(metadata_table)
        
        # Add link references
        link_references = generate_link_references(links, rule_id)
        if link_references:
            output.write(link_references)

if __name__ == '__main__':
    main()
