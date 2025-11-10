# auto_commit/analyzer.py
import re
from git import Repo
from typing import List, Dict

CHANGE_PATTERNS = {
    "feat": [r"add", r"new", r"implement", r"create", r"feature"],
    "fix": [r"fix", r"bug", r"resolve", r"patch", r"correct"],
    "docs": [r"doc", r"readme", r"comment", r"update.*(doc|readme)"],
    "refactor": [r"refactor", r"clean", r"optimize", r"restructure"],
    "test": [r"test", r"spec", r"mock", r"coverage"],
    "chore": [r"chore", r"deps", r"config", r"build", r"ci"],
}

def classify_diff(diff: str) -> str:
    diff_lower = diff.lower()
    for type_, patterns in CHANGE_PATTERNS.items():
        if any(re.search(p, diff_lower) for p in patterns):
            return type_
    return "chore"

def generate_smart_message(repo: Repo) -> Dict[str, str]:
    diffs = []
    for item in repo.index.diff(None):
        if item.a_path:
            diffs.append(item.a_path)
        if item.b_path:
            diffs.append(item.b_path)

    if not diffs:
        return {"type": "chore", "message": "No changes detected"}

    # Sample first few lines of diff
    sample_diff = ""
    for item in repo.index.diff(None)[:3]:
        if item.diff:
            sample_diff += item.diff.decode(errors='ignore')[:200]

    commit_type = classify_diff(sample_diff)
    scope = "general"
    if len(diffs) == 1:
        scope = diffs[0].split("/")[-1].split(".")[0]
    elif "tests/" in str(diffs):
        scope = "tests"

    subject = f"Update {len(diffs)} file(s)"
    if commit_type == "feat":
        subject = f"Add {scope} feature"
    elif commit_type == "fix":
        subject = f"Fix issue in {scope}"

    return {
        "type": commit_type,
        "scope": scope,
        "subject": subject,
        "body": f"Files changed: {', '.join([d.split('/')[-1] for d in diffs[:5]])}"
    }