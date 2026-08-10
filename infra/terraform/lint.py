#!/usr/bin/env python3
"""
Static checks for this Terraform configuration.

Not a substitute for `terraform validate` (which also checks provider schemas),
but it runs anywhere and catches the mistakes that actually happen: HCL syntax
errors, references to variables/resources/data sources that don't exist,
declared-but-unused variables, and template placeholders in user_data.sh that
compute.tf never passes in.

    pip install python-hcl2 && python3 lint.py
"""

import glob
import re
import sys

import hcl2

STRIP = str.maketrans("", "", '"')


def unquote(s):
    return s.translate(STRIP)


def main():
    files = sorted(glob.glob("*.tf"))
    if not files:
        print("no .tf files here — run this from infra/terraform/")
        return 1

    parsed, problems = {}, []

    for f in files:
        try:
            with open(f) as fh:
                parsed[f] = hcl2.load(fh)
        except Exception as e:  # noqa: BLE001 - report any parse failure
            problems.append(f"{f}: HCL syntax error -> {e}")
    if problems:
        print("\n".join(problems))
        return 1
    print(f"parsed {len(files)} files with no syntax errors")

    # ---- what the configuration declares --------------------------------
    declared_vars, locals_declared = set(), set()
    resources, datas, outputs = set(), set(), set()

    for doc in parsed.values():
        for b in doc.get("variable", []):
            declared_vars |= {unquote(k) for k in b}
        for b in doc.get("locals", []):
            locals_declared |= {unquote(k) for k in b}
        for b in doc.get("output", []):
            outputs |= {unquote(k) for k in b}
        for b in doc.get("resource", []):
            for rtype, inner in b.items():
                resources |= {f"{unquote(rtype)}.{unquote(n)}" for n in inner}
        for b in doc.get("data", []):
            for dtype, inner in b.items():
                datas |= {f"{unquote(dtype)}.{unquote(n)}" for n in inner}

    blob = "\n".join(open(f).read() for f in files)

    # ---- what it references ---------------------------------------------
    used_vars = set(re.findall(r"\bvar\.([a-zA-Z_]\w*)", blob))
    used_locals = set(re.findall(r"\blocal\.([a-zA-Z_]\w*)", blob))
    used_data = {f"{a}.{b}" for a, b in
                 re.findall(r"\bdata\.([a-z]\w*)\.([a-zA-Z_]\w*)", blob)}
    used_res = {f"{a}.{b}" for a, b in
                re.findall(r"(?<!data\.)\b((?:aws|random)_[a-z0-9_]+)\.([a-zA-Z_]\w*)", blob)}
    # a data reference also matches the resource pattern; drop those
    used_res -= used_data

    def report(label, bad, fatal=True):
        if bad:
            problems.append(f"{label}: {sorted(bad)}") if fatal else None
            print(f"  {'FAIL' if fatal else 'warn'}  {label}: {sorted(bad)}")
        else:
            print(f"  ok    {label}: none")

    print("\ncross-references")
    report("undeclared variable refs", used_vars - declared_vars)
    report("undeclared local refs", used_locals - locals_declared)
    report("undeclared data refs", used_data - datas)
    report("undeclared resource refs", used_res - resources)
    report("variables declared but never used", declared_vars - used_vars, fatal=False)

    # ---- user_data template contract ------------------------------------
    print("\nuser_data.sh template")
    try:
        script = open("user_data.sh").read()
    except FileNotFoundError:
        print("  FAIL  user_data.sh is missing")
        return 1

    # ${x} is a Terraform substitution; $${x} is an escaped literal for bash.
    placeholders = set(re.findall(r"(?<!\$)\$\{([a-zA-Z_]\w*)\}", script))
    tf = [f for f in files if "templatefile(" in open(f).read()]
    passed = set()
    for f in tf:
        body = open(f).read()
        block = body[body.index("templatefile("):]
        block = block[: block.index("})") + 2]
        passed |= set(re.findall(r"^\s*([a-zA-Z_]\w*)\s*=", block, re.M))

    report("placeholders used but not passed in", placeholders - passed)
    report("values passed but unused in the script", passed - placeholders, fatal=False)

    # bash variables must be escaped as $${VAR} so Terraform leaves them alone
    unescaped = re.findall(r"(?<!\$)\$\{([A-Z_]{2,})\}", script)
    report("bash vars that Terraform would try to interpolate", set(unescaped))

    print(f"\nsummary: {len(resources)} resources, {len(datas)} data sources, "
          f"{len(declared_vars)} variables, {len(outputs)} outputs")

    if problems:
        print(f"\n{len(problems)} problem(s) found")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
