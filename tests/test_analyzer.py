# tests/test_analyzer.py
from auto_commit.analyzer import classify_diff

def test_classify_feat():
    diff = "add login feature"
    assert classify_diff(diff) == "feat"

def test_classify_fix():
    diff = "fix null pointer bug"
    assert classify_diff(diff) == "fix"