import json
import re
import sys

header = re.compile(r"^\[(\w+)\]\s+(.+?):(\d+)\s+\((\w+)\)\s*$")

comments = []
current = None

with open(sys.argv[1], encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        m = header.match(line)
        if m:
            if current:
                comments.append(current)
            sev, path, num, cat = m.groups()
            current = {"path": path, "line": int(num), "head": f"**[{sev}] ({cat})**", "text": []}
        elif current and line.startswith("  "):
            current["text"].append(line.strip())
        elif current and not line.strip():
            comments.append(current)
            current = None

if current:
    comments.append(current)

out = [
    {"path": c["path"], "line": c["line"], "body": c["head"] + "\n\n" + " ".join(c["text"])}
    for c in comments
]

with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(out, f)

print(f"Converted {len(out)} findings")