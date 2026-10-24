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

## 2026-10-23T21:05:00-04:00 — Step 2: Suno take, drafting chat and audits logged retroactively

- **What:** Fetched the Suno share page and the drafting chat's share page with Sandbox Rhapsody's scripts. Extracted the take's metadata and submitted lyrics. Converted the chat to Markdown, and saved each audit's messages verbatim in `log/audits/`. Wrote `log/prompts/suno/takes.md`.
- **Commands:**
  - `cp ../sandbox-rhapsody/scripts/{fetch_share.mjs,fetch_suno.mjs,chat_snapshot_to_md.py,suno_meta.py} scripts/`; `package.json` and lock from Sandbox Rhapsody (renamed); `npm ci`
  - `node scripts/fetch_suno.mjs https://suno.com/s/3EJeKdHkJJEsodzS log/prompts/suno/fetch_accepted`; `.venv/bin/python -I scripts/suno_meta.py log/prompts/suno/fetch_accepted` (lyrics bounds changed to `[Verse 1]` … `Goodnight.`)
  - `node scripts/fetch_share.mjs https://claude.ai/share/b0788d14-90a8-4d6e-adbf-8ad3011e43c1 docs/drafting_chat/drafting_chat`; `.venv/bin/python -I scripts/chat_snapshot_to_md.py docs/drafting_chat/drafting_chat.json <url> > docs/drafting_chat/drafting_chat.md`
  - Audits: an inline Python script that writes chat messages 21–26 verbatim, two per auditor, to `log/audits/0{1,2,3}_*.md`
- **Outputs:** `docs/drafting_chat/drafting_chat.{json,html,txt,md}`, `log/prompts/suno/fetch_accepted/`, `log/prompts/suno/takes.md`, `log/audits/{README,01_gemini,02_chatgpt,03_glm}.md`
- **Findings:**
  - The take is Suno V6 (`chirp-hawk`), created 2026-10-23T08:28:20Z.
  - Suno's page lyrics equal v3.1. Step 1's doubled bridge line exists only in the MP3's lyrics tag, and the human confirms it isn't sung. So there is no lyric exception, and no submitted-vs-drafted difference.
  - The style prompt asks for music box and celesta. Suno added pizzicato strings, flute, bass, electric piano and a pad (step 1 MIDI inventory). That is an AI change, logged here, not a human one.
  - Each auditor's full response was a file attached to the chat. The public share doesn't expose attachments (`viewer_can_access_files: false`; `file_count: 1` on messages 21, 23 and 25). What the share does hold: Gemini's and ChatGPT's suggested lyrics, Claude's resolution tables, and Claude's summary of GLM's findings. The raw outputs are still needed from the human for N34, which shows them on screen.
  - Model versions: Gemini "Argon" (Gemini 4 Argon per message 22); ChatGPT's version is not recorded; GLM 5.3 Flash.
- **Why:** Brief, "Production rules": save the drafting chat and the audits verbatim with model, version and date, plus the resolution tables. Sandbox Rhapsody's pre-production step 2: log the audio retroactively.

## 2026-10-23T21:12:00-04:00 — Step 2b: raw auditor outputs saved

- **What:** The human saved each auditor's full response to `~/Downloads`. I copied them byte for byte into `log/audits/` (checked with `cmp`) and recorded each one's version, date and which lyric draft it audited. ChatGPT's version is the human's statement: "whatever the current free model is as of yesterday".
- **Commands:** `cp -p ~/Downloads/not-yet-{gemini,chatgpt,glm}-audit.md log/audits/0{1,2,3}_<auditor>_raw.md`; `cmp` each; `sha256sum log/audits/*_raw.md` (a46cd399…, 97a7c7d0…, 053c7988…)
- **Outputs:** `log/audits/{01_gemini,02_chatgpt,03_glm}_raw.md`; `log/audits/README.md` and the three per-audit notes updated
- **Findings:** Each auditor saw a different draft: Gemini saw v1, ChatGPT saw Gemini's revision and GLM saw v3. None audited v3.1 itself. GLM's "hallucination" line for N34 is in its section II.1. Gemini's and GLM's raw outputs also show the mistakes the brief wants on screen: Gemini calls the named events "hypothetical or fictionalized", and GLM pins verse 1 on Big Sleep and SQLite.
- **Why:** Brief, "Production rules": the auditors' outputs are saved verbatim with model name, version and date.

## 2026-10-23T21:58:00-04:00 — C1: style spec, look config, the set, and two test frames

- **What:** Wrote the style spec and `config/look.json`: the six colour-role hex values, materials, lighting, 60 fps, AgX Base Contrast. Vendored Sandbox Rhapsody's kit unchanged. Built the whole set as one procedural module: hall, plinth, glass room with frost and vault door, nursery, projected stars, street, shop window, lights and haze. Rendered the two C1 test frames at 720p and made a review sheet.
- **Commands:**
  - `cp ../sandbox-rhapsody/scenes/blender/lib/{sr_kit,sr_anim}.py scenes/blender/lib/`, unchanged. Source: Sandbox Rhapsody HEAD 5a56d3c; the files were last changed in f77185c. SHA-256: sr_kit 064ed831…, sr_anim c6894599…
  - `cp ../sandbox-rhapsody/assets/fonts/* assets/fonts/` (`sha256sum -c SHA256SUMS` OK)
  - `blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- renders/c1/c1_test_frame_{wide,close}.png 1280 720 64 {wide,close}` (about 21 s each on the GTX 970)
  - `.venv/bin/python -I scripts/c1_sheet.py renders/c1/c1_test_frame_wide.png renders/c1/c1_test_frame_close.png renders/c1/c1_sheet.jpg`
- **Outputs:** `style/style_spec.md`, `config/look.json`, `config/seeds.json` (the `stars` process), `scenes/blender/sets/nursery.py`, `scenes/blender/c1_test_frame.py`, `scripts/c1_sheet.py`, `scenes/blender/lib/{sr_kit,sr_anim}.py`, `assets/fonts/`, `renders/c1/c1_test_frame_{wide,close}.png`, `renders/c1/c1_sheet.jpg`
- **Iterations** (16-sample 720p drafts, judged by the agent):
  1. Interior all blue, door navy, shop blown out, street hidden. Raised the night-light (6→30 W) and the nursery fill (40→70 W), lowered the shop light (900→220 W, tubes 30→6), added the door's front light, raised the hill.
  2. The solid pastel door surround hid the nursery, and the street wasn't in the window's sightline. Made the door bay glass with a pastel ring frame. Placed the neighbor's house and the moon on the camera's line through the window, and brightened the sky.
  3. Frost was invisible (the shader read the plane's degenerate Z, and the coverage was mis-scaled), and the close camera sat on the door. Fixed both; the wide camera moved round so the crib and mobile show.
  4. The crib's end arches read as white ovals; flattened them. Moved the glint to the blanket's lip.
  - Mistake: I rendered drafts 1–3 to the same path, so only the last survives (`archive/renders/c1/draft_{wide,close}_superseded_c1-iteration.png`). That breaks the never-overwrite rule for intermediate renders. From here on every render gets a versioned name.
- **Kit notes:**
  - Some kit drivers made during the build were invalid at first evaluation: the music box's teeth and glow, and the mobile's hangers. `K.rebind_drivers()` before `K.refresh()` fixes them, as in Sandbox Rhapsody; none are left invalid.
  - Sandbox Rhapsody's music box glows amber, so it is recoloured on import (brief: amber belongs to the neighbor's window).
- **Self-assessment for C1:**
  - Holds up: the wide frame's composition (glowing glass room, stars, the amber window framed by the tall window, the shop and the tungsten slit) and the cold-out, warm-in split.
  - Weaker: the hall is very dark, apart from the haze, the spots and the moon patch. The shop window is still the brightest thing in the frame. The glint isn't visible in either frame.
  - Not in C1: the probe (C2), animation, and real reflections in the glass (planar probes, C4/C5).
- **Why:** Brief, checkpoint C1.
- **Status:** **C1 is ready for review.** The agent stops here for approval, per the brief.

## 2026-10-23T22:31:00-04:00 — C1 v2: darker, and four-pane windows for the "windows" play

- **What:** Revised C1 after the human's rejection (human interventions, 22:10). Exposure is now −0.4. The back wall's 4×8 grid window is now a 4.4 m four-pane cross window, and the front wall's taped window a 2.2 m one. The front window has a seeded hairline crack under its tape and a new one beside it that grows (`grow`, N10). I lowered the hill to 8 m so sky silhouettes the cross. The moon now sits in the back window's upper-left pane and the neighbor's amber window in its upper-right. I gave the tape a faint emission, since it read black. Added a third test framing (`hallwin`, the front window straight on) and generalised the review sheet to any number of frames.
- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- renders/c1/c1_v2_{wide,close,hallwin}.png 1280 720 64 {wide,close,hallwin}`
  - after the mullion and tape fixes: `… renders/c1/c1_v3_{wide,hallwin}.png 1280 720 64 {wide,hallwin}`
  - `.venv/bin/python -I scripts/c1_sheet.py "<title>" renders/c1/c1_v3_wide.png renders/c1/c1_v2_close.png renders/c1/c1_v3_hallwin.png renders/c1/c1_v2_sheet.jpg`
- **Outputs:** `scenes/blender/sets/nursery.py` (`crack`, `cross_window`, `wall_with_opening`, new `hall`), `scenes/blender/c1_test_frame.py`, `scripts/c1_sheet.py`, `config/look.json`, `config/seeds.json` (the `cracks` process), `style/style_spec.md`, `renders/c1/c1_v3_wide.png`, `renders/c1/c1_v2_close.png`, `renders/c1/c1_v3_hallwin.png`, `renders/c1/c1_v2_sheet.jpg`
- **Archived:**
  - Rejected (R1): `archive/renders/c1/c1_test_frame_{wide_rejected_too-bright-grid-window,close_rejected_too-bright}.png` and `c1_sheet_rejected_too-bright-grid-window.jpg`
  - Superseded: `c1_v2_wide_superseded_mullion-lost-against-hill.png` and `c1_v2_hallwin_superseded_tape-unlit.png`
- **Note for the shot list:** straight on, the backlit blue four panes are very close to the current Windows logo. N09 and N10 show the window as a reflection at an angle (brief), which keeps it a window. That gets checked at C4. The brief's set description still says "tall window"; I'll update the doc once you approve v2.
- **Why:** Human interventions, C1 rejection (R1).
- **Status:** **C1 v2 is ready for review.**

## 2026-10-23T22:45:00-04:00 — C1 approved: 30 fps; brief updated for the four-pane windows

- **What:** The human approved C1 v2 at 30 fps. I set `fps` to 30 and added `motion_blur_shutter` 0.5 in `config/look.json`, and updated the style spec's frame-rate section and C1 outcome. In the brief I changed three "tall window" phrases: the street bullet now describes the four-pane windows and the reason for them, N23 says "back window", and the moonlight clock says "back window". Re-exported the brief mirror.
- **Commands:** docs `update` on the brief (rev 24 → 27, three `find` replacements); docs `read` of the prose node, then `scripts/doc_to_md.py <read result> docs/brief.md`
- **Outputs:** `config/look.json`, `style/style_spec.md`, `docs/brief.md`
- **Why:** Human interventions, C1 approval (R1).
