"""Load Suno's MIDI files.

Suno writes key-signature meta events that mido can't decode (e.g. 12 sharps). The key is irrelevant to the
animation, so undecodable keys are kept as 'invalid:<sharps>:<mode>' instead of failing the whole file.
"""
import mido
import mido.midifiles.meta as meta
import pretty_midi

_orig_decode = meta.MetaSpec_key_signature.decode


def _tolerant_decode(self, message, data):
    try:
        _orig_decode(self, message, data)
    except meta.KeySignatureError:
        sharps = data[0] - 256 if data[0] > 127 else data[0]
        message.__dict__["key"] = f"invalid:{sharps}:{data[1]}"  # bypasses MetaMessage.check


meta.MetaSpec_key_signature.decode = _tolerant_decode


def load(path):
    """PrettyMIDI for `path`; pretty_midi skips key signatures it can't parse, so strip the invalid ones first."""
    mf = mido.MidiFile(path)
    for track in mf.tracks:
        track[:] = [m for m in track if not (m.type == "key_signature" and str(m.key).startswith("invalid:"))]
    return pretty_midi.PrettyMIDI(mido_object=mf)


def invalid_keys(path):
    return [m.key for t in mido.MidiFile(path).tracks for m in t if m.type == "key_signature" and str(m.key).startswith("invalid:")]
