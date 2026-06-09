"""Prove a within-file function reorder changed ONLY order, not any body.

For each given file, parse the working-tree version and the git HEAD version, build a map of
{top-level def/class name -> sha256 of its exact source segment}, and assert the two maps are
EQUAL. Equal maps => same set of defs with byte-identical bodies => only their order moved.

Usage: python scripts/check_reorder_neutral.py <file.py> [<file.py> ...]
Exit 0 if every file is neutral (or new/unchanged), 1 if any added/removed/edited a def body.
"""

import ast
import hashlib
import subprocess
import sys


def _defmap(src: str) -> dict[str, str]:
    tree = ast.parse(src)
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seg = ast.get_source_segment(src, node) or ""
            out[node.name] = hashlib.sha256(seg.encode()).hexdigest()
    return out


def _head_src(path: str) -> str | None:
    r = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main(paths: list[str]) -> int:
    bad = 0
    for path in paths:
        cur = open(path).read()
        old = _head_src(path)
        if old is None:
            print(f"NEW (no HEAD)  {path}")
            continue
        co, cn = _defmap(old), _defmap(cur)
        if co == cn:
            print(f"OK  {path}: {len(cn)} top-level defs, bodies byte-identical (order may differ)")
            continue
        bad += 1
        added = sorted(set(cn) - set(co))
        removed = sorted(set(co) - set(cn))
        changed = sorted(k for k in (set(co) & set(cn)) if co[k] != cn[k])
        print(f"DIFF {path}: added={added} removed={removed} body_changed={changed}")
    print("ALL NEUTRAL" if not bad else f"NOT NEUTRAL ({bad} file(s))")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
