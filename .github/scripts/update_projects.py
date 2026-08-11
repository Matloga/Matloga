import json
import os
import re
import sys
import urllib.request

owner = os.environ["GITHUB_REPOSITORY_OWNER"]
profile_repo = os.environ["GITHUB_REPOSITORY"].split("/")[1]
token = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "User-Agent": "opencode",
    "Accept": "application/vnd.github+json",
    "Authorization": f"token {token}",
}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def readme_description(repo):
    for branch in (repo.get("default_branch") or "main", "master", "main"):
        url = f"https://raw.githubusercontent.com/{owner}/{repo['name']}/{branch}/README.md"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "opencode"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            continue

        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"^#+\s*", "", text, flags=re.M)
        text = re.sub(r"\s+", " ", text).strip()

        for line in text.split("."):
            line = line.strip()
            if len(line) > 15:
                return line[:120] + ("..." if len(line) > 120 else "")
    return None


def build_description(repo):
    desc = (repo.get("description") or "").strip()
    if desc:
        return desc
    generated = readme_description(repo)
    if generated:
        return generated
    lang = repo.get("language")
    if lang:
        return f"A {lang} project built by Tsumbedzo Matloga."
    return "A project by Tsumbedzo Matloga."


try:
    repos = json.loads(fetch(f"https://api.github.com/users/{owner}/repos?sort=updated&per_page=100&type=public"))
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
    desc = build_description(r).replace("|", "\\|")
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
