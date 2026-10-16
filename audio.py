"""
Procedural Audio & Music Synthesizer using NumPy, standard wave, and Pygame Mixer.
Generates all combat SFX and atmospheric multi-layered music tracks in memory.
Gracefully handles missing audio hardware.
"""

import io
import wave
import math
import numpy as np
import pygame


class AudioManager:
    """Synthesizes and plays atmospheric music and responsive combat sound effects."""

    SAMPLE_RATE = 22050

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sfx_volume = 0.65
        self.music_volume = 0.45
        self.current_music_name = None
        self.sfx_bank = {}
        self.music_bank = {}
        self.music_channel = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=self.SAMPLE_RATE, size=-16, channels=1, buffer=512
                )
            pygame.mixer.set_num_channels(16)
            self.music_channel = pygame.mixer.Channel(0)
            self.enabled = True
            self._generate_all_audio()
        except pygame.error:
            self.enabled = False

    @classmethod
    def make_wav_bytes(cls, samples: np.ndarray) -> bytes:
        """Converts normalized float32 numpy array (-1.0..1.0) into WAV byte buffer."""
        clipped = np.clip(samples, -1.0, 1.0)
        pcm16 = (clipped * 32767.0).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(cls.SAMPLE_RATE)
            wav_file.writeframes(pcm16.tobytes())
        return buf.getvalue()

    def _sound_from_samples(self, samples: np.ndarray) -> pygame.mixer.Sound:
        wav_bytes = self.make_wav_bytes(samples)
        return pygame.mixer.Sound(file=io.BytesIO(wav_bytes))

    def _generate_all_audio(self):
        """Synthesizes all game SFX and ambient music loops procedurally."""
        sr = self.SAMPLE_RATE

        # 1. Jump SFX: rising airy pitch
        t = np.linspace(0, 0.14, int(sr * 0.14), endpoint=False)
        freq = np.linspace(190, 460, len(t))
        env = np.exp(-t * 14.0)
        self.sfx_bank["jump"] = self._sound_from_samples(
            0.5 * np.sin(2 * np.pi * np.cumsum(freq) / sr) * env
        )

        # 2. Dash SFX: filtered whoosh + low pulse
        t = np.linspace(0, 0.18, int(sr * 0.18), endpoint=False)
        rng = np.random.default_rng(42)
        noise = rng.uniform(-1, 1, len(t))
        kernel = np.ones(12) / 12.0
        filtered = np.convolve(noise, kernel, mode="same")
        sweep = np.sin(2 * np.pi * np.linspace(260, 90, len(t)) * t)
        env = np.sin(np.pi * t / 0.18) ** 1.5
        self.sfx_bank["dash"] = self._sound_from_samples((0.6 * filtered + 0.4 * sweep) * env)

        # 3. Slash SFX: crisp metallic swish
        t = np.linspace(0, 0.11, int(sr * 0.11), endpoint=False)
        noise = rng.uniform(-1, 1, len(t))
        kernel = np.ones(5) / 5.0
        swish = np.convolve(noise, kernel, mode="same")
        ring = np.sin(2 * np.pi * np.linspace(900, 320, len(t)) * t)
        env = np.exp(-t * 24.0)
        self.sfx_bank["slash"] = self._sound_from_samples((0.65 * swish + 0.35 * ring) * env)

        # 4. Hit SFX: crunchy impact + sub thump
        t = np.linspace(0, 0.15, int(sr * 0.15), endpoint=False)
        thump = np.sin(2 * np.pi * np.linspace(180, 48, len(t)) * t)
        crunch = np.sign(np.sin(2 * np.pi * 310 * t)) * 0.35
        env = np.exp(-t * 20.0)
        self.sfx_bank["hit"] = self._sound_from_samples((0.7 * thump + crunch) * env)

        # 5. Enemy Death: resonant shatter
        t = np.linspace(0, 0.35, int(sr * 0.35), endpoint=False)
        f1 = np.sin(2 * np.pi * np.linspace(420, 95, len(t)) * t)
        f2 = np.sin(2 * np.pi * np.linspace(630, 140, len(t)) * t)
        env = np.exp(-t * 8.5)
        self.sfx_bank["enemy_death"] = self._sound_from_samples(0.5 * (f1 + f2) * env)

        # 6. Player Hurt: heavy dissonant sting
        t = np.linspace(0, 0.32, int(sr * 0.32), endpoint=False)
        w1 = np.sign(np.sin(2 * np.pi * 145 * t)) * 0.4
        w2 = np.sin(2 * np.pi * 154 * t) * 0.5
        env = np.exp(-t * 7.0)
        self.sfx_bank["player_hurt"] = self._sound_from_samples((w1 + w2) * env)

        # 7. Heal SFX: warm harmonic chime
        t = np.linspace(0, 0.45, int(sr * 0.45), endpoint=False)
        chord = (
            np.sin(2 * np.pi * 440 * t)
            + 0.7 * np.sin(2 * np.pi * 554.37 * t)
            + 0.6 * np.sin(2 * np.pi * 659.25 * t)
        ) / 2.3
        env = np.sin(np.pi * t / 0.45) * np.exp(-t * 3.0)
        self.sfx_bank["heal"] = self._sound_from_samples(chord * env)

        # 8. Spell SFX: arcane laser-chime
        t = np.linspace(0, 0.28, int(sr * 0.28), endpoint=False)
        sweep = np.sin(2 * np.pi * np.cumsum(np.linspace(780, 220, len(t))) / sr)
        shimmer = np.sin(2 * np.pi * 1120 * t) * 0.3
        env = np.exp(-t * 10.0)
        self.sfx_bank["spell"] = self._sound_from_samples((0.7 * sweep + shimmer) * env)

        # 9. Boss Roar / Phase Shift
        t = np.linspace(0, 0.75, int(sr * 0.75), endpoint=False)
        growl = (
            np.sin(2 * np.pi * 75 * t + 3.0 * np.sin(2 * np.pi * 18 * t)) * 0.6
            + rng.uniform(-0.3, 0.3, len(t))
        )
        env = np.sin(np.pi * t / 0.75)
        self.sfx_bank["boss_roar"] = self._sound_from_samples(growl * env)
        self.sfx_bank["phase_shift"] = self.sfx_bank["boss_roar"]

        # 10. NPC Talk blip
        t = np.linspace(0, 0.06, int(sr * 0.06), endpoint=False)
        blip = np.sin(2 * np.pi * 360 * t) * np.exp(-t * 35.0)
        self.sfx_bank["npc_talk"] = self._sound_from_samples(blip * 0.5)

        # 11. Pickup / Checkpoint / Secret
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        notes = np.where(t < 0.2, 523.25, 783.99)
        bell = np.sin(2 * np.pi * notes * t) * np.exp(-t * 5.0)
        self.sfx_bank["pickup"] = self._sound_from_samples(bell * 0.6)
        self.sfx_bank["checkpoint"] = self.sfx_bank["heal"]
        self.sfx_bank["secret"] = self.sfx_bank["pickup"]

        # Generate Atmospheric Music Loops (6.4 seconds each, seamless loop)
        self.music_bank["title"] = self._build_music_loop(
            root_freq=110.0,
            scale_ratios=[1.0, 1.2, 1.5, 1.6, 1.8, 1.5, 1.2, 1.0],
            tempo_sec=0.8,
            pulse_strength=0.15,
        )
        self.music_bank["sanctuary"] = self._build_music_loop(
            root_freq=130.81,
            scale_ratios=[1.0, 1.125, 1.2, 1.5, 1.2, 1.125, 1.0, 0.75],
            tempo_sec=0.8,
            pulse_strength=0.1,
        )
        self.music_bank["ruins"] = self._build_music_loop(
            root_freq=98.0,
            scale_ratios=[1.0, 1.067, 1.2, 1.333, 1.5, 1.2, 1.067, 1.0],
            tempo_sec=0.7,
            pulse_strength=0.25,
        )
        self.music_bank["fungal"] = self._build_music_loop(
            root_freq=146.83,
            scale_ratios=[1.0, 1.2, 1.333, 1.5, 1.778, 1.5, 1.2, 1.0],
            tempo_sec=0.75,
            pulse_strength=0.18,
        )
        self.music_bank["citadel"] = self._build_music_loop(
            root_freq=123.47,
            scale_ratios=[1.0, 1.2, 1.5, 1.8, 2.0, 1.8, 1.5, 1.2],
            tempo_sec=0.65,
            pulse_strength=0.22,
        )
        self.music_bank["boss"] = self._build_music_loop(
            root_freq=82.41,
            scale_ratios=[1.0, 1.067, 1.2, 1.067, 1.414, 1.333, 1.2, 1.067],
            tempo_sec=0.35,
            pulse_strength=0.55,
        )
        self.music_bank["victory"] = self._build_music_loop(
            root_freq=146.83,
            scale_ratios=[1.0, 1.25, 1.5, 2.0, 1.5, 1.875, 2.0, 1.5],
            tempo_sec=0.7,
            pulse_strength=0.2,
        )

    def _build_music_loop(
        self, root_freq: float, scale_ratios: list, tempo_sec: float, pulse_strength: float
    ) -> pygame.mixer.Sound:
        """Synthesizes a melancholic dark-fantasy loop with bass drone, pad, and melody."""
        sr = self.SAMPLE_RATE
        num_steps = len(scale_ratios)
        total_dur = num_steps * tempo_sec
        total_samples = int(sr * total_dur)
        t = np.linspace(0, total_dur, total_samples, endpoint=False)

        # Deep atmospheric drone
        drone = (
            0.28 * np.sin(2 * np.pi * root_freq * t)
            + 0.16 * np.sin(2 * np.pi * (root_freq * 1.5) * t)
            + 0.08 * np.sin(2 * np.pi * (root_freq * 0.5) * t)
        )

        # Arpeggiated bell/harp motif
        melody = np.zeros(total_samples, dtype=np.float64)
        step_samples = int(sr * tempo_sec)
        for i, ratio in enumerate(scale_ratios):
            start = i * step_samples
            end = min(total_samples, start + step_samples)
            seg_len = end - start
            if seg_len <= 0:
                continue
            st = np.linspace(0, tempo_sec, seg_len, endpoint=False)
            note_freq = root_freq * 2.0 * ratio
            env = np.sin(np.pi * np.minimum(1.0, st / 0.04)) * np.exp(-st * 3.2)
            tone = (
                0.30 * np.sin(2 * np.pi * note_freq * st)
                + 0.12 * np.sin(2 * np.pi * (note_freq * 2.0) * st)
            ) * env

            # Optional rhythmic bass pulse for combat/boss tracks
            pulse_env = np.exp(-st * 11.0)
            pulse = pulse_strength * np.sin(2 * np.pi * (root_freq * 0.75) * st) * pulse_env
            melody[start:end] = tone + pulse

        mixed = (drone + melody) * 0.65
        return self._sound_from_samples(mixed)

    def play_sfx(self, name: str):
        if not self.enabled or self.muted:
            return
        snd = self.sfx_bank.get(name)
        if snd:
            snd.set_volume(self.sfx_volume)
            ch = pygame.mixer.find_channel(True)
            if ch and ch != self.music_channel:
                ch.play(snd)

    def play_music(self, track_name: str):
        if not self.enabled:
            return
        if track_name == self.current_music_name and self.music_channel.get_busy():
            return
        snd = self.music_bank.get(track_name)
        if snd and self.music_channel:
            self.current_music_name = track_name
            vol = 0.0 if self.muted else self.music_volume
            self.music_channel.set_volume(vol)
            self.music_channel.play(snd, loops=-1, fade_ms=500)

    def stop_music(self):
        if self.enabled and self.music_channel:
            self.music_channel.fadeout(400)
            self.current_music_name = None

    def set_sfx_volume(self, volume: float):
        self.sfx_volume = max(0.0, min(1.0, volume))

    def set_music_volume(self, volume: float):
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled and self.music_channel:
            self.music_channel.set_volume(0.0 if self.muted else self.music_volume)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.enabled and self.music_channel:
            self.music_channel.set_volume(0.0 if self.muted else self.music_volume)