# AudioCompare End-to-End Tests

This directory contains end-to-end tests for the AudioCompare audio matching system.

## Overview

The test suite validates core functionality including:
- Exact file matching (identical audio files)
- Format compatibility (WAV PCM/IEEE Float, MP3)
- No-match detection (different audio files)
- Partial clip matching (shorter clips from longer files)
- Empty file handling (silent WAV files)
- Directory comparisons
- Error handling for invalid and corrupted files

## Test Files

Test audio files are downloaded from publicly available sources and stored in `test_fixtures/` (gitignored due to size).

### Directory Structure

```
test_fixtures/
├── base/                    # Original downloaded WAV files
│   ├── piano2.wav           # Piano trill, 6.3 seconds (PCM)
│   ├── LRMonoPhase4.wav     # Voice test, 39 seconds (PCM)
│   ├── organfinale.wav      # Organ solo, 13 seconds (IEEE Float)
│   └── organfinale_pcm.wav  # Organ solo, PCM version (for format testing)
├── copies/                  # Exact copies for match testing
├── different/               # Files for no-match testing
├── silence/                 # Silent WAV files for edge cases
└── mp3/                     # MP3 versions (generated from WAV files)
    ├── piano2.mp3           # Converted from piano2.wav (192kbps)
    ├── LRMonoPhase4.mp3     # Converted from LRMonoPhase4.wav (192kbps)
    └── organfinale_pcm.mp3  # Converted from organfinale_pcm.wav (192kbps)
```

### Source Attribution

Test files are downloaded from:
- **Source**: https://www.kozco.com/tech/soundtests.html
- **License**: Public domain test files
- **Purpose**: Audio format testing and validation

## Setup

### 1. Install Test Dependencies

```bash
uv sync --extra test
```

This installs:
- pytest (test framework)
- pytest-timeout (30s timeout per test)
- requests (for downloading test files)

### 2. Download Test Files

```bash
uv run python test/download_test_files.py
```

This script will:
1. Download 3 base WAV files (~13MB total)
2. Create exact copies for match testing
3. Extract partial clips for partial match testing
4. Generate silent WAV files for edge cases
5. Generate MP3 files from WAV files (requires ffmpeg)
6. Create a manifest documenting all files

**Note**: Test files are only downloaded once. If files exist, the script skips downloading.

### MP3 Test Files (Optional)

MP3 test files are generated using ffmpeg. If ffmpeg is not installed:
- MP3 tests will be skipped automatically
- All WAV tests will still run normally

To install ffmpeg:
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Then regenerate test files
rm -rf test/test_fixtures/mp3
uv run python test/download_test_files.py
```

## Running Tests

### Run All Tests

```bash
uv run pytest test/ -v
```

### Run Specific Test Class

```bash
uv run pytest test/test_e2e.py::TestExactMatches -v
```

### Run Single Test

```bash
uv run pytest test/test_e2e.py::TestExactMatches::test_exact_match_piano -v
```

### Run with Output Capture Disabled

```bash
uv run pytest test/ -v -s
```

## Test Cases

### Exact Matches (3 tests)
- `test_exact_match_piano` - Identical piano files should match with high score (>5)
- `test_exact_match_organ` - Identical organ files should match with high score
- `test_self_match` - File compared to itself should match perfectly

### Format Compatibility (1 test)
- `test_pcm_vs_ieee_float_match` - PCM and IEEE Float versions of same audio should match

### No Matches (1 test)
- `test_different_audio_no_match` - Piano and organ should NOT match

### Partial Matches (1 test)
- `test_clip_matches_full_file` - 5-second clip should match the full 39-second file

### Empty Files (1 test)
- `test_empty_files_match` - Two silent files should match each other

### Directory Comparisons (2 tests)
- `test_directory_vs_file` - Compare directory against single file
- `test_directory_vs_directory` - Compare two directories

### Error Handling (2 tests)
- `test_invalid_file_handling` - Non-WAV file should produce error
- `test_missing_file_handling` - Non-existent file should produce error

### MP3 Support (6 tests)
- `test_mp3_self_match` - MP3 file compared to itself should match
- `test_mp3_vs_original_wav` - MP3 should match the WAV it was derived from
- `test_different_mp3s_no_match` - Different MP3 files should not match
- `test_mp3_directory_matching` - Mixed WAV/MP3 directories should find matches
- `test_corrupted_mp3_error_handling` - Corrupted MP3 should produce descriptive error
- `test_unsupported_format_error` - Unsupported format (e.g., FLAC) should produce helpful error

**Note**: MP3 tests are automatically skipped if MP3 files are not available (requires ffmpeg)

## Test Configuration

- **Timeout**: Each test has a 30-second timeout
- **Output**: Only shown on failures (capture enabled by default)
- **Retries**: No retries (fail fast as specified)

## Troubleshooting

### Test files not found

```
ERROR: Test files not found. Please run: uv run python test/download_test_files.py
```

**Solution**: Run the download script to fetch test files.

### Download fails with SSL error

The download script disables SSL verification for kozco.com due to known certificate issues. This is safe for public test data.

### Tests timeout

If tests consistently timeout, the audio files may be too large or the algorithm may need optimization. Current files are sized appropriately (~1-7MB each).

### Permission errors

Ensure you have write permissions to the `test/test_fixtures/` directory.

## Continuous Integration

To run these tests in CI:

1. Install test dependencies: `uv sync --extra test`
2. Download test files: `uv run python test/download_test_files.py`
3. Run tests: `uv run pytest test/ -v`

**Note**: Consider caching `test_fixtures/` in CI to avoid re-downloading on every run.

## File Sizes

### WAV Files
- piano2.wav: ~1.2MB
- LRMonoPhase4.wav: ~7.3MB
- organfinale.wav: ~4.4MB
- Generated WAV files: ~2MB
- **WAV Total**: ~15MB

### MP3 Files (if generated)
- piano2.mp3: ~149KB
- LRMonoPhase4.mp3: ~910KB
- organfinale_pcm.mp3: ~306KB
- **MP3 Total**: ~1.4MB

**Grand Total**: ~16.4MB

## Extending Tests

To add new test cases:

1. Add test WAV files to `test_fixtures/` directories
2. Update `download_test_files.py` if new files need downloading
3. Add test methods to appropriate test class in `test_e2e.py`
4. Follow existing naming conventions: `test_<scenario>_<expected_outcome>`

## License

Test code is part of the AudioCompare project. Test audio files are public domain from kozco.com.
