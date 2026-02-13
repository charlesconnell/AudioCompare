#!/usr/bin/env python
"""
Download and prepare test WAV files for AudioCompare end-to-end tests.

This script downloads publicly available WAV files from kozco.com and
generates additional test files (copies, clips, silent files) for testing.
"""

import sys
import wave
import struct
from pathlib import Path
import json
import requests
import urllib3

# Disable SSL warnings for kozco.com (known SSL certificate issue)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Base directory for test fixtures
FIXTURES_DIR = Path(__file__).parent / "test_fixtures"
BASE_DIR = FIXTURES_DIR / "base"
COPIES_DIR = FIXTURES_DIR / "copies"
DIFFERENT_DIR = FIXTURES_DIR / "different"
SILENCE_DIR = FIXTURES_DIR / "silence"
MP3_DIR = FIXTURES_DIR / "mp3"

# Test files to download from kozco.com
TEST_FILES = [
    {
        "url": "https://www.kozco.com/tech/piano2.wav",
        "filename": "piano2.wav",
        "description": "Piano trill, 6.3 seconds, stereo",
    },
    {
        "url": "https://www.kozco.com/tech/LRMonoPhase4.wav",
        "filename": "LRMonoPhase4.wav",
        "description": "Voice test, 39 seconds, stereo",
    },
    {
        "url": "https://www.kozco.com/tech/organfinale.wav",
        "filename": "organfinale.wav",
        "description": "Organ solo, 13 seconds, stereo",
    },
]


def download_file(url, destination):
    """Download a file from URL to destination."""
    print(f"Downloading {url}...")
    try:
        # Note: verify=False is used here because kozco.com has SSL issues
        # This is acceptable for test data from a known public source
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()

        with open(destination, "wb") as f:
            f.write(response.content)

        print(f"  -> Saved to {destination}")
        return True
    except Exception as e:
        print(f"  -> ERROR: Failed to download: {e}")
        sys.exit(1)


def create_silence_wav(filename, duration=1.0, sample_rate=44100, channels=2):
    """Create a WAV file containing silence."""
    print(f"Creating silent WAV file: {filename}")

    num_samples = int(duration * sample_rate)

    with wave.open(str(filename), "w") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Write silent samples (all zeros)
        for _ in range(num_samples):
            for _ in range(channels):
                wav_file.writeframes(struct.pack("<h", 0))

    print(f"  -> Created {filename}")


def extract_clip(source_file, dest_file, duration_seconds=5.0):
    """Extract the first N seconds from a WAV file."""
    print(f"Extracting {duration_seconds}s clip from {source_file.name}...")

    with wave.open(str(source_file), "rb") as source:
        params = source.getparams()
        frames_to_read = int(duration_seconds * params.framerate)
        frames_to_read = min(frames_to_read, params.nframes)

        audio_data = source.readframes(frames_to_read)

        with wave.open(str(dest_file), "wb") as dest:
            dest.setparams(params)
            dest.writeframes(audio_data)

    print(f"  -> Created {dest_file}")


def copy_file(source, destination):
    """Copy a file."""
    print(f"Copying {source.name} to {destination}...")
    with open(source, "rb") as src:
        with open(destination, "wb") as dst:
            dst.write(src.read())
    print(f"  -> Created {destination}")


def create_pcm_from_ieee_float(source_file, dest_file):
    """Convert IEEE Float WAV to PCM WAV format."""
    import numpy as np

    # Import InputFile from parent directory
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from InputFile import InputFile

    print(f"Converting {source_file.name} from IEEE Float to PCM...")

    # Read IEEE Float version
    src = InputFile(str(source_file))
    samples = src.get_audio_samples(src.total_samples)
    channels = src.channels
    sample_rate = src.sample_rate
    src.close()

    # Convert float32 (-1.0 to 1.0) to int16 (-32768 to 32767)
    samples_int16 = np.clip(samples * 32767, -32768, 32767).astype(np.int16)

    # Write as PCM WAV
    with wave.open(str(dest_file), "wb") as dst:
        dst.setnchannels(channels)
        dst.setsampwidth(2)  # 2 bytes = 16 bits
        dst.setframerate(sample_rate)

        # Interleave channels and write
        interleaved = np.empty((channels * samples_int16.shape[1],), dtype=np.int16)
        for ch in range(channels):
            interleaved[ch::channels] = samples_int16[ch]
        dst.writeframes(interleaved.tobytes())

    print(f"  -> Created {dest_file}")


def convert_wav_to_mp3(wav_file, mp3_file):
    """Convert WAV file to MP3 using ffmpeg if available."""
    import shutil
    import subprocess

    # Check if ffmpeg is available
    if shutil.which("ffmpeg") is None:
        print(f"⚠️  ffmpeg not found, skipping MP3 conversion for {wav_file.name}")
        return False

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(wav_file),
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "192k",
                "-y",  # overwrite
                str(mp3_file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"✓ Converted {wav_file.name} to MP3")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to convert {wav_file.name}: {e.stderr}")
        return False


def generate_mp3_test_files():
    """Generate MP3 test files from existing WAV files."""
    mp3_dir = FIXTURES_DIR / "mp3"
    mp3_dir.mkdir(exist_ok=True)

    # Convert base WAV files to MP3
    base_wavs = [
        (BASE_DIR / "piano2.wav", "Piano trill MP3"),
        (BASE_DIR / "LRMonoPhase4.wav", "Voice test MP3"),
        (BASE_DIR / "organfinale_pcm.wav", "Organ solo MP3 (from PCM)"),
    ]

    mp3_files = []
    for wav_file, description in base_wavs:
        if wav_file.exists():
            mp3_file = mp3_dir / f"{wav_file.stem}.mp3"
            if convert_wav_to_mp3(wav_file, mp3_file):
                mp3_files.append((mp3_file.name, description))

    return mp3_files


def create_manifest(mp3_files=None):
    """Create a manifest.json file documenting all test files."""
    manifest = {
        "description": "Test fixtures for AudioCompare end-to-end tests",
        "source": "Downloaded from kozco.com (public domain test files)",
        "files": {
            "base": [
                {"name": f["filename"], "description": f["description"]}
                for f in TEST_FILES
            ],
            "copies": "Exact copies of base files for match testing",
            "different": "Different audio files for no-match testing",
            "silence": "Silent WAV files for edge case testing",
        },
    }

    # Add MP3 files to manifest if they exist
    if mp3_files:
        manifest["files"]["mp3"] = [
            {"name": name, "description": desc} for name, desc in mp3_files
        ]

    manifest_path = FIXTURES_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Created manifest at {manifest_path}")


def main():
    """Main function to download and prepare all test files."""
    print("=" * 60)
    print("AudioCompare Test File Setup")
    print("=" * 60)
    print()

    # Check if files already exist
    base_files_exist = all((BASE_DIR / f["filename"]).exists() for f in TEST_FILES)
    pcm_version_exists = (BASE_DIR / "organfinale_pcm.wav").exists()

    if base_files_exist and pcm_version_exists:
        print("Base test files already exist. Skipping setup.")
        print("To re-run setup, delete the test/test_fixtures/ directory.")
        return

    # If only PCM version is missing, just create it
    if base_files_exist and not pcm_version_exists:
        print("Creating missing PCM version of IEEE Float file...")
        print("-" * 60)
        create_pcm_from_ieee_float(
            BASE_DIR / "organfinale.wav", BASE_DIR / "organfinale_pcm.wav"
        )
        print()
        print("=" * 60)
        print("Setup complete! Test files are ready.")
        print("=" * 60)
        return

    # Download base test files
    print("Step 1: Downloading base test files")
    print("-" * 60)
    for file_info in TEST_FILES:
        destination = BASE_DIR / file_info["filename"]
        download_file(file_info["url"], destination)
    print()

    # Create exact copies for match testing
    print("Step 2: Creating exact copies for match testing")
    print("-" * 60)
    copy_file(BASE_DIR / "piano2.wav", COPIES_DIR / "piano2_copy.wav")
    copy_file(BASE_DIR / "organfinale.wav", COPIES_DIR / "organfinale_copy.wav")
    print()

    # Copy different files to different directory
    print("Step 3: Organizing files for no-match testing")
    print("-" * 60)
    copy_file(BASE_DIR / "piano2.wav", DIFFERENT_DIR / "piano2.wav")
    copy_file(BASE_DIR / "organfinale.wav", DIFFERENT_DIR / "organfinale.wav")
    copy_file(BASE_DIR / "LRMonoPhase4.wav", DIFFERENT_DIR / "LRMonoPhase4.wav")
    print()

    # Create clip from longer file
    print("Step 4: Creating partial clips for clip matching tests")
    print("-" * 60)
    extract_clip(
        BASE_DIR / "LRMonoPhase4.wav",
        COPIES_DIR / "LRMonoPhase4_clip5s.wav",
        duration_seconds=5.0,
    )
    print()

    # Create silent files
    print("Step 5: Creating silent WAV files")
    print("-" * 60)
    create_silence_wav(SILENCE_DIR / "silence1.wav", duration=1.0)
    create_silence_wav(SILENCE_DIR / "silence2.wav", duration=1.0)
    print()

    # Create PCM version of IEEE Float file for format compatibility testing
    print("Step 6: Creating PCM version of IEEE Float file")
    print("-" * 60)
    create_pcm_from_ieee_float(
        BASE_DIR / "organfinale.wav", BASE_DIR / "organfinale_pcm.wav"
    )
    print()

    # Generate MP3 test files (optional, requires ffmpeg)
    print("Step 7: Generating MP3 test files")
    print("-" * 60)
    mp3_files = generate_mp3_test_files()

    if mp3_files:
        print(f"\n✓ Generated {len(mp3_files)} MP3 test files")
    else:
        print("\n⚠️  No MP3 files generated")
        print("   MP3 tests will be skipped unless ffmpeg is installed")
        print("   To install ffmpeg:")
        print("     - macOS: brew install ffmpeg")
        print("     - Linux: sudo apt-get install ffmpeg")
    print()

    # Create manifest
    print("Step 8: Creating manifest file")
    print("-" * 60)
    create_manifest(mp3_files if mp3_files else None)
    print()

    print("=" * 60)
    print("Setup complete! Test files are ready.")
    print("=" * 60)
    print()
    print("File summary:")
    print(f"  Base files:      {len(list(BASE_DIR.glob('*.wav')))} files")
    print(f"  Copies:          {len(list(COPIES_DIR.glob('*.wav')))} files")
    print(f"  Different files: {len(list(DIFFERENT_DIR.glob('*.wav')))} files")
    print(f"  Silent files:    {len(list(SILENCE_DIR.glob('*.wav')))} files")
    if mp3_files:
        print(f"  MP3 files:       {len(mp3_files)} files")
    print()
    print("You can now run: uv run pytest test/ -v")


if __name__ == "__main__":
    main()
