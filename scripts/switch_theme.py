#!/usr/bin/env python3
"""
Switch certificate templates between Christmas and Default themes.

Usage:
    python scripts/switch_theme.py christmas  # Enable Christmas theme
    python scripts/switch_theme.py default    # Disable Christmas theme (neutral)
"""

import os
import re
import sys

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "renderer", "templates")

TEMPLATE_FILES = [
    "wefly_certificate.html",
    "wefly_certificate_f1.html",
    "wefly_certificate_a4.html",
    "wefly_certificate_a4_f1.html",
]


def comment_christmas_block(content: str) -> str:
    """Comment out content between CHRISTMAS_START and CHRISTMAS_END markers."""
    pattern = r"(<!-- CHRISTMAS_START -->)\n(.*?)(<!-- CHRISTMAS_END -->)"

    def replace_func(match):
        start_marker = match.group(1)
        block_content = match.group(2)
        end_marker = match.group(3)

        # Check if already commented
        if "<!-- COMMENTED" in block_content:
            return match.group(0)

        # Comment out each line in the block
        lines = block_content.split("\n")
        commented_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("<!--"):
                # Wrap in comment
                commented_lines.append(f"<!-- COMMENTED {line} -->")
            else:
                commented_lines.append(line)

        return f"{start_marker}\n" + "\n".join(commented_lines) + f"{end_marker}"

    return re.sub(pattern, replace_func, content, flags=re.DOTALL)


def uncomment_christmas_block(content: str) -> str:
    """Uncomment content between CHRISTMAS_START and CHRISTMAS_END markers."""
    pattern = r"(<!-- CHRISTMAS_START -->)\n(.*?)(<!-- CHRISTMAS_END -->)"

    def replace_func(match):
        start_marker = match.group(1)
        block_content = match.group(2)
        end_marker = match.group(3)

        # Uncomment each line in the block
        lines = block_content.split("\n")
        uncommented_lines = []
        for line in lines:
            # Remove COMMENTED wrapper
            uncommented = re.sub(r"<!-- COMMENTED (.*?) -->", r"\1", line)
            uncommented_lines.append(uncommented)

        return f"{start_marker}\n" + "\n".join(uncommented_lines) + f"{end_marker}"

    return re.sub(pattern, replace_func, content, flags=re.DOTALL)


def switch_theme(theme: str) -> None:
    """Switch all templates to the specified theme."""
    if theme not in ("christmas", "default"):
        print(f"Error: Unknown theme '{theme}'. Use 'christmas' or 'default'.")
        sys.exit(1)

    for template_file in TEMPLATE_FILES:
        filepath = os.path.join(TEMPLATES_DIR, template_file)

        if not os.path.exists(filepath):
            print(f"Warning: Template not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if theme == "christmas":
            new_content = uncomment_christmas_block(content)
        else:
            new_content = comment_christmas_block(content)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Updated: {template_file}")

    print(f"\nTheme switched to: {theme}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/switch_theme.py <christmas|default>")
        sys.exit(1)

    theme = sys.argv[1].lower()
    switch_theme(theme)


if __name__ == "__main__":
    main()
