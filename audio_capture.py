# audio_capture.py
"""
Capture simultanee micro + audio systeme (voix des autres participants)
sur Windows, via soundcard (loopback WASAPI natif, pas de driver a installer).
"""
import io
import wave
import threading
from typing import Optional

import numpy as np
import soundcard as sc


class DualAudioRecorder:
    """Enregistre micro + audio systeme en parallele, puis les mixe."""

    def __init__(self, samplerate: int = 16000, chunk_size: int = 1024):
        self.samplerate = samplerate
        self.chunk_size = chunk_size
        self._mic_frames = []
        self._sys_frames = []
        self._stop_event = threading.Event()
        self._mic_thread: Optional[threading.Thread] = None
        self._sys_thread: Optional[threading.Thread] = None
        self.is_recording = False

    def _record_mic(self):
        mic = sc.default_microphone()
        with mic.recorder(samplerate=self.samplerate, channels=1) as rec:
            while not self._stop_event.is_set():
                self._mic_frames.append(rec.record(numframes=self.chunk_size))

    def _record_system(self):
        speaker = sc.default_speaker()
        loopback = sc.get_microphone(id=str(speaker.name), include_loopback=True)
        with loopback.recorder(samplerate=self.samplerate, channels=1) as rec:
            while not self._stop_event.is_set():
                self._sys_frames.append(rec.record(numframes=self.chunk_size))

    def start(self) -> None:
        if self.is_recording:
            return
        self._mic_frames, self._sys_frames = [], []
        self._stop_event.clear()
        self._mic_thread = threading.Thread(target=self._record_mic, daemon=True)
        self._sys_thread = threading.Thread(target=self._record_system, daemon=True)
        self._mic_thread.start()
        self._sys_thread.start()
        self.is_recording = True

    def stop(self) -> bytes:
        if not self.is_recording:
            return b""
        self.is_recording = False
        self._stop_event.set()
        self._mic_thread.join(timeout=2)
        self._sys_thread.join(timeout=2)

        mic = np.concatenate(self._mic_frames, axis=0) if self._mic_frames else np.zeros((0, 1), dtype=np.float32)
        sysa = np.concatenate(self._sys_frames, axis=0) if self._sys_frames else np.zeros((0, 1), dtype=np.float32)

        if len(mic) == 0 and len(sysa) == 0:
            return b""

        n = max(len(mic), len(sysa))
        mic = np.pad(mic, ((0, n - len(mic)), (0, 0)))
        sysa = np.pad(sysa, ((0, n - len(sysa)), (0, 0)))

        # Mix : on attenue chaque piste pour eviter la saturation a l'addition
        mixed = (mic * 0.7 + sysa * 0.7)
        mixed = np.clip(mixed, -1.0, 1.0)
        pcm = (mixed * 32767).astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()