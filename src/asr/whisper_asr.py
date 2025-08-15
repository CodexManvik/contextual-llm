import os
from typing import Optional, Tuple, Union

import numpy as np

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except Exception:
    FASTER_WHISPER_AVAILABLE = False


class WhisperASR:
    """Thin wrapper around faster-whisper for local, efficient ASR.

    Designed for RTX 3050 4GB: defaults to small model with int8_float16 on CUDA device 0.
    """

    def __init__(
        self,
        model_name_or_path: str = "small",
        device: str = "cuda",
        device_index: int = 0,
        compute_type: str = "int8_float16",
        language: Optional[str] = None,
        beam_size: int = 1,
        vad_filter: bool = True,
    ) -> None:
        if not FASTER_WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper is not installed. Install with: pip install faster-whisper")

        # Environment overrides
        model_name_or_path = os.getenv("WHISPER_MODEL", model_name_or_path)
        device = os.getenv("WHISPER_DEVICE", device)
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", compute_type)
        try:
            device_index = int(os.getenv("WHISPER_DEVICE_INDEX", str(device_index)))
        except Exception:
            device_index = 0

        self.language = os.getenv("WHISPER_LANGUAGE", language) or language
        self.beam_size = int(os.getenv("WHISPER_BEAM_SIZE", str(beam_size)))
        self.vad_filter = os.getenv("WHISPER_VAD_FILTER", "1" if vad_filter else "0") == "1"

        # Load model with robust fallback if CUDA/cuDNN is missing
        self.model = None
        last_error: Optional[Exception] = None

        # If CUDA is requested but we want to be safe, try CPU first
        if device == "cuda":
            try:
                # Try CUDA first
                self.model = WhisperModel(
                    model_name_or_path,
                    device=device,
                    device_index=device_index,
                    compute_type=compute_type,
                )
                print("✅ Whisper initialized on CUDA")
            except Exception as e:
                last_error = e
                print(f"⚠️ Whisper CUDA init failed: {e}")
                print("🔄 Falling back to CPU...")
                
                # Fallback to CPU
                try:
                    self.model = WhisperModel(
                        model_name_or_path,
                        device="cpu",
                        device_index=0,
                        compute_type="int8",
                    )
                    print("✅ Whisper initialized on CPU")
                except Exception as e2:
                    raise RuntimeError(f"Failed to initialize Whisper on both CUDA and CPU. CUDA: {last_error}; CPU: {e2}")
        else:
            # CPU mode - direct initialization
            self.model = WhisperModel(
                model_name_or_path,
                device="cpu",
                device_index=0,
                compute_type="int8",
            )
            print("✅ Whisper initialized on CPU")

    def transcribe_array(self, audio: Union[np.ndarray, bytes], sample_rate: int = 16000) -> str:
        """Transcribe a mono audio buffer to text.

        Accepts int16 numpy, float32 numpy in [-1, 1], or raw bytes of int16.
        """
        if isinstance(audio, (bytes, bytearray)):
            audio = np.frombuffer(audio, dtype=np.int16)

        if isinstance(audio, np.ndarray):
            if audio.dtype == np.int16:
                # Normalize to float32 in [-1, 1]
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype != np.float32:
                audio = audio.astype(np.float32)
        else:
            raise TypeError("audio must be bytes or numpy.ndarray")

        segments, _ = self.model.transcribe(
            audio=audio,
            language=self.language,
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
            temperature=0.0,
            without_timestamps=True,
            word_timestamps=False,
        )

        # Concatenate segments text
        parts = [seg.text.strip() for seg in segments if getattr(seg, "text", None)]
        text = " ".join([p for p in parts if p])
        return text.strip().lower()


