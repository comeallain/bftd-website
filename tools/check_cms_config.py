#!/usr/bin/env python3
"""
Guard against the CMS silently deleting content.

Sveltia rewrites content.json from the fields declared in admin/config.yml.
Any key present in content.json but not declared there is dropped on the first
save, with no error and no warning — you would find out when the page went
blank. This check fails the build if that is ever true.

It compares field *names*, not structure, deliberately: no YAML parser is
available without adding a dependency, and a missing name is the failure mode
that actually costs you data.

    python3 tools/check_cms_config.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def json_key_names(obj, acc=None):
    """Every key name appearing anywhere in the document, including inside
    list items."""
    acc = set() if acc is None else acc
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k)
            json_key_names(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            json_key_names(v, acc)
    return acc

def declared_names(yml):
    """Field names declared in the CMS config, from both block and inline
    mapping styles. Ignores names inside comments."""
    live = '\n'.join(re.sub(r'(?<!:)#.*$', '', ln) for ln in yml.splitlines())
    return set(re.findall(r'\bname:\s*([A-Za-z_][A-Za-z0-9_]*)', live))

def main():
    with open(os.path.join(ROOT, 'content.json'), encoding='utf-8') as f:
        content = json.load(f)
    with open(os.path.join(ROOT, 'admin', 'config.yml'), encoding='utf-8') as f:
        cfg = f.read()

    in_json = json_key_names(content)
    in_cfg = declared_names(cfg)

    undeclared = sorted(in_json - in_cfg)
    if undeclared:
        print("ERROR: these keys exist in content.json but are not declared in "
              "admin/config.yml.\n       Saving through the CMS would delete them:\n",
              file=sys.stderr)
        for k in undeclared:
            print(f"         {k}", file=sys.stderr)
        print("\n       Add a field for each, then re-run.", file=sys.stderr)
        return 1

    # Not fatal: a declared field with no data yet is normal (e.g. `active`,
    # which only the Home nav item carries).
    structural = {'content', 'site'}
    extra = sorted(in_cfg - in_json - structural)
    if extra:
        print("note: declared in config.yml but absent from content.json "
              f"(fine if intentional): {', '.join(extra)}")

    print(f"ok: all {len(in_json)} content.json keys are declared in admin/config.yml")
    return 0

if __name__ == '__main__':
    sys.exit(main())
