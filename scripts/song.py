"""This song's files and stems, in one place for every analysis script (Sandbox Rhapsody hard-coded them in each)."""
TITLE = "Sleep, Little Secret"
TRACK = f"audio/track/{TITLE}.wav"  # the Suno mix; the mastered track replaces it in config/audio.json when it exists
STEM = f"audio/stems/{TITLE} ({{}}).wav"
MIDI = f"audio/stems/midi/{TITLE} ({{}}).mid"
STEMS = ["Vocals", "Backing Vocals", "Keyboard", "Percussion", "Strings", "Guitar", "Bass"]
