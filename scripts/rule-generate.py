import json
import os
import re
from pathlib import Path
from urllib.parse import quote

def extract_rule_name_and_path(full_name):
    # Extract name and path from 'name (path_to_file.md)' format
    match = re.match(r'(.+?)\s*\((.+?)\)', full_name)
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
                continue
                
            if 'Rules' in line:
                metadata['rules'] = line.split(':')[1].strip()
            elif 'Glossary' in line:
                metadata['glossary'] = line.split(':')[1].strip()
            elif '所属规则' in line:
                # Extract rule names and convert to [name] format
                rule_names = []
                for full_name in line.split(':')[1].split(','):
                    name, _ = extract_rule_name_and_path(full_name.strip())
                    rule_names.append(f'[{name}]')
                metadata['parent_rules'] = rule_names
            elif '内含规则' in line:
                # Extract rule names and convert to [name] format
                rule_names = []
                for full_name in line.split(':')[1].split(','):
                    name, _ = extract_rule_name_and_path(full_name.strip())
                    rule_names.append(f'[{name}]')
                metadata['child_rules'] = rule_names
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
    table_content = ['\n\n----\n\n# 规则关系表\n', '| Name | Glossary | Rules | 所属规则 | 内含规则 |', '|------|----------|-------|----------|----------|']
    
    # Sort rules by name
    sorted_rules = sorted(all_metadata.keys())
    
    for rule_name in sorted_rules:
        metadata = all_metadata[rule_name]
        row = [f'[{rule_name}]']
        
        # Add Glossary
        row.append(metadata.get('glossary', ''))
        
        # Add Rules
        row.append(metadata.get('rules', ''))
        
        # Add Parent Rules
        parent_rules = metadata.get('parent_rules', [])
        row.append(', '.join(parent_rules))
        
        # Add Child Rules
        child_rules = metadata.get('child_rules', [])
        row.append(', '.join(child_rules))
        
        # Join row with | and add to table
        table_content.append('|' + '|'.join(row) + '|')
    
    return '\n'.join(table_content)

def generate_link_references(links, rule_id):
    if not links:
        return ""
    
    references = ['\n']
    rules_dir = f'Rules/规则库 {rule_id}'
    
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
    # Read positions_order.json
    with open('Rules/positions_order.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    rule_id = config['id']
    positions_order = config['positions_order']
    
    # Read CSV file
    csv_path = f'Rules/规则库 {rule_id}.csv'
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return
    
    # Scan rules directory
    rules_dir = f'Rules/规则库 {rule_id}'
    if not os.path.exists(rules_dir):
        print(f"Error: Rules directory {rules_dir} not found")
        return
    
    # Get all markdown files and generate links
    md_files = {}
    links = {}
    for file in os.listdir(rules_dir):
        if file.endswith('.md'):
            name = file.split(' ')[0]
            md_files[name] = os.path.join(rules_dir, file)
            links[name] = file
    
    # Process all files and collect metadata
    all_metadata = {}
    processed_contents = []
    
    for position in positions_order:
        if position in md_files:
            with open(md_files[position], 'r', encoding='utf-8') as f:
                content = f.read()
                processed_content, metadata = process_markdown_content(content, position)
                processed_contents.append(processed_content)
                all_metadata[position] = metadata
        else:
            print(f"Warning: No markdown file found for position {position}")
    
    # Generate GameRules.md
    with open('GameRules.md', 'w', encoding='utf-8') as output:
        # Write all processed contents
        output.write('\n\n'.join(processed_contents))
        
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
