# auto_commit/analyzer.py
import re
from git import Repo
from git.objects import Blob
import os
from typing import List, Dict

CHANGE_PATTERNS = {
    "feat": [
        r"\b(add|new|implement|create|introduce|enable)\b",
        r"\bfeature\b",
        r"\bui\b",
        r"\bcomponent\b",
        r"\bpage\b",
    ],
    "fix": [
        r"\b(fix|bug|resolve|patch|correct|repair)\b",
        r"\bcrash\b",
        r"\berror\b",
        r"\bfail\b",
    ],
    "docs": [
        r"\b(doc|readme|comment|update.*(doc|readme|example))\b",
        r"\breadme\.md\b",
        r"\bcontributing\.md\b",
    ],
    "refactor": [
        r"\b(refactor|clean|optimize|restructure|improve|rename)\b",
        r"\bperformance\b",
        r"\brewrite\b",
    ],
    "test": [r"\b(test|spec|mock|coverage|assert)\b", r"\btest_.*\.py\b", r"tests?/"],
    "chore": [
        r"\b(chore|deps|config|build|ci|lint|format)\b",
        r"\.toml$",
        r"\.yml$",
        r"\.yaml$",
        r"\.json$",
    ],
}


def classify_diff(diff_text: str, file_paths: List[str]) -> str:
    text = diff_text.lower()
    for f in file_paths:
        f_lower = f.lower()
        for typ, patterns in CHANGE_PATTERNS.items():
            if any(re.search(p, f_lower) for p in patterns):
                return typ
    for typ, patterns in CHANGE_PATTERNS.items():
        if any(re.search(p, text) for p in patterns):
            return typ
    return "chore"


def generate_smart_message(repo: Repo) -> Dict[str, str]:
    diffs = set()
    diff_samples = []

    # Unstaged changes
    for item in repo.index.diff(None):
        path = item.a_path or item.b_path
        if path:
            diffs.add(path)
        if item.diff:
            diff_samples.append(item.diff.decode(errors="ignore"))

    # Staged changes
    staged_samples = []
    if repo.head.is_valid():
        for item in repo.index.diff("HEAD"):
            path = item.a_path or item.b_path
            if path:
                diffs.add(path)
            if item.diff:
                staged_samples.append(item.diff.decode(errors="ignore"))
    else:
        # Initial commit: get staged files from index
        staged_paths = set(path for (path, stage) in repo.index.entries if stage == 0)
        for path in staged_paths:
            diffs.add(path)
            try:
                entry = repo.index.entries[(path, 0)]
                binsha = entry.binsha
                blob = Blob(repo, binsha)
                content = blob.data_stream.read().decode(errors="ignore")
                staged_samples.append(content)
            except:
                pass

    # Untracked files
    untracked = repo.untracked_files
    untracked_samples = []
    for u in untracked:
        diffs.add(u)
        full_path = os.path.join(repo.working_tree_dir, u)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            untracked_samples.append(content)
        except:
            pass

    all_files = sorted(list(diffs))

    if not all_files:
        return {
            "type": "chore",
            "scope": "general",
            "subject": "No changes detected",
            "body": "No files were modified or added.",
        }

    sample_diff = "\n".join(diff_samples + staged_samples + untracked_samples)[:500]
    commit_type = classify_diff(sample_diff, all_files)

    if len(all_files) == 1:
        scope = all_files[0].split("/")[-1].split(".")[0]
    elif any("tests/" in f for f in all_files):
        scope = "tests"
    elif any(f.endswith((".py", ".js", ".ts")) for f in all_files):
        scope = "src"
    else:
        scope = "general"

    file_count = len(all_files)
    subject = f"Update {file_count} file{'s' if file_count != 1 else ''}"
    if commit_type == "feat":
        subject = f"Add {scope} functionality"
    elif commit_type == "fix":
        subject = f"Fix bug in {scope}"
    elif commit_type == "refactor":
        subject = f"Refactor {scope} code"

    file_list = ", ".join([f.split("/")[-1] for f in all_files[:5]])
    if len(all_files) > 5:
        file_list += "..."

    return {
        "type": commit_type,
        "scope": scope,
        "subject": subject,
        "body": f"Files changed: {file_list}",
    }
