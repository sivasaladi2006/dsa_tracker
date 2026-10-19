import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (file, exact text to replace, replacement, what the mistake is, test scope, test file that must catch it)
MUTATIONS = [
    ("app/algorithms/search.py", "_key_of(items[mid], key) < target", "_key_of(items[mid], key) <= target",
     "lower_bound compares with <= instead of <", "unit", "test_search.py"),
    ("app/algorithms/sorting.py", "else left_key <= right_key", "else left_key < right_key",
     "merge sort stops being stable (ties take the right item first)", "unit", "test_sorting.py"),
    ("app/algorithms/hashing.py", "if self.load_factor() > MAX_LOAD_FACTOR:", "if self.load_factor() > 99:",
     "hash table never resizes", "unit", "test_hashing.py"),
    ("app/algorithms/hashing.py", "self._size -= 1", "self._size -= 0",
     "deleting a key does not shrink the stored size", "unit", "test_hashing.py"),
    ("app/algorithms/graph.py", "if node in mastered:", "if node in ():",
     "BFS no longer stops at mastered topics", "unit", "test_graph.py"),
    ("app/services/scoring.py", "STALE_FULL_AT_DAYS = 30", "STALE_FULL_AT_DAYS = 300",
     "staleness takes 300 days to max out instead of 30", "unit", "test_scoring.py"),
    ("app/services/scoring.py", '"low_solve": 0.45', '"low_solve": 0.55',
     "score weights no longer add up to 1", "unit", "test_scoring.py"),
    ("app/services/recommender.py", "MASTERED_BELOW = 0.35", "MASTERED_BELOW = 0.95",
     "almost every topic counts as mastered", "unit", "test_recommender.py"),
    ("app/services/recommender.py", "MIN_ATTEMPTED_FOR_MASTERY = 3", "MIN_ATTEMPTED_FOR_MASTERY = 0",
     "mastery no longer needs a minimum number of problems tried", "unit", "test_recommender.py"),
    ("app/services/revision.py", "if overdue >= 0:", "if overdue > 0:",
     "a problem due exactly today is not listed", "unit", "test_revision.py"),
    ("app/services/problem_picker.py", "EASY_BELOW = 0.50", "EASY_BELOW = 0.90",
     "the Easy difficulty threshold moves from 0.50 to 0.90", "unit", "test_problem_picker.py"),
    ("app/services/explain.py", "SMALL_SAMPLE = 5", "SMALL_SAMPLE = 3",
     "the small-sample warning threshold moves from 5 to 3", "unit", "test_explain.py"),
    ("app/services/catalog.py", "p.difficulty = %s", "p.difficulty <> %s",
     "the difficulty filter returns the opposite set", "all", "test_api_read.py"),
    ("app/services/catalog.py", "ORDER BY s2.submitted_at DESC", "ORDER BY s2.submitted_at ASC",
     "a problem's latest status uses its oldest submission", "all", "test_api_read.py"),
    ("app/errors.py", '"Retry-After": "5"', '"X-Other": "5"',
     "the 503 response loses its Retry-After header", "all", "test_api_errors.py"),
]


def purge_bytecode():
    """Remove compiled files so a run can never reuse bytecode from a different version of a file."""
    for cache in (ROOT / "app").rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run_tests(scope):
    purge_bytecode()
    cmd = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    if scope == "unit":
        cmd += ["-m", "not integration"]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)


def failing(output):
    """(number of failed tests, sorted test files that had failures)."""
    lines = [l for l in output.splitlines() if l.startswith("FAILED ")]
    files = {l[len("FAILED "):].split("::")[0].split("/")[-1] for l in lines}
    return len(lines), sorted(files)


def app_is_clean():
    return subprocess.run(["git", "diff", "--quiet", "--", "app"], cwd=ROOT).returncode == 0


def server_is_running(port=8000):
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main():
    if server_is_running():
        sys.exit("A server is listening on port 8000. Stop it first (Ctrl+C in its terminal): "
                 "its auto-reloader can cache modified code and give misleading results.")
    if not app_is_clean():
        sys.exit("app/ has uncommitted changes. Commit or stash them first, so nothing can be lost.")

    for rel, old, *_ in MUTATIONS:
        count = (ROOT / rel).read_text().count(old)
        if count != 1:
            sys.exit(f"Cannot run: {old!r} appears {count} times in {rel} (expected 1). Nothing was changed.")

    for scope in ("unit", "all"):
        if run_tests(scope).returncode != 0:
            sys.exit(f"The {scope} tests already fail on unmodified code. Fix that before mutation testing.")
    print("Baseline: all tests pass on the unmodified code.\n")

    caught = suspicious = survived = 0
    for i, (rel, old, new, desc, scope, expect) in enumerate(MUTATIONS, start=1):
        path = ROOT / rel
        original = path.read_text()
        try:
            path.write_text(original.replace(old, new))
            result = run_tests(scope)
        finally:
            path.write_text(original)
        name = Path(rel).name
        n_failed, files = failing(result.stdout)
        if result.returncode == 0:
            survived += 1
            print(f"{i:>2}. SURVIVED   {name}: {desc}   <-- no test noticed this")
        elif result.returncode == 1 and expect in files:
            caught += 1
            print(f"{i:>2}. KILLED     {name}: {desc}")
            print(f"       {n_failed} failing test(s) in: {', '.join(files)}")
        else:
            suspicious += 1
            print(f"{i:>2}. SUSPICIOUS {name}: {desc}")
            print(f"       expected {expect} to fail; pytest exit code {result.returncode}, "
                  f"{n_failed} failing test(s) in: {', '.join(files) or 'none'}")

    clean_again = all(run_tests(scope).returncode == 0 for scope in ("unit", "all"))
    print(f"\n{caught} of {len(MUTATIONS)} mistakes were caught by the test file written for them")
    if suspicious:
        print(f"{suspicious} caught only by unexpected tests, or errored (see SUSPICIOUS lines)")
    if survived:
        print(f"{survived} not caught at all (see SURVIVED lines)")
    print("Baseline after all mutations: " + ("all tests pass" if clean_again else "FAILING, something leaked"))
    print("app/ restored cleanly" if app_is_clean() else "WARNING: app/ differs from git. Run: git diff -- app")
    sys.exit(0 if caught == len(MUTATIONS) and clean_again else 1)


if __name__ == "__main__":
    main()
