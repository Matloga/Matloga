import json
import os
import re
import sys
import urllib.request

owner = os.environ["GITHUB_REPOSITORY_OWNER"]
profile_repo = os.environ["GITHUB_REPOSITORY"].split("/")[1]
token = os.environ["GITHUB_TOKEN"]

url = f"https://api.github.com/users/{owner}/repos?sort=updated&per_page=100&type=public"
req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "opencode",
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {token}",
    },
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        repos = json.load(resp)
except Exception as exc:
    print(f"::error::Failed to fetch repos: {exc}")
    sys.exit(0)

repos = [r for r in repos if not r["fork"] and r["name"] != profile_repo]
repos.sort(key=lambda r: r["pushed_at"], reverse=True)
repos = repos[:5]


def prettify(name):
    return re.sub(r"[-_]", " ", name).title()


rows = []
for r in repos:
    name = prettify(r["name"])
    desc = (r.get("description") or "No description provided.").strip()
    desc = desc.replace("|", "\\|")
    lang = r.get("language") or "—"
    rows.append(f"| [**{name}**]({r['html_url']}) | {desc} | {lang} |")

table = "\n".join(rows)
section = "| Project | Description | Tech |\n|---|---|---|\n" + table

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

pattern = re.compile(r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->", re.S)
replacement = f"<!-- PROJECTS:START -->\n{section}\n<!-- PROJECTS:END -->"

if pattern.search(readme):
    new_readme = pattern.sub(replacement, readme)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)
    print("Projects section updated.")
else:
    print("No PROJECTS markers found in README; skipping.")
    sys.exit(0)
