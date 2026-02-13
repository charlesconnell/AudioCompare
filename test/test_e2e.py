"""
End-to-end tests for AudioCompare WAV file matching.

These tests verify the core functionality of the audio matching algorithm
using real WAV files downloaded from public sources.
"""

import pytest
from pathlib import Path


# Use 30-second timeout for all tests as specified
pytestmark = pytest.mark.timeout(30)


class TestExactMatches:
    """Test cases for files that should match exactly."""

    def test_exact_match_piano(
        self,
        base_files_dir,
        copies_dir,
        run_audiomatch_fixture,
        parse_match_result_fixture,
    ):
        """Two identical piano WAV files should produce MATCH result with high score."""
        file1 = base_files_dir / "piano2.wav"
        file2 = copies_dir / "piano2_copy.wav"

        result = run_audiomatch_fixture(["-f", str(file1), "-f", str(file2)])

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "MATCH" in result.stdout, (
            f"Expected MATCH in output, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert len(matches) > 0, "No match results found in output"
        assert matches[0]["is_match"], "Expected match but got no match"
        assert matches[0]["score"] is not None, "Expected score in match result"
        assert matches[0]["score"] > 5, f"Expected score > 5, got {matches[0]['score']}"

    def test_exact_match_organ(
        self,
        base_files_dir,
        copies_dir,
        run_audiomatch_fixture,
        parse_match_result_fixture,
    ):
        """Two identical organ WAV files should produce MATCH result with high score."""
        file1 = base_files_dir / "organfinale.wav"
        file2 = copies_dir / "organfinale_copy.wav"

        result = run_audiomatch_fixture(["-f", str(file1), "-f", str(file2)])

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "MATCH" in result.stdout, (
            f"Expected MATCH in output, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert matches[0]["is_match"], "Expected match but got no match"
        assert matches[0]["score"] > 5, (
            f"Expected high score, got {matches[0]['score']}"
        )

    def test_self_match(
        self, base_files_dir, run_audiomatch_fixture, parse_match_result_fixture
    ):
        """A file compared to itself should produce MATCH with perfect score."""
        file1 = base_files_dir / "piano2.wav"

        result = run_audiomatch_fixture(["-f", str(file1), "-f", str(file1)])

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "MATCH" in result.stdout, (
            f"Expected MATCH in output, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert matches[0]["is_match"], "File should match itself"
        assert matches[0]["score"] > 5, "Self-match should have high score"


class TestFormatCompatibility:
    """Test cases for matching across different WAV formats."""

    def test_pcm_vs_ieee_float_match(
        self, base_files_dir, run_audiomatch_fixture, parse_match_result_fixture
    ):
        """PCM and IEEE Float versions of the same audio should match."""
        ieee_float_file = base_files_dir / "organfinale.wav"
        pcm_file = base_files_dir / "organfinale_pcm.wav"

        result = run_audiomatch_fixture(
            ["-f", str(ieee_float_file), "-f", str(pcm_file)]
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "MATCH" in result.stdout, (
            f"Expected PCM and IEEE Float versions to MATCH, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert matches[0]["is_match"], "PCM and IEEE Float versions should match"
        assert matches[0]["score"] > 5, (
            f"Expected high match score, got {matches[0]['score']}"
        )


class TestNoMatches:
    """Test cases for files that should NOT match."""

    def test_different_audio_no_match(
        self, different_dir, run_audiomatch_fixture, parse_match_result_fixture
    ):
        """Piano and organ files should NOT match."""
        file1 = different_dir / "piano2.wav"
        file2 = different_dir / "organfinale.wav"

        result = run_audiomatch_fixture(["-f", str(file1), "-f", str(file2)])

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "NO MATCH" in result.stdout, (
            f"Expected NO MATCH in output, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert not matches[0]["is_match"], "Different audio files should not match"


class TestPartialMatches:
    """Test cases for partial audio clips."""

    def test_clip_matches_full_file(
        self,
        base_files_dir,
        copies_dir,
        run_audiomatch_fixture,
        parse_match_result_fixture,
    ):
        """A 5-second clip should match the full audio file it was extracted from."""
        full_file = base_files_dir / "LRMonoPhase4.wav"
        clip_file = copies_dir / "LRMonoPhase4_clip5s.wav"

        result = run_audiomatch_fixture(["-f", str(clip_file), "-f", str(full_file)])

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "MATCH" in result.stdout, (
            f"Expected clip to MATCH full file, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert matches[0]["is_match"], "Clip should match the full file"
        assert matches[0]["score"] > 5, (
            f"Expected high match score, got {matches[0]['score']}"
        )


class TestEmptyFiles:
    """Test cases for empty/silent files."""

    def test_empty_files_match(
        self, silence_dir, run_audiomatch_fixture, parse_match_result_fixture
    ):
        """Two silent/empty WAV files should match each other."""
        file1 = silence_dir / "silence1.wav"
        file2 = silence_dir / "silence2.wav"

        result = run_audiomatch_fixture(["-f", str(file1), "-f", str(file2)])

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "MATCH" in result.stdout, (
            f"Expected silent files to MATCH, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert matches[0]["is_match"], "Empty files should match each other"


class TestDirectoryComparisons:
    """Test cases for directory-based comparisons."""

    def test_directory_vs_file(
        self, copies_dir, base_files_dir, run_audiomatch_fixture
    ):
        """Compare a directory of files against a single file."""
        directory = copies_dir
        single_file = base_files_dir / "piano2.wav"

        result = run_audiomatch_fixture(["-d", str(directory), "-f", str(single_file)])

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        # Should have at least one match (piano2_copy.wav matches piano2.wav)
        assert "MATCH" in result.stdout, (
            f"Expected at least one MATCH, got: {result.stdout}"
        )

    def test_directory_vs_directory(
        self, base_files_dir, copies_dir, run_audiomatch_fixture
    ):
        """Compare two directories of files."""
        result = run_audiomatch_fixture(
            ["-d", str(base_files_dir), "-d", str(copies_dir)]
        )

        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        # Should have multiple matches since copies were made from base files
        match_count = result.stdout.count("MATCH")
        assert match_count >= 2, f"Expected at least 2 matches, found {match_count}"


class TestExitCodes:
    """Test cases specifically for exit codes."""

    def test_exit_code_success_on_match(
        self, base_files_dir, copies_dir, run_audiomatch_fixture
    ):
        """Exit code should be 0 when files match successfully."""
        file1 = base_files_dir / "piano2.wav"
        file2 = copies_dir / "piano2_copy.wav"

        result = run_audiomatch_fixture(["-f", str(file1), "-f", str(file2)])

        assert result.returncode == 0, (
            f"Expected exit code 0 for successful match, got {result.returncode}"
        )
        assert "MATCH" in result.stdout

    def test_exit_code_success_on_no_match(
        self, different_dir, run_audiomatch_fixture
    ):
        """Exit code should be 0 when files don't match (no error occurred)."""
        file1 = different_dir / "piano2.wav"
        file2 = different_dir / "organfinale.wav"

        result = run_audiomatch_fixture(["-f", str(file1), "-f", str(file2)])

        assert result.returncode == 0, (
            f"Expected exit code 0 for successful comparison (no match), got {result.returncode}"
        )
        assert "NO MATCH" in result.stdout

    def test_exit_code_failure_on_invalid_file(
        self, tmp_path, base_files_dir, run_audiomatch_fixture
    ):
        """Exit code should be 1 when processing an invalid file."""
        invalid_file = tmp_path / "not_audio.txt"
        invalid_file.write_text("This is not an audio file")
        valid_file = base_files_dir / "piano2.wav"

        result = run_audiomatch_fixture(
            ["-f", str(invalid_file), "-f", str(valid_file)]
        )

        assert result.returncode == 1, (
            f"Expected exit code 1 for invalid file, got {result.returncode}"
        )
        assert "ERROR" in result.stderr or "ERROR" in result.stdout

    def test_exit_code_failure_on_missing_file(
        self, base_files_dir, run_audiomatch_fixture
    ):
        """Exit code should be 1 when a file doesn't exist."""
        valid_file = base_files_dir / "piano2.wav"
        missing_file = base_files_dir / "does_not_exist.wav"

        result = run_audiomatch_fixture(
            ["-f", str(missing_file), "-f", str(valid_file)]
        )

        assert result.returncode == 1, (
            f"Expected exit code 1 for missing file, got {result.returncode}"
        )
        # Should have error output (either formatted ERROR or exception traceback)
        assert len(result.stderr) > 0 or "ERROR" in result.stdout, (
            "Expected error output in stderr or stdout"
        )

    def test_exit_code_failure_on_wrong_argument_count(self, run_audiomatch_fixture):
        """Exit code should be 1 when incorrect number of inputs provided."""
        # Only one input provided
        result = run_audiomatch_fixture(["-f", "dummy.wav"])

        assert result.returncode == 1, (
            f"Expected exit code 1 for wrong argument count, got {result.returncode}"
        )
        assert "ERROR" in result.stderr or "ERROR" in result.stdout

    def test_exit_code_failure_on_no_arguments(self, run_audiomatch_fixture):
        """Exit code should be 1 when no inputs provided."""
        result = run_audiomatch_fixture([])

        assert result.returncode == 1, (
            f"Expected exit code 1 for no arguments, got {result.returncode}"
        )
        assert "ERROR" in result.stderr or "ERROR" in result.stdout

    def test_exit_code_failure_on_three_inputs(
        self, base_files_dir, run_audiomatch_fixture
    ):
        """Exit code should be 1 when three inputs provided (should be exactly two)."""
        file1 = base_files_dir / "piano2.wav"
        file2 = base_files_dir / "organfinale.wav"
        file3 = base_files_dir / "LRMonoPhase4.wav"

        result = run_audiomatch_fixture(
            ["-f", str(file1), "-f", str(file2), "-f", str(file3)]
        )

        assert result.returncode == 1, (
            f"Expected exit code 1 for three inputs, got {result.returncode}"
        )
        assert "ERROR" in result.stderr or "ERROR" in result.stdout
        assert "exactly two" in result.stderr.lower() or "exactly two" in result.stdout.lower()

    def test_exit_code_success_on_directory_match(
        self, base_files_dir, copies_dir, run_audiomatch_fixture
    ):
        """Exit code should be 0 when comparing directories successfully."""
        result = run_audiomatch_fixture(
            ["-d", str(base_files_dir), "-d", str(copies_dir)]
        )

        assert result.returncode == 0, (
            f"Expected exit code 0 for successful directory comparison, got {result.returncode}"
        )


class TestErrorHandling:
    """Test cases for error handling."""

    def test_invalid_file_handling(
        self, tmp_path, base_files_dir, run_audiomatch_fixture
    ):
        """Attempting to compare an invalid file should produce an error message."""
        # Create a non-WAV text file
        invalid_file = tmp_path / "not_audio.txt"
        invalid_file.write_text("This is not an audio file")

        valid_file = base_files_dir / "piano2.wav"

        result = run_audiomatch_fixture(
            ["-f", str(invalid_file), "-f", str(valid_file)]
        )

        # Should fail or produce error message
        assert (
            result.returncode != 0
            or "ERROR" in result.stderr
            or "ERROR" in result.stdout
        ), "Expected error when processing invalid file"

    def test_missing_file_handling(self, base_files_dir, run_audiomatch_fixture):
        """Attempting to compare a non-existent file should produce an error."""
        valid_file = base_files_dir / "piano2.wav"
        missing_file = base_files_dir / "does_not_exist.wav"

        result = run_audiomatch_fixture(
            ["-f", str(missing_file), "-f", str(valid_file)]
        )

        # Should fail or produce error message
        assert (
            result.returncode != 0
            or "ERROR" in result.stderr
            or "ERROR" in result.stdout
        ), "Expected error when file is missing"


class TestMP3Support:
    """Test cases for MP3 file support."""

    def test_mp3_self_match(
        self,
        mp3_dir,
        run_audiomatch_fixture,
        parse_match_result_fixture,
    ):
        """An MP3 file compared to itself should produce MATCH with high score."""
        mp3_file = mp3_dir / "piano2.mp3"

        if not mp3_file.exists():
            pytest.skip("MP3 test files not available (requires ffmpeg)")

        result = run_audiomatch_fixture(["-f", str(mp3_file), "-f", str(mp3_file)])

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "MATCH" in result.stdout, f"Expected MATCH, got: {result.stdout}"

        matches = parse_match_result_fixture(result.stdout)
        assert matches[0]["is_match"], "Expected match but got no match"
        assert matches[0]["score"] > 5, f"Expected score > 5, got {matches[0]['score']}"

    def test_mp3_vs_original_wav(
        self,
        base_files_dir,
        mp3_dir,
        run_audiomatch_fixture,
        parse_match_result_fixture,
    ):
        """MP3 derived from WAV should match the original WAV file."""
        wav_file = base_files_dir / "piano2.wav"
        mp3_file = mp3_dir / "piano2.mp3"

        if not mp3_file.exists():
            pytest.skip("MP3 test files not available (requires ffmpeg)")

        result = run_audiomatch_fixture(["-f", str(wav_file), "-f", str(mp3_file)])

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "MATCH" in result.stdout, (
            f"Expected MATCH between WAV and MP3, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert matches[0]["is_match"], "Expected WAV and MP3 to match"
        assert matches[0]["score"] > 5, (
            f"Expected high score for WAV-MP3 match, got {matches[0]['score']}"
        )

    def test_different_mp3s_no_match(
        self,
        mp3_dir,
        run_audiomatch_fixture,
        parse_match_result_fixture,
    ):
        """Two different MP3 files should not match."""
        mp3_file1 = mp3_dir / "piano2.mp3"
        mp3_file2 = mp3_dir / "LRMonoPhase4.mp3"

        if not mp3_file1.exists() or not mp3_file2.exists():
            pytest.skip("MP3 test files not available (requires ffmpeg)")

        result = run_audiomatch_fixture(["-f", str(mp3_file1), "-f", str(mp3_file2)])

        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "NO MATCH" in result.stdout, (
            f"Expected NO MATCH for different MP3s, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        assert not matches[0]["is_match"], "Different MP3 files should not match"

    def test_mp3_directory_matching(
        self,
        mp3_dir,
        base_files_dir,
        run_audiomatch_fixture,
        parse_match_result_fixture,
    ):
        """Directory with mixed WAV and MP3 files should find matches."""
        # Compare MP3 directory with base WAV directory
        if not mp3_dir.exists() or len(list(mp3_dir.glob("*.mp3"))) == 0:
            pytest.skip("MP3 test files not available (requires ffmpeg)")

        result = run_audiomatch_fixture(["-d", str(base_files_dir), "-d", str(mp3_dir)])

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Should find at least one match (WAV vs corresponding MP3)
        assert "MATCH" in result.stdout, (
            f"Expected at least one MATCH between directories, got: {result.stdout}"
        )

        matches = parse_match_result_fixture(result.stdout)
        match_count = sum(1 for m in matches if m["is_match"])
        assert match_count > 0, "Expected matches between WAV and MP3 directories"

    def test_corrupted_mp3_error_handling(
        self,
        test_fixtures_dir,
        run_audiomatch_fixture,
    ):
        """Corrupted MP3 file should produce descriptive error message."""
        # Create a fake/corrupted MP3 file
        corrupted_mp3 = test_fixtures_dir / "corrupted.mp3"
        corrupted_mp3.write_bytes(b"NOT A REAL MP3 FILE" * 100)

        try:
            result = run_audiomatch_fixture(
                ["-f", str(corrupted_mp3), "-f", str(corrupted_mp3)]
            )

            # Should fail with descriptive error
            assert result.returncode != 0, "Expected failure for corrupted MP3"
            assert (
                "Failed to decode MP3" in result.stderr
                or "format" in result.stderr.lower()
            ), f"Expected descriptive error message, got: {result.stderr}"
        finally:
            # Cleanup
            if corrupted_mp3.exists():
                corrupted_mp3.unlink()

    def test_unsupported_format_error(
        self,
        test_fixtures_dir,
        run_audiomatch_fixture,
    ):
        """Unsupported audio format should produce helpful error message."""
        # Create a fake audio file with unsupported format
        fake_file = test_fixtures_dir / "fake.flac"
        fake_file.write_bytes(b"fLaC" + b"\x00" * 100)  # FLAC signature

        try:
            result = run_audiomatch_fixture(
                ["-f", str(fake_file), "-f", str(fake_file)]
            )

            # Should fail with helpful error message
            assert result.returncode != 0, "Expected failure for unsupported format"
            assert any(
                keyword in result.stderr.lower()
                for keyword in ["unsupported", "format", "convert", "wave", "mp3"]
            ), f"Expected helpful error message, got: {result.stderr}"
        finally:
            # Cleanup
            if fake_file.exists():
                fake_file.unlink()
