import struct
import numpy as np
import miniaudio


class InputFile:
    def __init__(self, filename):
        """Open an Audio file with the given file path.
        Supported formats:
        - WAVE: PCM (format_tag 1) and IEEE Float (format_tag 3)
        - MP3: Decoded using miniaudio library

        MP3 files are decoded to memory on initialization using the miniaudio library.
        WAVE files are parsed and audio data is read from disk on demand.

        For WAVE files, this document http://www-mmsp.ece.mcgill.ca/documents/AudioFormats/WAVE/WAVE.html
        was used as a spec. We implement a limited subset of the WAVE format,
        supporting both PCM and IEEE Float audio data.

        At the end of this constructor:
        - For WAV: self.wav_file is positioned at the first byte of audio data
        - For MP3: self.mp3_samples contains decoded audio, self.mp3_sample_position = 0
        """

        # Store original filename for error messages
        self.original_filename = filename

        # Detect file format
        file_format = self.__detect_format(filename)

        if file_format == "wav":
            # Handle WAV files (existing logic)
            self.is_mp3 = False
            self.wav_file = open(filename, "rb")

            # At this point, audio file should have the canonical form(WAVE)
            self.wav_file.seek(4, 0)
            riff_size = InputFile.__read_size(self.wav_file)

            # Parse chunks to find fmt and data
            self.wav_file.seek(12, 0)  # Skip RIFF header
            fmt_data = None
            data_chunk_pos = None
            self.data_chunk_size = 0

            while True:
                chunk_id = self.wav_file.read(4)
                if len(chunk_id) < 4:
                    break

                chunk_size = InputFile.__read_size(self.wav_file)
                chunk_data_pos = self.wav_file.tell()

                if chunk_id == b"fmt ":
                    fmt_data = self.wav_file.read(chunk_size)
                elif chunk_id == b"data":
                    data_chunk_pos = chunk_data_pos
                    self.data_chunk_size = chunk_size
                    break  # Data chunk is usually last, can stop here

                # Move to next chunk
                self.wav_file.seek(chunk_data_pos + chunk_size, 0)

            if fmt_data is None:
                raise IOError("No fmt chunk found in WAV file")
            if data_chunk_pos is None:
                raise IOError("No data chunk found in WAV file")

            # Parse fmt chunk data
            self.format_tag = self.__read_ushort(fmt_data[0:2])
            self.channels = self.__read_ushort(fmt_data[2:4])
            self.sample_rate = self.__read_uint(fmt_data[4:8])
            self.block_align = self.__read_ushort(fmt_data[12:14])
            self.bits_per_sample = (
                self.__read_ushort(fmt_data[14:16]) if len(fmt_data) >= 16 else 16
            )

            # Position file at start of audio data
            self.wav_file.seek(data_chunk_pos, 0)
            self.total_samples = self.data_chunk_size // self.block_align

        elif file_format == "mp3":
            # Handle MP3 files (new logic)
            self.__decode_mp3_with_miniaudio(filename)

        else:
            # Unsupported format - provide helpful error message
            raise IOError(
                f"Unsupported audio format for file '{filename}'. "
                f"AudioCompare supports WAVE (PCM, IEEE Float) and MP3 files. "
                f"Please convert your file to one of these formats."
            )

    @staticmethod
    def __detect_format(filename):
        """Detect audio file format by reading magic bytes.

        Returns:
            'wav': RIFF WAVE file
            'mp3': MP3 file (ID3 tag or MPEG sync)
            'unknown': Unsupported format
        """
        with open(filename, "rb") as f:
            # Read first 12 bytes for format detection
            header = f.read(12)

            if len(header) < 4:
                return "unknown"

            # Check for WAV (RIFF header)
            if header[0:4] == b"RIFF" and len(header) >= 12 and header[8:12] == b"WAVE":
                return "wav"

            # Check for MP3
            # ID3v2 tag: starts with 'ID3'
            if header[0:3] == b"ID3":
                return "mp3"

            # MP3 without ID3: check for MPEG frame sync
            # MPEG frame sync: 11 bits set (0xFF 0xFx or 0xFF 0xEx)
            if header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
                return "mp3"

        return "unknown"

    def __decode_mp3_with_miniaudio(self, filename):
        """Decode MP3 file to PCM samples using miniaudio.

        Populates instance variables to match WAV interface:
        - self.mp3_samples: numpy array of decoded audio samples
        - self.sample_rate: samples per second
        - self.channels: number of audio channels
        - self.total_samples: total samples per channel
        - self.format_tag: set to 1 (PCM) since miniaudio decodes to PCM
        - self.bits_per_sample: 16 (miniaudio decodes to 16-bit PCM)
        - self.block_align: bytes per sample frame
        - self.is_mp3: True (flag for get_audio_samples to use memory)
        """
        try:
            decoded = miniaudio.decode_file(filename)
        except Exception as e:
            raise IOError(f"Failed to decode MP3 file '{filename}': {str(e)}")

        # miniaudio returns samples as a 1D array (interleaved channels)
        # Convert to numpy array with appropriate dtype
        samples = np.array(decoded.samples, dtype=np.int16)

        # Store metadata
        self.sample_rate = decoded.sample_rate
        self.channels = decoded.nchannels
        self.total_samples = decoded.num_frames  # samples per channel

        # Reshape from interleaved to channel-separated
        # miniaudio format: [L, R, L, R, ...] (if stereo)
        # our format: [[L, L, L, ...], [R, R, R, ...]]
        if self.channels > 1:
            self.mp3_samples = samples.reshape(-1, self.channels).T
        else:
            self.mp3_samples = samples.reshape(1, -1)

        # Set WAV-compatible metadata
        self.format_tag = 1  # PCM (miniaudio decodes to PCM)
        self.bits_per_sample = 16  # miniaudio decodes to 16-bit
        self.block_align = self.channels * 2  # 2 bytes per sample (16-bit)

        # Flag to indicate this is an MP3 file (for get_audio_samples)
        self.is_mp3 = True

        # Track current position in samples (for sequential reading)
        self.mp3_sample_position = 0

    @staticmethod
    def __is_wave_file(file):

        if not InputFile.__check_riff_format(file):
            return False
        if not InputFile.__check_wave_id(file):
            return False
        if not InputFile.__check_fmt(file):
            return False

        file.seek(20)
        data = file.read(2)
        file.seek(0)
        if not InputFile.__check_fmt_valid(data):
            return False
        return InputFile.__check_data(file)

    @staticmethod
    def __check_riff_format(file):
        RIFF = file.read(4)
        file.seek(0)
        return RIFF == b"RIFF"

    @staticmethod
    def __check_wave_id(file):
        file.seek(8)
        WAVE = file.read(4)
        file.seek(0)
        return WAVE == b"WAVE"

    @staticmethod
    def __check_fmt(file):
        file.seek(12)
        fmt = file.read(4)
        file.seek(0)
        return fmt == b"fmt "

    @staticmethod
    def __check_data(file):
        """Check if the file contains a data chunk."""
        file.seek(12)  # Skip RIFF header (4) + size (4) + WAVE (4)

        # Search for data chunk
        while True:
            chunk_id = file.read(4)
            if len(chunk_id) < 4:
                file.seek(0)
                return False

            chunk_size_bytes = file.read(4)
            if len(chunk_size_bytes) < 4:
                file.seek(0)
                return False

            if chunk_id == b"data":
                file.seek(0)
                return True

            # Skip this chunk's data
            chunk_size = int.from_bytes(chunk_size_bytes, "little")
            file.seek(chunk_size, 1)

    @staticmethod
    def __check_fmt_valid(data):
        format_tag = InputFile.__read_ushort(data[0:2])
        # Support PCM (1) and IEEE Float (3) formats
        return format_tag in (1, 3)

    @staticmethod
    def __read_size(file):
        """Read a 4 byte uint from the file."""
        return InputFile.__read_uint(file.read(4))

    @staticmethod
    def __read_ushort(data):
        """Turn a 2-byte little endian number into a Python number."""
        return struct.unpack("<H", data)[0]

    @staticmethod
    def __read_uint(data):
        """Turn a 4-byte little endian number into a Python number."""
        return struct.unpack("<I", data)[0]

    def get_audio_samples(self, n):
        """Get n audio samples from each channel.
        Returns an array of arrays. There will be one
        array for each channel, each with n samples in it.
        If we encounter end of file, we may return less than
        n samples. If we were already at end of file, we raise
        EOFError.

        For WAV files: reads from self.wav_file (positioned at audio data)
        For MP3 files: reads from self.mp3_samples (decoded in memory)
        """

        # Handle MP3 files (read from memory)
        if self.is_mp3:
            start = self.mp3_sample_position
            end = min(start + n, self.total_samples)

            if start >= self.total_samples:
                raise EOFError("Already at end of audio data")

            # Extract the requested samples
            samples = self.mp3_samples[:, start:end]

            # Update position for next read
            self.mp3_sample_position = end

            return samples

        # Handle WAV files (read from file) - EXISTING LOGIC
        # Determine the data type based on format tag
        if self.format_tag == 3:  # IEEE Float (32-bit)
            dtype = np.float32
            result_dtype = float
        else:  # PCM (16-bit integer)
            dtype = np.int16
            result_dtype = int

        data = np.fromfile(self.wav_file, dtype=dtype, count=n * self.channels)

        if len(data) == 0:
            raise EOFError("Already at end of audio data")

        result = np.zeros(
            (self.channels, len(data) // self.channels), dtype=result_dtype
        )
        for c in range(self.channels):
            result[c] = data[c :: self.channels]

        return result

    def get_channels(self):
        """Returns the number of channels in the file."""
        return self.channels

    def get_block_align(self):
        """Returns the number of bytes used in the file
        to represent a sample, multiplied by the number of channels."""
        return self.block_align

    def get_sample_rate(self):
        """Returns the numbers of samples per second, per channel."""
        return self.sample_rate

    def get_total_samples(self):
        """Returns the total number of samples per channel."""
        return self.total_samples

    def close(self):
        """Close the input file and free resources."""
        if hasattr(self, "wav_file"):
            self.wav_file.close()

        # For MP3 files, clear decoded samples to free memory
        if hasattr(self, "mp3_samples"):
            del self.mp3_samples
