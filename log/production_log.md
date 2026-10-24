# Production log

Append-only. One entry per action: timestamp, step (shot ID where relevant), what, exact command/prompt/script, outputs, why.

## 2026-10-23T20:39:00-04:00 — Step 1: repo scaffolding and supplied audio

- **What:** Read the brief (Claude Doc rev 24) and, in full, the Ghost in the Machine and Sandbox Rhapsody briefs (`docs/brief.md` in each repo, their local Markdown mirrors). Created Sandbox Rhapsody's directory layout, `.gitignore`, the 50 MiB pre-commit hook, `scripts/manifest.sh`, `CLAUDE.md`, the logs, a Python env (Sandbox Rhapsody's dependencies, CPU PyTorch for this GTX 970 box) and `config/{seeds,render_profiles}.json`. Mirrored the brief to `docs/brief.md`. Copied the Suno mix and stems in from `~/Downloads` (originals left in place) and checked each copy's SHA-256 against its source (17/17 OK).
- **Commands:**
  - `mkdir -p log/prompts/{suno,other} log/audits scripts/hooks docs lyrics archive style timing shots config scenes/blender/{lib,sets} overlays assets renders deliverables reference audio/{track,stems/midi,master}`
  - `cp ../sandbox-rhapsody/{.gitignore,scripts/hooks/pre-commit,scripts/manifest.sh,scripts/doc_to_md.py,scripts/midi_io.py}` (manifest dir list trimmed to `audio renders takes transcripts archive`); `git config core.hooksPath scripts/hooks`
  - `pyproject.toml` from Sandbox Rhapsody's, renamed, PyTorch index `cpu` instead of `cu128`; `uv sync`
  - `cp ~/Downloads/"Sleep, Little Secret".{wav,mp3} audio/track/`; `cp ~/Downloads/"Sleep, Little Secret Stems.zip" audio/`; `unzip` into `audio/stems/`, MIDI moved to `audio/stems/midi/`; `sha256sum -c` against the sources
  - Brief: docs `read` of the doc's prose node, then `scripts/doc_to_md.py <read result> docs/brief.md`
  - `ffprobe -show_entries format_tags=lyrics-eng "audio/track/Sleep, Little Secret.mp3" > log/prompts/suno/lyrics_submitted.txt`
- **Outputs:** the files above; `lyrics/v3.1_drafted.txt` (the brief's lyric block); `log/prompts/suno/lyrics_submitted.txt` (the lyrics Suno stored in the MP3)
- **Findings:**
  - The track is Suno, so the brief's "generator" open item is answered: the MP3's comment tag reads `made with suno; created=2026-10-23T09:42:43Z; id=8289b42f-49cc-4433-b82b-65c70a1fa9ac`. Length 246.36 s, 48 kHz stereo.
  - The submitted lyrics differ from v3.1 in one place: the bridge line "It found the old crack under most of the net," appears twice. The only other differences are curly apostrophes. A quick faster-whisper pass (`small.en`, CPU, scratch only, not the C3 alignment) hears the line once, so the as-sung text likely matches v3.1 here. The human still needs to confirm by ear at C3.
  - Stems: Vocals, Backing Vocals, Keyboard, Strings, Guitar, Bass and Percussion, each with a MIDI file. By its MIDI, Keyboard is an orchestral harp line (1238 notes, 0–246 s), the likely music box. Percussion is a vibraphone line (247 notes), the likely celesta. There are no drums despite the stem's name. The MIDI tempo is about 115→112 bpm. Every MIDI file carries an undecodable key signature, as in Sandbox Rhapsody, so `scripts/midi_io.py` is reused.
- **Why:** Brief, "Production rules": inherited setup before the first commit; read both briefs in full before the first action.
- **Environment:** Claude Code (Opus 5.5); Blender 5.2.2 LTS; ffmpeg 8.0.1; uv 0.13.1; Node v24.22.0; git. GPU: GTX 970 4 GB, driver 580.178.04 (draft box; finals move to the RTX 5090). Disk: 138 GB free.
