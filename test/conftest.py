"""
Pytest configuration and fixtures for AudioCompare tests.
"""

import pytest
import subprocess
import sys
from pathlib import Path


# Get paths
TEST_DIR = Path(__file__).parent
FIXTURES_DIR = TEST_DIR / "test_fixtures"
PROJECT_ROOT = TEST_DIR.parent


@pytest.fixture(scope="session")
def test_fixtures_dir():
    """Return the path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def base_files_dir(test_fixtures_dir):
    """Return the path to base test files."""
    return test_fixtures_dir / "base"


@pytest.fixture(scope="session")
def copies_dir(test_fixtures_dir):
    """Return the path to copied test files."""
    return test_fixtures_dir / "copies"


@pytest.fixture(scope="session")
def different_dir(test_fixtures_dir):
    """Return the path to different test files."""
    return test_fixtures_dir / "different"


@pytest.fixture(scope="session")
def silence_dir(test_fixtures_dir):
    """Return the path to silent test files."""
    return test_fixtures_dir / "silence"


@pytest.fixture(scope="session")
def mp3_dir(test_fixtures_dir):
    """Return the path to MP3 test files."""
    return test_fixtures_dir / "mp3"


@pytest.fixture(scope="session", autouse=True)
def ensure_test_files(test_fixtures_dir):
    """Ensure test files are downloaded before running tests."""
    # Check if base files exist
    base_dir = test_fixtures_dir / "base"
    if not base_dir.exists() or len(list(base_dir.glob("*.wav"))) == 0:
        pytest.fail(
            "Test files not found. Please run: uv run python test/download_test_files.py"
        )

    # Check if MP3 files exist (optional - just warn, don't fail)
    mp3_dir = test_fixtures_dir / "mp3"
    if not mp3_dir.exists() or len(list(mp3_dir.glob("*.mp3"))) == 0:
        print("\n⚠️  Warning: MP3 test files not found. MP3 tests will be skipped.")
        print("   To enable MP3 tests: install ffmpeg and re-run download script")
        print("   - macOS: brew install ffmpeg")
        print("   - Linux: sudo apt-get install ffmpeg")


def run_audiomatch(args):
    """
    Run the audiomatch command with given arguments.

    Args:
        args: List of command line arguments

    Returns:
        CompletedProcess object with returncode, stdout, stderr
    """
    cmd = [sys.executable, str(PROJECT_ROOT / "main.py")] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result


def parse_match_result(output):
    """
    Parse the output of audiomatch to extract match results.

    Args:
        output: String output from audiomatch

    Returns:
        dict with keys: 'is_match', 'score', 'file1', 'file2'
    """
    lines = output.strip().split("\n")
    results = []

    for line in lines:
        if line.startswith("MATCH ") or line.startswith("NO MATCH "):
            is_match = line.startswith("MATCH ")

            # Extract score if it's a match
            score = None
            if is_match and "(" in line and ")" in line:
                score_str = line[line.find("(") + 1 : line.find(")")]
                try:
                    score = float(score_str)
                except ValueError:
                    score = None

            # Extract filenames
            parts = line.split()
            file1 = parts[1] if len(parts) > 1 else None
            file2 = parts[2] if len(parts) > 2 else None

            results.append(
                {
                    "is_match": is_match,
                    "score": score,
                    "file1": file1,
                    "file2": file2,
                    "raw_line": line,
                }
            )

    return results


@pytest.fixture
def run_audiomatch_fixture():
    """Fixture that provides the run_audiomatch function."""
    return run_audiomatch


@pytest.fixture
def parse_match_result_fixture():
    """Fixture that provides the parse_match_result function."""
    return parse_match_result
