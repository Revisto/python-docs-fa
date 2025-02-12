import polib
import re
import sys
import os
import glob

code_patterns = [
    # Basic patterns
    r"\([^)]*،[^)]*\)",  # foo(3.0، -4.5)
    r"\[[^]]*،[^]]*\]",  # ['a'، 'b'، 'c']
    r"\{[^}]*،[^}]*\}",  # {'Sjoerd': 4127، 'Jack': 4098}
    # Function and class definitions
    r"def\s+\w+\s*\([^)]*،[^)]*\)",  # def __init__(self، name)
    r"class\s+\w+\s*\([^)]*،[^)]*\)",  # class AsyncZip(threading.Thread، file)
    r"__init__\([^)]*،[^)]*\)",  # __init__(self، realpart، imagpart)
    # Method and function calls
    r"\w+\([^)]*،[^)]*\)",  # round(Decimal('0.70')، 2)
    r"__import__\([^،]*(?:،\s*[^،)]*){0,4}\)",  # __import__('spam.ham'، globals()، locals())
    r"(?:globals|locals)\(\)،\s*(?:globals|locals)\(\)",  # globals()، locals()
    # Variable assignments and operations
    r"for\s+\w+،\s*\w+\s+in\s+",  # for a، b in table.items()
    r"print\([^)]*،[^)]*\)",  # print(a، end=' ')
    # Variable and attribute access
    r"\w+\.\w+،\s*\w+\.\w+",  # x.r، x.i
    r"(?:\w+\([^)]*\)|'[^']*'|\"[^\"]*\"|[)\]])،\s*\w+",  # os.open('mydata.db'، 'rb')
    # Dictionary operations
    r"{\s*'[^']*':\s*\w+،",  # {'primary': یک، 'secondary': دو}
    r"for\s+\w+،\s*\w+\s+in\s+\w+\.items\(\)",  # for a، b in table.items()
    r">>>.*،.*",  # >>> a، b
]


def is_code_pattern(text: str) -> bool:
    """
    Check if the text matches common code patterns
    where virgules should be converted to commas.
    """

    return any(re.search(pattern, text) for pattern in code_patterns)


def fix_virgules_in_code(entry):
    """
    Fix virgules in code sections while preserving them in regular text.
    Returns True if any changes were made.
    """
    modified = False

    # Check if original message is complete Python code
    if is_complete_python_code(entry.msgid):
        if entry.msgid != entry.msgstr and entry.msgstr != "":
            entry.msgstr = entry.msgid
            modified = True
        return modified

    # If the text appears to be code, replace virgules
    if is_code_pattern(entry.msgstr):
        new_text = entry.msgstr

        # Handle matches
        def replace_virgules(match):
            return match.group().replace("،", ",")

        # Use the same patterns from is_code_pattern
        for pattern in code_patterns:
            new_text = re.sub(pattern, replace_virgules, new_text)

        if new_text != entry.msgstr:
            entry.msgstr = new_text
            modified = True

    return modified


def is_complete_python_code(text: str) -> bool:
    """
    Check if the text is complete, runnable Python code.
    """
    if (
        len(text.split()) == 1
        and "_" not in text
        and "(" not in text
        and ")" not in text
        and "," not in text
    ):
        return False
    try:
        compile(text, "<string>", "exec")
        return True
    except SyntaxError:
        return False


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
    if os.path.isfile(path) and path.endswith(".po"):
        files.append(path)
    elif os.path.isdir(path):
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(".po"):
                    files.append(os.path.join(root, filename))
    else:
        # Handle wildcards
        for p in glob.glob(path, recursive=True):
            if os.path.isfile(p) and p.endswith(".po"):
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
        print(
            "Usage: python fix_code_virgules.py "
            "<po-file|directory|glob-pattern> [additional paths...]"
        )
        sys.exit(1)
    main(sys.argv[1:])
