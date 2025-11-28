"""Module for generating directory tree structures with filtering capabilities."""

import fnmatch
from pathlib import Path


def print_directory_tree(start_path=".", ignore_patterns=None, indent="", prefix=""):
    """
    Generate a directory tree structure from the specified path, ignoring provided patterns.

    Args:
        start_path: Root directory to start from (default: current directory)
        ignore_patterns: List of filename patterns to ignore
        indent: Current indentation level (used internally for recursion)
        prefix: Prefix for the current line (used internally for recursion)

    Returns:
        String representation of the directory tree

    Raises:
        OSError: If there are problems accessing the directory structure
    """
    if ignore_patterns is None:
        ignore_patterns = []

    start_path = Path(start_path).resolve()
    items = []

    try:
        for item in start_path.iterdir():
            should_ignore = False
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(item.name, pattern) or (
                    item.is_dir() and pattern in item.name
                ):
                    should_ignore = True
                    break
            if not should_ignore:
                items.append(item)
    except OSError as e:
        return f"{indent}{prefix}⚠ Error reading directory: {e}"

    items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
    lines = []

    for index, item in enumerate(items):
        is_last = index == len(items) - 1
        connector = "└── " if is_last else "├── "
        line = f"{indent}{prefix}{connector}{item.name}"
        lines.append(line)

        if item.is_dir():
            new_prefix = "    " if is_last else "│   "
            sub_tree = print_directory_tree(
                start_path=item,
                ignore_patterns=ignore_patterns,
                indent=indent + new_prefix,
                prefix="",
            )
            lines.extend(sub_tree.splitlines())

    return "\n".join(lines)


def main():
    """Main function to demonstrate directory tree generation."""
    # Examples of patterns to ignore
    ignore_patterns = [
        "*.pyc",  # Ignore .pyc files
        "__pycache__",  # Ignore __pycache__ directory
        "venv",  # Ignore venv directory
        ".git",  # Ignore .git directory
        "node_modules",  # Ignore node_modules directory
        "*.log",  # Ignore log files
        ".pytest_cache",  # Ignore pytest cache directory
        ".vscode",  # Ignore VSCode configuration directory
        "htmlcov",  # Ignore HTML coverage directory
    ]

    try:
        print(f"Directory tree for: {Path('.').resolve()}")
        print(print_directory_tree(ignore_patterns=ignore_patterns))
    except OSError as e:
        print(f"Error generating directory tree: {e}")


if __name__ == "__main__":
    main()
