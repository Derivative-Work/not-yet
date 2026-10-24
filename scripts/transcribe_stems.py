"""Re-transcribe the pitched stems with Spotify's Basic Pitch (Bittner et al. 2022, ICASSP model, ONNX backend).
Ported from Sandbox Rhapsody, where Suno's MIDI proved incomplete for every pitched instrument; here it explains
0-26% of each stem's detected onsets (timing/midi_inventory.md), so the same re-transcription is the first step.

Per stem a frequency range keeps the model on the instrument (no bass notes from the guitar's low strings ringing,
and so on). Usage: .venv/bin/python -I scripts/transcribe_stems.py [stem ...]  ->  timing/transcriptions/<stem>.json
"""
import json
import sys
from pathlib import Path

from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.inference import Model, predict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from song import STEM  # noqa: E402

STEMS = {  # stem: (min Hz, max Hz, onset threshold, frame threshold, min note ms)
    "Keyboard": (60, 4200, 0.5, 0.3, 58),     # the music box / harp line: the comb
    "Percussion": (120, 4200, 0.5, 0.3, 58),  # vibraphone / celesta: the stars
    "Strings": (40, 2500, 0.45, 0.3, 80),     # pizzicato strings and flute
    "Guitar": (40, 2500, 0.5, 0.3, 58),       # electric piano, pad
    "Bass": (30, 220, 0.5, 0.3, 58),          # fundamentals only (Sandbox Rhapsody: 2nd harmonics read as octave jumps)
}


def main():
    model = Model(ICASSP_2022_MODEL_PATH)
    out = Path("timing/transcriptions")
    out.mkdir(parents=True, exist_ok=True)
    for stem in sys.argv[1:] or STEMS:
        lo, hi, on_t, fr_t, min_ms = STEMS[stem]
        _, midi, notes = predict(STEM.format(stem), model, onset_threshold=on_t,
                                 frame_threshold=fr_t, minimum_note_length=min_ms, minimum_frequency=lo,
                                 maximum_frequency=hi, melodia_trick=True)
        ev = sorted(({"t": round(float(s), 4), "end": round(float(e), 4), "pitch": int(p), "vel": int(round(a * 127))}
                     for s, e, p, a, _ in notes), key=lambda n: (n["t"], n["pitch"]))
        (out / f"{stem.lower()}.json").write_text(json.dumps(
            {"stem": stem, "model": "basic-pitch 0.4.0 (ICASSP 2022, ONNX)",
             "params": dict(zip(["min_hz", "max_hz", "onset_threshold", "frame_threshold", "min_note_ms"],
                                STEMS[stem])), "notes": ev}) + "\n")
        midi.write(str(out / f"{stem.lower()}.mid"))
        print(stem, len(ev), "notes")


if __name__ == "__main__":
    main()
