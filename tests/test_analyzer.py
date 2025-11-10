# tests/test_analyzer.py
from auto_commit.analyzer import classify_diff, generate_smart_message
from git import Repo
import os


def test_classify_feat():
    diff = "add login feature"
    files = ["auth.py"]
    assert classify_diff(diff, files) == "feat"


def test_classify_fix():
    diff = "fix null pointer bug"
    files = ["utils.c"]
    assert classify_diff(diff, files) == "fix"


def test_classify_test():
    diff = "add test coverage"
    files = ["tests/test_user.py"]
    assert classify_diff(diff, files) == "test"


def test_generate_message_no_duplicates(tmp_path):
    os.chdir(tmp_path)
    repo = Repo.init(tmp_path)

    # Create files
    (tmp_path / "hello.py").write_text('print("hello")\n')
    (tmp_path / "utils.py").write_text("def add(a,b): return a+b\n")

    # USE repo.git.add() — THIS IS THE MAGIC
    repo.git.add("hello.py", "utils.py")

    msg = generate_smart_message(repo)

    # DEBUG: Uncomment to see
    # print("BODY:", msg["body"])

    assert "hello.py, utils.py" in msg["body"]
    assert "hello.py, hello.py" not in msg["body"]
    assert msg["type"] == "feat"
    assert msg["scope"] == "src"
