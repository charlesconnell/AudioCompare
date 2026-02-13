Summary
-------

Compares two audio files or directories of audio files to gauge their
similarity. A file that is likely to have been derived from another
is flagged as a match.

To run the program, type one of:
* `uv run audiomatch -f file1.wav -f file2.wav`
* `uv run audiomatch -f file1.wav -d dir1`
* `uv run audiomatch -d dir1 -f file1.wav`
* `uv run audiomatch -d dir1 -d dir2`

Arguments following a "-f" argument must be a filename,
and arguments following a "-d" argument must be a directory
containing only audio files. Input files must be WAVE or MP3 files.
You may list the same file or directory twice.

Supported formats:
* WAVE: PCM (16-bit) and IEEE Float (32-bit)
* MP3: All standard MP3 formats

If errors are found, appropriate error messages
will be printed, and the program may continue if it can.
Match results will be printed as "NO MATCH" if two
non-matching files were compared, and "MATCH ..."
if two matching files were compared, listing the two
files that matched, and giving the match score.

This program is intended to run on any operating system, but has mostly been tested on Linux and Mac OS X.

Dependencies
------------

* Python 3.8+
* NumPy
* miniaudio (for MP3 decoding)
* uv (for package management)

All audio format support is included - no external audio tools required.

Usage
-----

Run the program using `uv run`:

```bash
uv run audiomatch -f file1.wav -f file2.wav
```

Alternatively, if you activate the virtual environment first:

```bash
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
audiomatch -f file1.wav -f file2.wav
```

Testing
-------

The project includes end-to-end tests that validate the core matching functionality.

### Running Tests

1. Install test dependencies:
```bash
uv sync --extra test
```

2. Download test files (first time only):
```bash
uv run python test/download_test_files.py
```

3. Run the test suite:
```bash
uv run pytest test/ -v
```

Test files are downloaded from publicly available sources and stored in `test/test_fixtures/` (gitignored).
See `test/README.md` for detailed testing documentation.

Technical Details
-----------------

### Audio Format Support

AudioCompare includes native support for WAVE and MP3 formats with no external dependencies:

- **WAVE files**: Parsed directly using custom WAV parser supporting PCM and IEEE Float formats
- **MP3 files**: Decoded using the miniaudio library (pure Python bindings to C decoder)

Both formats are converted to a common PCM representation for fingerprint analysis.

### How It Works

AudioCompare uses audio fingerprinting to detect if files are derived from each other:

1. **FFT Analysis**: Divides audio into time chunks and performs FFT to extract frequency data
2. **Fingerprint Extraction**: Identifies dominant frequencies in each chunk to create a hash
3. **Matching**: Compares fingerprint hashes between files to find time-aligned patterns
4. **Scoring**: Calculates match confidence based on consistent time offsets

A match score above 5 indicates files are likely derived from the same source.

History
-------

The program was written as the semester project
for CS 4500, Fall 2013, with Professor William Clinger
at Northeastern University.

The team members were:
* An Dang (@dangan249)
* Cory Finger (@fingerco)
* Zheng Hui Er (@zh-er)
* Charles Connell (@charlesconnell)


Third-Party Software Acknowledgements
-------------------------------------

There are about 15 lines of code in FFT.py that
are a modified version of code inside
matplotlib. The file
LICENSE.matplotlib license found in this directory
is the matplotlib license, included as required
when creating derivative works. More information
can be found in FFT.py.

Notes
-----

Test files are automatically downloaded from public sources when you run the test setup script.
The audio files are stored in `test/test_fixtures/` and are excluded from git due to their size (~15MB total).
