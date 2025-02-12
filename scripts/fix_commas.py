import polib
import re
import sys
import os
import glob

def is_code_pattern(text: str) -> bool:
    """
    Check if the text matches common code patterns where virgules should be converted to commas.
    """
    code_patterns = [
        r'\([^)]*،[^)]*\)',  # Function calls with params: foo(a، b)
        r'\[[^]]*،[^]]*\]',  # List literals: [1، 2، 3]
        r'def\s+\w+\s*\([^)]*،[^)]*\)', # Function definitions
        r'class\s+\w+\s*\([^)]*،[^)]*\)', # Class definitions
        r'\{[^}]*،[^}]*\}',  # Dict literals
    ]
    
    return any(re.search(pattern, text) for pattern in code_patterns)

def fix_virgules_in_code(entry):
    """
    Fix virgules in code sections while preserving them in regular text.
    Returns True if any changes were made.
    """
    if not isinstance(entry.msgstr, str):
        return False
        
    modified = False
    
    # If the text appears to be code, replace virgules
    if is_code_pattern(entry.msgstr):
        new_text = entry.msgstr
        
        # Handle parentheses content
        def replace_in_parens(match):
            return match.group().replace('،', ',')
            
        # Replace virgules in various code patterns
        patterns_and_replacements = [
            (r'\([^)]+\)',  replace_in_parens),  # Function params
            (r'\[[^]]+\]',  replace_in_parens),  # List literals
            (r'\'[^\']+\'', replace_in_parens),  # Single quoted strings
            (r'"[^"]+"',    replace_in_parens),  # Double quoted strings
            (r'\{[^}]+\}',  replace_in_parens),  # Dict literals
        ]
        
        for pattern, replacement in patterns_and_replacements:
            new_text = re.sub(pattern, replacement, new_text)
            
        if new_text != entry.msgstr:
            entry.msgstr = new_text
            modified = True
            
    return modified

def process_po_file(po_file):
    """Process a single PO file."""
    try:
        po = polib.pofile(po_file)
        fixed_entries = 0
        
        for entry in po:
            if fix_virgules_in_code(entry):
                fixed_entries += 1
                
        if fixed_entries > 0:
            po.save()
            print(f"Fixed {fixed_entries} entries in {po_file}")
            
    except Exception as e:
        print(f"Error processing {po_file}: {e}")

def collect_po_files(path):
    """
    Given a path (wildcard, file, or directory), return a list of .po files.
    """
    files = []
    if os.path.isfile(path) and path.endswith('.po'):
        files.append(path)
    elif os.path.isdir(path):
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith('.po'):
                    files.append(os.path.join(root, filename))
    else:
        # Handle wildcards
        for p in glob.glob(path, recursive=True):
            if os.path.isfile(p) and p.endswith('.po'):
                files.append(p)
    return files

def main(paths):
    processed_files = set()
    for path in paths:
        for po_file in collect_po_files(path):
            if po_file not in processed_files:
                process_po_file(po_file)
                processed_files.add(po_file)
    
    if not processed_files:
        print("No PO files found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_code_virgules.py <po-file|directory|glob-pattern> [additional paths...]")
        sys.exit(1)
    main(sys.argv[1:])