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

## 2026-10-23T23:20:00-04:00 — C2: kit import, the probe in this set's light beside Sandbox Rhapsody's

- **What:**
  - Rendered Sandbox Rhapsody's own C1 close-up of its lead probe at 720p from that repo, as the reference. Its working tree was clean before and after; only this repo's `renders/c2/` was written.
  - Imported the probe with the kit's `sr_kit.probe(led_role="standby")`, unchanged, as `nursery.crib_probe()`. It lies at the crib's head end under the blanket's lip, scaled 3x: 20 cm across, a baby's size, with the kit's proportions, materials and rig untouched.
  - Rendered three Not Yet frames: `match` (the same rig, pose and camera offsets as the reference, on the dresser), `reveal` (N38: over the rail, iris open via `sing` 0.55, LED lit, rising out of the felt, clear glass) and `glint` (before N38: chassis hidden, glint only).
  - Made a 2x2 review sheet. Deepened the blanket colour, since `#9fb3cf` read white under the cream light.
- **Commands:**
  - `blender -b --factory-startup --python ../sandbox-rhapsody/scenes/blender/c1_test_frame.py -- $PWD/renders/c2/sr_reference_close.png 1280 720 64 close` (Sandbox Rhapsody at 5a56d3c, 138 s on the GTX 970)
  - `blender -b --factory-startup --python scenes/blender/c2_test_frame.py -- renders/c2/c2_v<N>_{reveal,glint,match}.png 1280 720 64 {reveal,glint,match}` (about 22 s each)
  - `.venv/bin/python -I scripts/c2_sheet.py renders/c2/c2_sheet.jpg renders/c2/sr_reference_close.png "…" renders/c2/c2_v3_match.png "…" renders/c2/c2_v4_reveal.png "…" renders/c2/c2_v3_glint.png "…"`
- **Outputs:** `scenes/blender/c2_test_frame.py`, `scenes/blender/sets/nursery.py` (`PROBE_SCALE`, `crib_probe`), `scripts/c2_sheet.py`, `config/look.json`, `style/style_spec.md` (`felt_blue`), `renders/c2/{sr_reference_close,c2_v3_match,c2_v4_reveal,c2_v3_glint}.png`, `renders/c2/c2_sheet.jpg`
- **Iterations** (archived under `archive/renders/c2/`, named by cause):
  1. Cameras read `matrix_world` before the depsgraph ran, so the reveal camera sat inside the set and the match probe was misplaced. Fixed with `view_layer.update()`.
  2. `hide_render` on the probe's root empty didn't hide its parts. Fixed with `hide_tree()`.
  3. The reveal camera looked through the slats; it now looks over the rail. The match probe stood behind the music box; the music box and monitor are hidden for that frame.
  4. Blanket recolour; an arms pass.
- **Self-assessment for C2:**
  - It reads as the same make: chrome sphere, bezel, iris, LED dome and arms, with only the light changed from amber to green. The match frame is the direct test.
  - The 3x scale is my call. The brief doesn't give a size, and a tennis-ball probe would be lost in a 1.3 m crib.
  - The brief's "two thin arms folded on the blanket" isn't met yet. The arms hang from just below the equator, so a probe sunk into the felt hides them. Staging the N38 rise (the probe lifts as the iris opens, arms coming to rest on the blanket) is animation work for C4.
  - From this angle the glint shows only as green spill on the crib's end board. Its framing is a C4 camera choice.
  - Not done here: the shop window's twin with mittens, built at C4 with the same function and `led_role="standby"`.
- **Why:** Brief, checkpoint C2.
- **Status:** **C2 is ready for review.** The agent stops here for approval, per the brief.

## 2026-10-24T00:40:00-04:00 — C3: MIDI validated against the stems, event sources, meter, word alignment, timing map, preview

- **What:**
  - Ported Sandbox Rhapsody's analysis behind one song module (`scripts/song.py`), so the stem paths are no longer hard-coded per script.
  - Inventoried and validated Suno's MIDI.
  - Re-transcribed the pitched stems with Basic Pitch, and chose a source per instrument.
  - Built the 3/4 bar grid, aligned every word, built the timing map at 30 fps, and rendered the C3 preview against the Suno mix.
- **Commands** (all `.venv/bin/python -I`, in this order):
  - `scripts/transcribe_stems.py` (Basic Pitch 0.4.0, ONNX on CPU, 22 s)
  - `scripts/event_sources.py`
  - `scripts/midi_inventory.py`
  - `scripts/align_words.py` (torchaudio MMS_FA on CPU, 43 s)
  - `scripts/meter.py`
  - `scripts/stem_envelopes.py`
  - `scripts/timing_map.py`
  - `scripts/c3_preview.py` (68 s); a 15 s test cut is archived at `archive/renders/c3/c3_preview_30-45_test.mp4`
- **Outputs:**
  - Scripts: `scripts/{song,attack_times,midi_inventory,transcribe_stems,event_sources,align_words,meter,stem_envelopes,timing_map,c3_preview}.py`
  - Timing: `timing/transcriptions/*.{json,mid}`, `timing/events/{keyboard,percussion,strings,guitar,bass}.json` (plus the inventory's per-track Suno event files), `timing/event_sources.md`, `timing/midi_inventory.md`, `timing/midi_validation.json`, `timing/words.json`, `timing/beats.json`, `timing/envelopes/*.npy`, `timing/timing_map.{json,md}`
  - Config and lyrics: `config/event_sources.json`, `config/meter.json`, `config/shot_anchors.json`, `lyrics/as_sung.txt`
  - Render: `renders/c3/c3_preview.mp4` (960×540, 30 fps, 246.36 s)
- **Findings:**
  - **Suno's MIDI runs 176 ms early** in every file (per stem: +174 to +195 ms, measured as the shift that maximises coverage of the stem's detected onsets). Unshifted, it looked unusable (0–26% coverage). Shifted, the music box track is "usable": 5.5 ms median and 17.5 ms p95 scatter, 0.99 support. Every other instrument track passes after a small shift. The two Vocals tracks fail validation, but voices are timed by the word alignment, not the MIDI. Sandbox Rhapsody's Suno MIDI was 6–14 ms early, so the offset differs per song and must be measured every time.
  - **Events:** for every instrument, the union wins: Suno's notes (offset applied), plus Basic Pitch's where Suno has no note within 50 ms and the stem's onset rises. It covers 54–75% of each stem's detected onsets at 0.96–1.0 support (`timing/event_sources.md`). Music box 1,549 events; celesta 472; strings 659; e-piano/pad 835; bass 65.
  - **Stems:** the Percussion stem is a vibraphone/celesta (pitched), not a kit, so it is judged as plucked. Keyboard is the music box/harp line and plays throughout. The band (strings, e-piano, bass) plays mainly from 30 to 120 s and from 204 to 216 s.
  - **Beats:** Suno's tempo map is the beat grid (identical in every file, 525 beats), moved by the offset and a further −6.9 ms fine shift to the music box's onsets. Tempo breathes: about 109 bpm at the start, about 145 in the choruses, about 100 in the bridge.
  - **Bars:** I tried beat_this (CPJKU), a dedicated downbeat tracker; installing it from GitHub was blocked by the permission classifier (external code). Downbeats are instead chosen by dynamic programming over the grid, scoring music box, bass and guitar onsets plus sung word starts, with a penalty on 2- or 4-beat bars. Result: 176 bars, 167 of 3 beats, 5 of 2, 3 of 4. The three consecutive 2-beat bars at 42.4–44.8 s may be a real hemiola at the chorus cadence, or a grid error; that's for the ear check.
  - **Words:** all 38 lines are aligned. The voice enters at 11.08 s (Suno's vocal MIDI, offset applied, at 11.0 s). Nine words score below 0.3: "weigh", "billionaires' toys", "it?", "Goodnight." and others (`timing/timing_map.md`).
  - **Outro conflict, proposal only, not applied to any audio:** the brief stops the music box at the pen scratch (N39), but Suno's music box plays on to 245.8 s. Proposal: make the stop in the edit (Folks Like Us rule). The music cuts to silence at the end of "signed" (229.42 s) with a pen scratch; "Goodnight." (232.97 s) plays from the vocal stem alone; black at 233.94 s (N40); the CRT line at 235.44 s (N41). The preview plays the unedited mix and marks these points.
- **Why:** Brief, checkpoint C3; Sandbox Rhapsody's steps 4–5.
- **Status:** **C3 is ready for review.** The human checks the preview by ear; corrections go in the intervention log.

## 2026-10-24T01:55:00-04:00 — C3 revision: beat_this beat grid, crosstalk removed, score preview

- **What:** Three changes after the human's C3 review (human interventions, 00:50).
  1. **Beats and bars rebuilt with beat_this** (CPJKU, pinned at b95c8ab, checkpoint final0, approved by the human).
     - Suno's grid agreed with beat_this 81–100% while the band plays (30–120 s), but only 12–41% in the intro, bridge and outro, where it dropped to 95–115 bpm.
     - The lyric lines show the song doesn't slow down: every line spans 4.6–5.6 s, four bars of three beats.
     - New method: dynamic-programming beat tracking (librosa) on beat_this's beat probability (mix and music box averaged), with a tempo prior from the line spacing (147.8 bpm) and high tightness. Bars come from dynamic programming on beat_this's downbeat probability plus line starts.
     - Result: 609 beats, median 150 bpm (p5–p95 143–158); 203 bars, 193 of 3 beats, 5 of 4, 4 of 2.
     - Bar phase check: 46 of 56 bass notes fall on beat 1, and the music box's lowest note is on beat 1 in 112 of 187 bars. Most lines start with a one-beat pickup.
     - The v1 meter (Suno grid) is archived in `archive/timing/meter_v1_suno_grid/`.
  2. **Crosstalk.** Suno's stems leak into each other. Before the fix, 69–86% of the other stems' events had a same-pitch-class event in the music box within 30 ms. Two filters in `scripts/event_sources.py`:
     - **Bleed:** a note is dropped where another stem is more than 10 dB louder at its pitch and moment. Against the vocal stem it is dropped only if its attack is also soft (rise over 25 ms): voice-dropped notes had a median rise of 52 ms, against 32 ms for kept ones.
     - **Duplicates:** an identical note left in two stems stays only in the louder one, unless they're within 3 dB (a unison).
     - Exact duplicates are gone. What remains is mostly octave doubling (`timing/event_sources.md`).
     - Events now: music box 1,006, celesta 108, strings 140, e-piano/pad 416, bass 45.
  3. **A score** (`scripts/score_build.py`, `score_render.py`, `c3_score_preview.py`, ported from Sandbox Rhapsody):
     - Parts: Vocals with the aligned lyrics; music box, strings and e-piano/pad on two staves each; celesta; bass.
     - Notes are at eighth-note resolution on the new grid, in the song's own bars.
     - Keys are G minor throughout, except the final chorus in E-flat major (music21 analysis per section).
     - 1080p, a cursor on the beat grid, and notes lighting while they sound.
- **Commands:**
  - `uv add "beat_this @ git+https://github.com/CPJKU/beat_this.git@b95c8ab0c58c2d9fcfd40508ae8dffbc05ac4f5c"` (checkpoint downloaded to `~/.cache/torch/hub/checkpoints/beat_this-final0.ckpt`, 77 MB)
  - `.venv/bin/python -I scripts/beats_beat_this.py`
  - `scripts/meter.py`, `scripts/timing_map.py`, `scripts/event_sources.py`, `scripts/midi_inventory.py`, `scripts/score_build.py`, `scripts/c3_score_preview.py` (4 min), `scripts/c3_preview.py`
- **Outputs:** `scripts/{beats_beat_this,meter,event_sources,score_build,score_render,c3_score_preview}.py`, `timing/beat_this.json`, `timing/beats.json`, `config/meter.json`, `timing/events/*.json`, `timing/event_sources.md`, `timing/timing_map.{json,md}`, `renders/c3/c3_score_preview.mp4` (primary), `renders/c3/c3_preview.mp4` (lanes)
- **Archived:** rejected (R1) `archive/renders/c3/c3_preview_rejected_unreadable-suno-grid-crosstalk.mp4`. Superseded: the test cut `c3_score_preview_34-50_test.mp4`, and the first full score and lane renders with the level-only bleed rule (`*_superseded_voice-bleed-rule.mp4`).
- **Open for the ear check:**
  - The soft chords dropped as voice leakage under the bridge's vocal (141.9 s, 143.1 s).
  - Whether the "celesta" (Percussion stem) is a real separate instrument. After the duplicate rule it has only 108 notes, mostly in the intro and the final chorus.
  - The irregular bars (`timing/timing_map.md`).
  - The outro edit proposal (unchanged).
- **Status:** **C3 is ready for re-review.**

## 2026-10-24T02:50:00-04:00 — C3 revision 2: events grouped by instrument, not stem

- **What:** Regrouped the events by the human's identification by ear (human interventions, 02:20).
  - The music box is the Keyboard and Percussion stems together.
  - The fingerstyle guitar is the Guitar and Bass stems together.
  - Strings is arco only.
- **How** (`scripts/event_sources.py`):
  - Each stem is still analysed and cleaned on its own: source choice, Suno offset, ghosts, inactive sections. Per-stem files moved to `timing/events/stems/`.
  - Bleed is now judged only against stems of other instruments, so the two halves of the music box (or of the guitar) no longer cancel each other.
  - An instrument's stems are merged; a note in both stems is kept once, from the louder stem.
  - Strings keep bowed notes only (rise ≥ 30 ms, duration ≥ 0.2 s): 75 plucked or short notes dropped as crosstalk. That includes Suno's "Pizzicato" and "Flute" labels, which were transcription guesses.
  - Duplicates are then judged between instruments.
  - Result: music box 1,149 events, guitar 340, strings 76.
  - The score shows Vocals, Music box (2 staves), Guitar (treble 8vb) and Strings (2 staves); the lane preview has the same instruments.
- **Brief consequence (open):** the brief places each new star on a celesta note, but the human hears no celesta. Proposed: stars on the music box's top-line notes, decided at C4 (`config/event_sources.json` → `stars`).
- **Also from the human (02:05):** the notes are "accurate enough to make a convincing video". On how much the bar grid matters: only the chair (beat 1), the mobile (downbeats), three focus pulls and the N18 flap use it. Everything else follows note and word onsets. The chair will rock on a steady 3-beat cycle nudged to the nearest downbeat, so an odd bar can't jerk it (C4).
- **Commands:** `.venv/bin/python -I scripts/event_sources.py`; `scripts/score_build.py`; `scripts/c3_score_preview.py`; `scripts/c3_preview.py`
- **Outputs:** `timing/events/{music_box,guitar,strings}.json`, `timing/events/stems/*.json`, `config/event_sources.json`, `timing/event_sources.md`, `scripts/{event_sources,score_build,c3_preview}.py`, `renders/c3/c3_score_preview.mp4`, `renders/c3/c3_preview.mp4`
- **Archived:** `archive/renders/c3/{c3_score_preview,c3_preview}_superseded_stem-not-instrument-grouping.mp4`
- **Status:** C3 ready for re-review.

## 2026-10-24T03:15:00-04:00 — C3 approved; outro as chosen; the pen scratch

- **What:** C3 is approved (human interventions, 03:00). Outro per the human's choice: the audio is not edited, and a code-synthesised pen scratch goes on top just after "signed" (229.42 s).
  - On screen, the chair stops and the stars freeze at the scratch, but the music box keeps turning while it is still heard (85 notes to 244.5 s), so no audible note goes without its pluck. This departs from the brief's "the music box stops", which assumed the music would stop. It keeps the sync rule.
  - Black after "Goodnight." (233.94 s), with the music box playing out in the dark. The CRT line opens 0.8 s after the audio ends (247.16 s, N41's "Silence"), then the fact card (248.16 s).
  - Stars: on the music box's melody notes (top line), the human's choice (C4).
- **Commands:** `.venv/bin/python -I scripts/timing_map.py`; `.venv/bin/python -I scripts/pen_scratch.py`; `ffmpeg -ss 220 -i <track> -i audio/sfx/pen_scratch.wav -filter_complex "[1:a]adelay=9420|9420[s];[0:a][s]amix=inputs=2:duration=first:normalize=0" renders/c3/outro_pen_scratch_preview.wav`
- **Outputs:** `scripts/pen_scratch.py`, `audio/sfx/pen_scratch.wav` (1.62 s, 48 kHz, 24-bit, seed 41), `config/audio.json`, `config/seeds.json`, `scripts/timing_map.py`, `timing/timing_map.{json,md}`, `config/shot_anchors.json`, `renders/c3/outro_pen_scratch_preview.wav`
- **Level:** over the scratch's 1.8 s, the mix's mean level rises from −32.9 to −29.2 dB. The level gets judged by ear at C5.
- **Why:** Human interventions, C3 approval (R1).

## 2026-10-24T03:35:00-04:00 — Pen scratch: the human-chosen recording replaces the synthesised one

- **What:**
  - Copied the human's download of Pixabay "scribble" (sound effect 6144; royalty-free, attribution not required) into `audio/sfx/` (`cmp` OK). It's 1.23 s, mono, 44.1 kHz, and the scribble starts at 0 s.
  - `config/audio.json` places it at 229.42 s with +11 dB gain (its peak is −24.9 dB), panned a little right, on top of the unedited track.
  - Archived the rejected synthesised sound and its script. Remixed the outro preview.
- **Commands:**
  - `cp -p ~/Downloads/freesound_community-scribble-6144.mp3 audio/sfx/`; `git mv scripts/pen_scratch.py archive/scripts/pen_scratch_rejected_not-a-pen.py`
  - `ffmpeg -ss 220 -i <track> -i audio/sfx/freesound_community-scribble-6144.mp3 -filter_complex "[1:a]aresample=48000,volume=11dB,pan=stereo|c0=0.95*c0|c1=c0,adelay=9420|9420[s];[0:a][s]amix=inputs=2:duration=first:normalize=0" renders/c3/outro_pen_scratch_preview.wav`
- **Outputs:** `audio/sfx/freesound_community-scribble-6144.mp3`, `config/audio.json`, `renders/c3/outro_pen_scratch_preview.wav`
- **Archived:** `archive/audio/sfx/pen_scratch_rejected_not-a-pen.wav`, `archive/scripts/pen_scratch_rejected_not-a-pen.py`, `archive/renders/c3/outro_pen_scratch_preview_rejected_synth.wav`
- **Level:** the mean over the scratch is −29.6 dB, against −32.9 dB for the track alone. The final level is set by ear at C5, on the mastered track.
- **Why:** Human interventions, 03:25 (R1, plus an exception for a recorded sound).

## 2026-10-24T05:10:00-04:00 — C4: the animatic

- **What:** The whole camera move at final timing, every anchor hit, low-res on the GTX 970: 640×360, Eevee at 8 samples, every second frame (3,510 frames in 51 min, 0.87 s/frame).
- **Set additions** (`scenes/blender/sets/nursery.py`):
  - The basement: the maintainer from behind, desk, lamp, laptop, peanut and donation jars, a 220-sheet paper avalanche with glowing sheets, and the mail slot with its flap, falling sheets and cold light through it.
  - Outside and in the hall: the moat (reflective ring with faint edges), the navy velvet rope on brass posts, the falling ticket and the drift against the glass.
  - The street: the road and the town's crack, the porch lights keyed per house, the far hills with 16 amber windows, the neighbor's walking glow.
  - The shop: the twin's mittened forearms over the blanket edge and the waiver clipboard with pen and string, the AVAILABLE tag, the screen placeholder.
  - The nursery: the music box's coin slot, the floor gaps, the ceiling call graph, and the mobile's ticket stacks.
  - Stars, call graph, crack and gaps use one reveal material: per-face birth and dim times against a frame-driven clock clamped at the pen scratch, so the stars freeze with one clamp.
- **Animation** (`scenes/blender/animate.py`): everything is keyed from the timing map and the C3 events. Nothing is keyed by hand. The module docstring has the full map. Highlights:
  - Comb: plucks on every music-box note (1,149).
  - Stars: 278 born on the melody, building per section, none on a key word; 4 dim.
  - Chair: one rock per bar; it stops at the pen scratch, where the stars freeze.
  - Mobile: steps on downbeats; its pieces lower on "bank", "browser", "cloud" and "week".
  - Moon: the moonlight clock (58° to 16°).
- **Camera** (`scenes/blender/camera_path.py`):
  - 49 keyed poses on the shot anchors, centripetal Catmull–Rom through time, baked per frame. It never stops or eases at a key.
  - It passes the door's 20° crack three times.
  - It cuts away through the plinth twice: the floor layers are hidden while the eye is inside them (81.9–82.5 s, 104.1–105.3 s).
  - Speed: median 0.15 m/s, p95 0.9, max 1.57 m/s, on the crossings to and from the shop. It isn't constant (brief). I evened it once: the crossings start earlier, the return has one key fewer, and N29 moved closer.
- **Iterations** (archived under `archive/renders/`):
  - Anchors v1: the note was 0.4 m too high (room-local coordinates), the basement was near-black, the moat invisible, and N09/N10 looked edge-on into the glass.
  - v2: the note text faced inward and N18 was black.
  - v3: N18's slot sat inside the ceiling slab.
  - Animatic v1: no cutaway, so 82 s showed solid beige inside the rug and plinth.
- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/anchors_v4 --anchors`
  - `… -- --out renders/c4/frames_v1 --step 2`, then `… --from 80 --to 86` and `--from 103 --to 107` after the cutaway
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v1 2 renders/c4/c4_animatic.mp4`
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v4 renders/c4/c4_anchor_sheet.jpg 6`
- **Outputs:**
  - Code and config: `scenes/blender/{animatic,animate,camera_path}.py`, `scenes/blender/sets/nursery.py`, `scripts/{animatic_assemble,contact_sheet}.py`, `config/instrument_map.json`
  - Renders: `renders/c4/c4_animatic.mp4` (252 s, with the track, the pen scratch and burned-in review captions: lyrics lighting word by word, shot IDs, the N02 label, placeholders for the 2D outro shots), `renders/c4/c4_anchor_sheet.jpg`
- **Not in C4, for C5:**
  - Real reflections in the glass (the texture pass's foreshadowing, and N09/N10's taped window). These need planar probes.
  - The projector's slow rotation sweeping the stars, dust in the beam, breaths brightening the projector, the baby monitor's screen.
  - The real pages at N33/N34 (R composite), the 2D outro (N41–N44), the vertical framing, and the thumbnail view re-aligned to the moved neighbor.
- **Status:** **C4 is ready for review.**

## 2026-10-24T10:12 — C4 review received

- The human asked for seven changes (see `log/human_interventions.md`), including one cut before "and windows are never quite mended" (an EXCEPTION to the brief's no-cut move). I'm making them as C4 v2.

## 2026-10-24T11:50 — C4 v2: the review's changes, the one cut at N10

- **The cut (N10, an EXCEPTION, human's call):**
  - At 52.00 s, on the beat after "…and" and right before "windows are never quite mended", the move cuts to the taped, cracked front window seen from outside. Through it, the glass room glows down the hall.
  - The new crack grows on "never". The camera then pushes in through the lower-left pane and pans slowly around the set to the door, which it passes at N11 + 2.6 s. There is no second cut.
  - `camera_path.py`: `CUT` splits the keys into two splines. `build()` holds the last frame before the cut and keys the new pose half a frame early, so nothing, motion blur included, interpolates across the cut.
  - The front window has no backdrop now: a far sky plane and a faint cold fill outside. The tape and cracks sit just off the glass on the outer face, so they read from outside, upper right as in the C1 frame.
- **Continuity (human):** the back window, the one seen after the cut (N23–N29), carries the same taped pane, glazed faintly. Its new crack grows with the front one's on "never" and stays.
- **N18:**
  - The mail slot is bigger and lit, cut through the basement ceiling, with a short glowing chute and a flap that hangs ajar between clatters.
  - Folded tickets push through it, crease first, on every other beat, and drop to the desk.
  - The camera is closer, under the slot.
- **N18 → N19:**
  - The plinth is hollow: a top slab on four stone sides, and the hall floor has a hole the plinth's size.
  - The cutaway hides only the slab, the rug, the basement ceiling and the floor gaps.
  - On the rise, the camera looks up at the crib and mobile, so neither the hall nor the town shows.
- **N20/N21:** the sticky note is printed on both sides and reads correctly from inside.
- **N25–N27 (the town):**
  - Eight more houses; every house has one or two lit windows that go out with its porch light.
  - The road now reaches the top of the hill, with a cross lane and 16 streetlights, each a head on a pole with a pool of light.
  - The streetlights go out down the hill on "killed"; two stay dark.
- **N31:** the shop's walls flickered: they started inside the hall wall, in the same planes as the opening's faces. The shop box now starts behind the wall. A frame-to-frame measure over N31–N32 changes smoothly, with no alternating jumps.
- **N32:**
  - The twin is the kit's probe at the crib scale, under a mound of blanket that covers its chassis (still hidden until N38, per the brief).
  - Its arms reach out from under the felt along the blanket, the mittens on their hands.
  - The camera is over the rail at 55 mm.
- **N33–N34:**
  - The camera holds 1.4 m from the screen, which fills most of the frame, from N33 to N34 + 5.8 s.
  - It returns faster (peak 1.96 m/s).
  - The note now falls at N35 + 1.2 s, framed from in front of the open door. The coin drops at N36 + 1.6 s.
- **N38:** the blanket has a nest, a cup the probe lies in, with the felt rising to its equator. It switches in with the probe 0.5 s before N38. The probe rides the blanket's breath, so the felt never passes through it. Its arms lie forward on the blanket (brief: "folded on the blanket").
- **Camera speed:** median 0.19 m/s, p95 1.53, max 1.96 at 201 s (the shop return; v1 1.57). The window entry peaks at 1.85 m/s.
- **Tools:**
  - `animatic.py --times` renders stills at chosen song seconds.
  - `scripts/review_sheet.py` makes a labelled grid of them.
  - Review rounds: `renders/c4/review_v2a`–`v2d`.
- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v2 --step 2` (3,510 frames, 0.96 s/frame)
  - `… -- --out renders/c4/anchors_v5 --anchors`
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v2 2 renders/c4/c4_animatic_v2.mp4`
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v5 renders/c4/c4_anchor_sheet_v2.jpg 6`
- **Archived:**
  - `archive/renders/c4/c4_animatic_v1_rejected_c4-review.mp4`
  - `archive/renders/c4/c4_anchor_sheet_v1_rejected_c4-review.jpg`
  - `archive/renders/c4_anchors_v4_rejected_c4-review/`
- **Outputs:** `renders/c4/c4_animatic_v2.mp4` (252 s), `renders/c4/c4_anchor_sheet_v2.jpg`.
- **Status:** **C4 v2 is ready for review.**

## 2026-10-24T13:11 — C4 v3: the music box held and readable, the rail cleared, the arms open the blanket

From the C4 v2 review (`log/human_interventions.md`, 11:57).

- **N36 (the music box):**
  - The box now faces the room, at scale 2, with its lid open on a hinge at 104° and a felt lining. A small warm key light falls on its comb and cylinder.
  - The camera arrives at N36 + 1.2 s at 40 mm and holds on the box until N37 + 1.8 s (about 7.5 s, v2 about 2 s), drifting only a few centimetres. Then it turns toward the walls.
- **N37/N38 (the rail):** the camera rises over the rail and looks down into the crib from 1.98 m to 1.84 m at 45 mm to 56 mm, so the rail crosses only the bottom of the frame.
- **N38 (the reveal):**
  - The quilt over the probe is now two folds hinged along the crib's length.
  - From N38 − 0.7 s the probe's arms reach up and forward, and the folds open (prop `open`, N38 − 0.4 s to N38 + 1.0 s). The arms then settle on the blanket.
  - The LED comes up as the folds open. The probe sits in its nest, and nothing passes through the felt.
  - At 720p the arms read only faintly while the folds open: they're under and behind the lips.
- **N32:** the COMING SOON tag moved to the hall side of the rail, clear of the crib, and it reads.
- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v3 --step 2` (3,510 frames)
  - `… -- --out renders/c4/anchors_v6 --anchors`
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v3 2 renders/c4/c4_animatic_v3.mp4`
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v6 renders/c4/c4_anchor_sheet_v3.jpg 6`
  - Review stills are in `renders/c4/review_v3a`–`v3c`.
- **Archived:**
  - `archive/renders/c4/c4_animatic_v2_rejected_c4-v2-review.mp4`
  - `archive/renders/c4/c4_anchor_sheet_v2_rejected_c4-v2-review.jpg`
  - `archive/renders/c4_anchors_v5_rejected_c4-v2-review/`
- **Outputs:** `renders/c4/c4_animatic_v3.mp4` (252 s), `renders/c4/c4_anchor_sheet_v3.jpg`.
- **Status:** **C4 v3 is ready for review.**

## 2026-10-24T13:20 — C4 v3 review received

N17's laptop screen to show warnings/CVEs; N32's clipboard clips through the bed. See `log/human_interventions.md`.

## 2026-10-24T14:05 — N17's advisory feed: the real bugs from the lyrics, sources checked

- **The human asked** which CVEs the first pass showed (they were made up) and asked for the ones the words allude to.
- **The allusions,** per the drafting chat's verse notes:
  - Verse 1, "twenty-seven-year ghosts": Mythos Preview's 27-year-old OpenBSD bug.
  - Bridge, "the old crack under most of the net": PHP2Shell.
- **Checked on 2026-10-24:**
  - **PHP2Shell:** CVE-2026-109618 and CVE-2026-109619, two critical PHP remote code execution flaws (CVSS v4.0 9.2), fixed in PHP 8.5.12, 8.4.27, 8.3.36 and 8.2.35. Sources: Help Net Security (2026-10-21), Bitsight, Tanium and Huntress.
  - **The OpenBSD bug:** a TCP SACK bug with no CVE. Anthropic's write-up (anthropic.com/research/mythos-preview) calls it "A 27-year-old OpenBSD bug" and links OpenBSD's fix, `pub/OpenBSD/patches/7.8/common/025_sack.patch.sig` (7.8 errata 025, 2026-03-25; 7.7 errata 031).
- **The page now lists:**
  - CVE-2026-109618 and CVE-2026-109619, both CRITICAL (header: "2 critical").
  - "OpenBSD errata 025", marked "27 years old".
  - Five noise rows: WARNING unused var / deprecated, and AI report unverified / duplicate / ???.
  - No IDs are made up.
- **Legibility:** the rows are set in Inter, because JetBrains Mono's dotted zero read as an 8 at 720p ("2826"). Checked in `renders/c4/review_v4e`–`v4f`.
- **The first v4 full render** (frames_v4) was stopped before it finished, to pick up this change. Its frames will be overwritten by the restart; frame sequences are not archived.

## 2026-10-24T14:30 — Brief: a second vertical cut, the windows (EXCEPTION, human)

- **Spec:**
  - Chorus 1, N07 (34.56 s) to just before N11 (about 64.7 s; N11 is 64.98), 30 s.
  - It runs from the sticky note through the taped pane and the new crack on "never" (N09/N10), the one cut to the cracked window from outside, and the push back in through it.
  - It ends on that push, fading out in the instrumental bar before verse 2. No fact card. It opens with the `AI-generated satire` label and has burned-in captions.
- **Deadline:** before Patch Tuesday, Tuesday 2026-11-10 (the second Tuesday of November).
- **Order of work:**
  - C5 renders this span (about 910 frames) first on the 5090 box.
  - It needs the mastered track (the human, R4).
  - The human publishes it (R4).
- **Brief:**
  - Section 7 has the new paragraph.
  - The deliverables now read "Two 9:16 vertical cuts".
  - The C6 checklist item covers both cuts, the windows cut first.
  - Updated in the Claude Doc (rev 30) and mirrored in `docs/brief.md`.
