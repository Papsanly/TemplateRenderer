#!/usr/bin/env python3
"""
Switch certificate templates between Christmas and Default themes.

Usage:
    python scripts/switch_theme.py christmas  # Enable Christmas theme
    python scripts/switch_theme.py default    # Disable Christmas theme (neutral)
    python scripts/switch_theme.py default --dry-run  # Show what would change without applying
"""

import os
import re
import sys
from pathlib import Path

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "renderer", "templates")

TEMPLATE_FILES = [
    "wefly_certificate.html",
    "wefly_certificate_f1.html",
    "wefly_certificate_a4.html",
    "wefly_certificate_a4_f1.html",
]


def comment_christmas_block(content: str) -> str:
    """Comment out content between CHRISTMAS_START and CHRISTMAS_END markers."""
    pattern = r"(  <!-- CHRISTMAS_START -->\n)(.*?)(  <!-- CHRISTMAS_END -->)"

    def replace_func(match):
        start_marker = match.group(1)
        block_content = match.group(2)
        end_marker = match.group(3)

        # Check if already commented
        if "<!-- DISABLED" in block_content:
            return match.group(0)

        # Comment out the entire block
        lines = block_content.split("\n")
        commented_lines = ["  <!-- DISABLED"]
        for line in lines:
            if line.strip():  # Only add non-empty lines
                commented_lines.append(line)
        commented_lines.append("  -->")

        return start_marker + "\n".join(commented_lines) + "\n" + end_marker

    return re.sub(pattern, replace_func, content, flags=re.DOTALL)


def uncomment_christmas_block(content: str) -> str:
    """Uncomment content between CHRISTMAS_START and CHRISTMAS_END markers."""
    pattern = r"(  <!-- CHRISTMAS_START -->\n)  <!-- DISABLED\n(.*?)\n  -->\n(  <!-- CHRISTMAS_END -->)"

    def replace_func(match):
        start_marker = match.group(1)
        block_content = match.group(2)
        end_marker = match.group(3)

        return start_marker + block_content + "\n" + end_marker

    return re.sub(pattern, replace_func, content, flags=re.DOTALL)


def show_diff(filename: str, old_content: str, new_content: str):
    """Show simple diff of changes."""
    if old_content == new_content:
        print(f"  ✓ {filename}: No changes needed")
        return False

    print(f"  → {filename}: Changes detected")
    old_lines = old_content.split("\n")
    new_lines = new_content.split("\n")

    changes = 0
    for i, (old, new) in enumerate(zip(old_lines, new_lines), 1):
        if old != new:
            changes += 1
            if changes <= 3:  # Show first 3 changes
                print(f"    Line {i}:")
                if old.strip():
                    print(f"      - {old[:80]}")
                if new.strip():
                    print(f"      + {new[:80]}")

    if changes > 3:
        print(f"    ... and {changes - 3} more changes")

    return True


def switch_theme(theme: str, dry_run: bool = False) -> None:
    """Switch all templates to the specified theme."""
    if theme not in ("christmas", "default"):
        print(f"Error: Unknown theme '{theme}'. Use 'christmas' or 'default'.")
        sys.exit(1)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Switching to theme: {theme}\n")

    changed_files = 0

    for template_file in TEMPLATE_FILES:
        filepath = os.path.join(TEMPLATES_DIR, template_file)

        if not os.path.exists(filepath):
            print(f"  ⚠ Warning: Template not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if theme == "christmas":
            new_content = uncomment_christmas_block(content)
        else:
            new_content = comment_christmas_block(content)

        has_changes = show_diff(template_file, content, new_content)

        if has_changes:
            changed_files += 1
            if not dry_run:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

    print(f"\n{'Would change' if dry_run else 'Changed'} {changed_files} file(s)")

    if dry_run and changed_files > 0:
        print("\nTo apply changes, run without --dry-run flag")
    elif not dry_run and changed_files > 0:
        print(f"✓ Theme switched to: {theme}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/switch_theme.py <christmas|default> [--dry-run]")
        sys.exit(1)

    theme = sys.argv[1].lower()
    dry_run = "--dry-run" in sys.argv

    switch_theme(theme, dry_run)


if __name__ == "__main__":
    main()
