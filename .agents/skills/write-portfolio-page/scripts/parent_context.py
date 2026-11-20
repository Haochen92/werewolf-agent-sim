"""Print what a reader has already read before arriving on a portfolio page.

A Level 2 page is reached from its chapter page. A Level 3 page may be reached directly from
a self-contained chapter or from a Level 2 subject. The conventional parent is the named page
in the same directory, or the named page one directory above for a nested subject. The reader has read the parent's introduction and
the parent section that links here, so the cold editorial review treats that text as known context.

Usage: python3 parent_context.py <page.md>
"""
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{2,6}) ")


def main(page: Path) -> None:
    parent, link_target = find_parent(page)
    if parent is None:
        print("(No conventional parent page found. Treat this page as opened directly.)")
        return

    lines = page_copy_lines(parent)
    link_index = next((i for i, line in enumerate(lines)
                       if f"]({link_target})" in line or f"]({link_target}#" in line), None)
    if link_index is None:
        print(f"(The parent page {parent.name} does not link to this page. "
              "Treat it as opened directly.)")
        return

    section_start, level = heading_above(lines, link_index)
    section_end = next((i for i in range(link_index + 1, len(lines))
                        if (m := HEADING.match(lines[i])) and len(m.group(1)) <= level), len(lines))
    intro_end = next((i for i, line in enumerate(lines)
                      if (m := HEADING.match(line)) and len(m.group(1)) == level), section_start)

    print(f"Parent page: {parent.name}\n")
    print("--- The parent's introduction ---\n")
    print("\n".join(lines[:intro_end]).strip())
    print("\n--- The parent's section that links to this page ---\n")
    print("\n".join(lines[section_start:section_end]).strip())


def find_parent(page: Path):
    """Return (parent page, link text the parent uses for this page), or (None, None)."""
    stem = re.sub(r"\.skill(_\d+)?$", "", page.stem)  # trial copies: <stem>.skill.md, <stem>.skill_2.md
    folder = page.parent
    if stem == folder.name:  # Level 2: <chapter>/<subject>/<subject>.md
        parent = folder.parent / f"{folder.parent.name}.md"
        return (parent, f"{folder.name}/{stem}.md") if parent.exists() else (None, None)
    parent = folder / f"{folder.name}.md"  # Level 3: beside its Level 2 page
    if parent.exists() and parent != page:
        return parent, f"{stem}.md"
    return None, None


def page_copy_lines(path: Path) -> list[str]:
    """The parent's reader-facing text: after its page-copy marker, without HTML comments."""
    text = re.sub(r"<!--.*?-->", "", path.read_text(), flags=re.S)
    marker = re.search(r"^## (Page copy|Level 1)[^\n]*$", text, flags=re.M)
    return (text[marker.end():] if marker else text).splitlines()


def heading_above(lines: list[str], index: int) -> tuple[int, int]:
    """The nearest heading above a line: (its line index, its level)."""
    for i in range(index, -1, -1):
        if m := HEADING.match(lines[i]):
            return i, len(m.group(1))
    return 0, 2


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
