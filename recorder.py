"""
Enregistrement audio local depuis n'importe quel peripherique audio systeme.
Utilise sounddevice pour capturer le micro ou l'audio systeme (ex: BlackHole sur macOS).
"""
import io
import wave
from typing import List, Dict, Optional

import numpy as np
import sounddevice as sd


def list_input_devices() -> List[Dict]:
    """Retourne la liste des peripheriques d'entree disponibles."""
    devices = sd.query_devices()
    input_devices = []
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            input_devices.append({
                "index": i,
                "name": d["name"],
                "channels": d["max_input_channels"],
                "samplerate": int(d["default_samplerate"]),
            })
    return input_devices


class AudioRecorder:
    """
    Enregistreur audio en temps reel.
    Doit etre stocke dans st.session_state pour survivre aux reruns Streamlit.
    """

    def __init__(self, device_index: Optional[int] = None, samplerate: int = 16000):
        self.device_index = device_index
        self.samplerate = samplerate
        self._frames: List[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self.is_recording = False

    def start(self) -> None:
        if self.is_recording:
            return
        self._frames = []
        self._stream = sd.InputStream(
            device=self.device_index,
            samplerate=self.samplerate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()
        self.is_recording = True

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        self._frames.append(indata.copy())

    def stop(self) -> bytes:
        """Arrete l'enregistrement et retourne les bytes WAV."""
        if not self.is_recording:
            return b""
        self.is_recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return b""

        data = np.concatenate(self._frames, axis=0)
        pcm = (data * 32767).clip(-32768, 32767).astype(np.int16)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()
