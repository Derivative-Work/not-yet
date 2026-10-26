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

## 2026-10-24T15:00 — C4 v4: N17's advisory feed, N32's clipboard on the blanket

From the C4 v3 review and its follow-up (`log/human_interventions.md`, 13:20 and 14:05).

- **N17 (the laptop):**
  - The screen carries a security advisories page: an amber title bar, "1,024 new warnings · 2 critical", and eight rows. The real bugs are PHP2Shell's CVE-2026-109618 and CVE-2026-109619 (CRITICAL, marked in amber) and "OpenBSD errata 025 · 27 years old". The rest is noise (14:05 entry).
  - The camera at N17 is over the maintainer's right shoulder at 36 mm, easing to 40 mm by N17 + 3.2 s, so the page reads through the line.
  - Loose sheets that landed on the desk in front of the laptop now land on the floor.
  - N14's falling ticket now lands flat beside the laptop (it ended tilted against the screen). Its x spin ends on a whole turn.
- **N32 (the clipboard):** it stood against the shop crib's headboard and passed through it. It now lies on the blanket just past the mittens, reading the right way up from the hall, and rides the blanket's breath.
- **Housekeeping:** `renders/c4/review_v4a.log` (a review render's log) was deleted by mistake; its stills are kept.
- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v4 --step 2` (3,510 frames)
  - `… -- --out renders/c4/anchors_v7 --anchors`
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v4 2 renders/c4/c4_animatic_v4.mp4`
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v7 renders/c4/c4_anchor_sheet_v4.jpg 6`
  - Review stills are in `renders/c4/review_v4a`–`v4f`.
- **Archived:**
  - `archive/renders/c4/c4_animatic_v3_rejected_c4-v3-review.mp4`
  - `archive/renders/c4/c4_anchor_sheet_v3_rejected_c4-v3-review.jpg`
  - `archive/renders/c4_anchors_v6_rejected_c4-v3-review/`
- **Outputs:** `renders/c4/c4_animatic_v4.mp4` (252 s), `renders/c4/c4_anchor_sheet_v4.jpg`.
- **Status:** **C4 v4 is ready for review.**

## 2026-10-24T16:30 — C4 v5: the last grey-box geometry replaced (maintainer, laptop, shop easel, twin's blanket)

From the human's go-ahead (`log/human_interventions.md`, 15:20).

- **The maintainer (N15–N17):**
  - A felt doll like the nursery's toys, from behind, hunched over the laptop: hips in jeans, a hoodie torso leaning forward, the hood down and bunched on the upper back, a short neck, the head (hair) with ears.
  - The arms go shoulder → elbow → forearm → cuff → hand resting on the keys. The legs go thigh → knee → shin → shoe, under the desk.
  - The parts are rounded boxes, through a new `soft_box` helper: the size is baked into the mesh, then a wide bevel and one subdivision. A first pass subdivided scaled cubes, which turned every part into a ball (a snowman), and a torus hood read as a ring.
  - "breath" lifts the torso, head and upper arms. The forearms and hands stay on the keys, and the elbow joints hide the seam.
  - The figure moved from x 0.45 to 0.37, centred on the laptop.
  - The chair now has a seat, four legs, two back posts, a top rail and a lower rail.
- **The laptop (N16–N17):**
  - A keyboard of 48 keys and a space bar (one mesh), a trackpad and a hinge.
  - The lid is dark plastic; only the advisory page glows (before, the whole box emitted).
- **The shop's easel (N29–N37):** the screen stands on an easel in pale wood: two front legs, a back leg, a ledge.
- **The twin's blanket (N31–N32):**
  - The mound drapes: a softer dome, folds around the skirt, and raised ridges over the dome. The ridges only lift the felt, so it never cuts into the hidden chassis.
  - Clearance over the probe's sides is at least 7 mm under the felt's thickness.
- **Review stills:** `renders/c4/review_v5a`–`v5c`.
- **Render:**
  - Only the spans the changes can reach were re-rendered: 78–108.5 s (the basement, N14–N19) and 160–222 s (the shop, N29–N38). They went into `renders/c4/frames_v5`, seeded with a copy of `frames_v4`; the other frames are unchanged.
  - Checked: the shop isn't in frame before 160 s.
- **Commands:**
  - `cp -r renders/c4/frames_v4 renders/c4/frames_v5`
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v5 --step 2 --from 78 --to 108.5` (458 frames)
  - `… --from 160 --to 222` (931 frames)
  - `… -- --out renders/c4/anchors_v8 --anchors`
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v5 2 renders/c4/c4_animatic_v5.mp4`
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v8 renders/c4/c4_anchor_sheet_v5.jpg 6`
- **Archived (superseded, not rejected):**
  - `archive/renders/c4/c4_animatic_v4_superseded_greybox-geometry.mp4`
  - `archive/renders/c4/c4_anchor_sheet_v4_superseded_greybox-geometry.jpg`
  - `archive/renders/c4_anchors_v7_superseded_greybox-geometry/`
- **Not geometry, still for C5:**
  - the N33/N34 real pages;
  - the baby monitor receiver's picture;
  - the 2D outro (N41–N44);
  - planar reflections in the glass.
- **Outputs:** `renders/c4/c4_animatic_v5.mp4` (252 s), `renders/c4/c4_anchor_sheet_v5.jpg`.
- **Status:** **C4 v5 is ready for review.**

## 2026-10-25T08:05 — On the RTX 5090 box: environment updated, motion blur wired, draft720 retuned

From the human's direction (`log/human_interventions.md`, 07:39).

- **Import check:** all 504 files in `MANIFEST.sha256` verify on this box (`sha256sum -c`).
- **Box:**
  - RTX 5090 (32 GB), driver 595.99.02, CUDA 13.2, Ubuntu 26.04.1.
  - Eevee renders on the 5090 through OpenGL (`gpu.platform`: "NVIDIA GeForce RTX 5090/PCIe/SSE2").
- **Blender:** 5.2.2 → **5.2.3 LTS**. The snap moved from `latest/stable` to the `5.2lts/stable` track, so a 5.3 release can't change the look mid-production.
- **Python venv:**
  - The imported `.venv` pointed at the draft box's interpreter (`/home/derivative-work/...`) and couldn't run. It was rebuilt with `uv sync --python 3.12`.
  - A first attempt to set the old venv aside in the scratchpad ran out of /tmp quota partway, so the dead venv was deleted. Venvs are regenerable and never archived.
  - `pyproject.toml` changes:
    - torch/torchaudio from the CPU index to **cu128** (torch 2.8.0+cu128, sm_120 in its arch list). The version stays at 2.8.* so analysis re-runs match.
    - `tool.uv.environments` narrowed to x86_64 Linux. The lock had tried aarch64, which has no cu128 wheels.
    - The CPU `onnxruntime` that faster-whisper pulls is overridden away. It shares `onnxruntime-gpu`'s module and hid the CUDA provider.
  - Checked: torch runs on cuda; onnxruntime lists TensorRT, CUDA and CPU providers; ctranslate2 sees 1 CUDA device.
- **Node:** Puppeteer 24.43.1's Chrome 148 is cached. It launches as the scripts launch it (`headless: 'shell'`, `--no-sandbox`); AppArmor restricts user namespaces here too, as on the draft box.
- **ffmpeg:** 8.0.1, with libass and NVENC. The review cuts stay on libx264.
- **Motion blur was never on.** `config/look.json` carried `motion_blur_shutter: 0.5`, but `sr_kit.setup_render` never set `use_motion_blur`, so every C1–C4 frame rendered without it. `setup_render` now turns it on with the spec's shutter, and takes a `mb_steps` argument (Eevee re-evaluates the scene that many times inside the shutter).
- **The C4 animatic frames were 640×360, not 720p:** `animatic.py` defaults to 640×360, and the v1–v5 runs passed no `--size`.
- **`animatic.py`:**
  - New `--profile NAME`: size, samples and motion-blur steps from `config/render_profiles.json`. `--size` and `--samples` still override.
  - The scene build moved into `build()`, so the QC scripts build exactly what renders. The CLI is unchanged otherwise.
- **draft720 retuned on the 5090:**
  - Settings: 32 samples, 2 motion-blur steps (were 8 samples, no blur).
  - `scripts/qc_mbtest.py` rendered 74.5, 80.8 and 155.9 s at 1280×720 under (8,1), (16,1), (32,1), (32,2), (64,1) and (64,4); stills in `renders/qc/mbtest/`.
  - 8 samples leaves crawling grain in soft shadows (the floor under the crib rail at 80.8 s). 32 clears most of it. 64×4 is only slightly smoother.
  - Steps change the blur where the camera arcs fastest (155.9 s).
  - Cost: 0.34–0.6 s/frame over two continuous test spans, so about an hour for the 7,019 frames.
  - `final` gets 4 steps.
- **Commands:**
  - `sudo snap refresh blender --channel=5.2lts/stable`
  - `uv sync --python 3.12`
  - `blender -b --factory-startup --python scripts/qc_mbtest.py -- renders/qc/mbtest 74.5 80.8 155.9`
- **Status:** environment ready. The artifact check of the existing frames comes next, before any re-render.

## 2026-10-25T10:20 — Artifact check of the C4 v5 frames: one visible z-fight (the crib's arched ends), three latent; fixed

From the human's direction (`log/human_interventions.md`, 07:39): check the existing frames for z-fighting and similar artifacts before re-rendering.

- **New QC tools:**
  - `scripts/qc_flicker.py`: motion-compensated temporal pops. a and c are warped onto b with DIS optical flow, with a forward-backward check, so camera motion cancels.
    - A first pass without flow compensation flagged the camera's fast moves (155.9 s, 66.6 s, 199.5 s) and was discarded as a method. Its output is kept in `renders/qc/flicker_v5/`.
  - `scripts/qc_flicker_frames.py`: panels of the worst frames.
  - `scripts/qc_geometry.py`: coplanar overlapping triangles of different objects at every anchor, with depth-buffer precision at the camera's distance (clip_start 0.02 m).
  - `scripts/qc_raypeel.py` (+ `qc_raypeel_lib.py`, `qc_raypeel_crops.py`): rays peel through every surface to catch near-coincident curved surfaces.
  - `scripts/qc_flicker_cause.py`: renders a frame pair under shadow and ray-tracing variations, to isolate a flicker's cause.
- **What the frames showed (`renders/c4/frames_v5`, 640×360, 8 samples, every 2nd frame, no motion blur):**
  - **Edge crawl** on the thin mullions, glass edges, the door rim, the crib bars and the N17 page's small text. Sub-pixel aliasing at 360p and 8 samples, the stepping the style spec said to watch at C4.
  - **Sampling grain** in soft shadows (the floor under the crib rail at 80.8 s, the shop floor).
  - Both drop about 5–6× per pixel at draft720 (two test spans, 58–64 s and 174–178 s).
  - Stars, LEDs and the blanket's breath pop by design.
- **Z-fighting found:**
  - **The crib's arched ends (visible):** each arch disc was 3 cm thick at the same x as its 3 cm end board, so its smooth-shaded caps lay in the board's faces. A dark crescent jumped around on the end board every frame. It was plain on the shop crib at N31 (176–178 s) and present on the hero crib (N02–N40, down to 1.2 m).
    - The cause was traced: it survives shadow jitter, 2× shadow resolution, no ray tracing and no shadows (`renders/qc/cause_shop_arch/`). It fixes only with the geometry.
    - Fix: the arch is 2.4 cm thick, its caps 3 mm inside the board's faces.
    - Before/after: `renders/qc/shop_arch_before_after.png`.
  - **The plinth's steel band:** its top was level with the stone sides' tops (N02–N11). It now sits 5 mm under them. 3 mm was still marginal at N02's 16 m.
  - **The donation jar's coins (N15):** placed for a thinner desk top, two coins were buried in the desk and the third's face lay in its top. All three now stack on the desk, half a millimetre apart, so the jar shows the three coins the brief asks for.
  - **The basement collar:** its top was level with the hall floor and its ends flush with the plinth sides; seen only from inside the plinth during the cutaways. Its top is now 4 mm under the floor, its ends 1 cm inside the sides.
- **Flagged and left as they are:**
  - same-material flush joints, which can't show (plinth panels, frame pieces, the room's steel, paper folds, the maintainer's felt parts, collar corners);
  - slivers under 1 cm² (haze box, star projector);
  - faces hidden under other geometry (the rug under the crib posts);
  - the mail chute against the ceiling opening (same colour and roughness);
  - the door's chrome bead crossing its ring (an intersection seam; its dotted highlight is chrome aliasing);
  - the music box comb's tips against their teeth (a 0.05 mm overlap, in the vendored kit, untouched);
  - the probe's shell and lens (the Sandbox Rhapsody rig, untouched).
- **Checked after the fixes:**
  - `qc_geometry.py --shots N02 N15 N31 N38`: no fixed pair still flags, apart from the band at 3 mm, since widened to 5 mm.
  - The shop span re-rendered clean (`renders/qc/frames_draft720_fix1_b`).
  - Review stills at draft720: `renders/qc/review_fix1/`.
- **Housekeeping:**
  - The first geometry scan crashed writing its JSON (a numpy bool); fixed and re-run (`renders/qc/geometry_v5.log` is the crashed run, `geometry_v5b.log` the good one).
  - The two draft720 test spans were renamed to `frames_draft720_test_a/b`, so the manifest treats them as frame sequences.
- **Commands:**
  - `.venv/bin/python -I scripts/qc_flicker.py renders/c4/frames_v5 renders/qc/flicker_v5b`
  - `blender -b --factory-startup --python scripts/qc_geometry.py -- renders/qc/geometry_v5.json`
  - `blender -b --factory-startup --python scripts/qc_raypeel.py -- renders/qc/raypeel_v5.json --every 2`
  - `blender -b --factory-startup --python scripts/qc_raypeel_crops.py -- renders/qc/raypeel_v5.json renders/qc/raypeel_v5_crops --top 30`
  - `blender -b --factory-startup --python scripts/qc_flicker_cause.py -- renders/qc/cause_shop_arch 5329 715 268 795 328`
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/qc/frames_draft720_test_a --profile draft720 --from 58 --to 64` (and `_b` 174–178)
- **Status:** ready for the full re-render at draft720.

## 2026-10-25T11:05 — C4 v6: the full re-render at draft720 (1280x720, 30 fps, motion blur)
- **Render:** all 7,019 frames at draft720 (32 samples, 2 motion-blur steps, shutter 0.5), with the z-fight fixes of the previous step. It took 5,261 s on the RTX 5090, averaging 0.75 s/frame; the star-ceiling end of the move runs at about 1.2 s/frame. This is the first C4 render with motion blur applied and the first at 720p.
- **Outputs:**
  - `renders/c4/frames_v6/`
  - `renders/c4/anchors_v9/` (39 stills)
  - `renders/c4/c4_animatic_v6.mp4` (1280x720, 30 fps, 252.17 s, with the Suno master)
  - `renders/c4/c4_anchor_sheet_v6.jpg`
- **Flicker check** (`renders/qc/flicker_v6/`):
  - Per pixel and per frame, the pop rate is about 5x lower than v5 (`flicker_v5b`, which was 360p and sampled every second frame, so the comparison is rough).
  - The crib arch no longer flags.
  - The top runs are edge crawl on thin lines and small text: the N17 laptop text, the distant crib bars in the shop window, the window crack and the ceiling constellation lines. None of them is z-fighting.
  - At 4K they will be smaller relative to the pixel. Still worth a look at C5: the N17 text.
- **Archived** (superseded: 360p, no motion blur, crib-arch z-fight):
  - `archive/renders/c4/c4_animatic_v5_superseded_360p-no-motion-blur-arch-zfight.mp4`
  - `archive/renders/c4/c4_anchor_sheet_v5_superseded_360p-no-motion-blur-arch-zfight.jpg`
  - `archive/renders/c4_anchors_v8_superseded_360p-no-motion-blur-arch-zfight/`
  - `renders/c4/frames_v5/` stays in place (frame sequences are never archived).
- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v6 --profile draft720`
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/anchors_v9 --profile draft720 --anchors`
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v6 1 renders/c4/c4_animatic_v6.mp4`
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v9 renders/c4/c4_anchor_sheet_v6.jpg 6`
  - `.venv/bin/python -I scripts/qc_flicker.py renders/c4/frames_v6 renders/qc/flicker_v6`
- **Status:** C4 v6 is ready for human review (R1).

## 2026-10-25T11:40 — Audit for the remaining placeholder geometry (after the human's C4 v6 note)
The human: "a few more places of placeholder geometry like the laptop. See if you can find them all". I went over all 39 v6 anchor stills (`renders/c4/anchors_v9`) at full size and read the builder for every suspect in `scenes/blender/sets/nursery.py`. Nothing is changed yet.

- **Placeholder geometry, in the order it shows on screen:**
  1. **The maintainer's forearms and hands (N16–N17):** forearms are plain cylinders (`bar`) and hands are squashed spheres. In the N17 close-up over the laptop they read as rolling pins with blobs on the ends. There are no fingers, and nothing touches the keys.
  2. **The paper avalanche (N15–N17):** 220 identical flat A4 slabs at random tilts, so they cut through each other and the desk top. Nothing is curled, stacked or folded, and there's no print on them.
  3. **The "glowing" sheets are black slabs until N17 (a bug):** `mat_emission` with floor 0 and no surface shader, so before the glow starts they render pitch black. One shows as a black block on the desk at N16.
  4. **The ticket drift against the glass (N29–N37):** the same random-card scatter: 60 cards floating up to 12 cm off the floor at ±0.6 rad, not lying on it or on each other.
  5. **The peanut jar (N15):** 14 spheres.
  6. **The baby monitor camera on the dresser (N36–N37):** a ball on a pin on a disc. It reads as a joystick.
  7. **The shop twin's mittens (N31–N32):** stretched spheres on the probe's thin wrists. They read as eggs on pins.
  8. **The reveal quilt's folds (N38–N40):** two height-field strips with a 1.5 cm solidify and cut-off edges. There's no hem or rolled edge, so they read as shells sliced from a mound; the nest blanket's edge is the same.
  9. **The shop easel's legs (N33–N34):** the leg ends show as pointed stakes above the ledge and at the top.
- **Looked at and judged deliberate:**
  - the N33/N34 screen card "[ real page, composited at C5 ]" (a C5 composite, as planned);
  - the felt-toy style of the mobile pieces, the maintainer's body, and the stylised town silhouettes;
  - the mobile's ticket stacks (N13);
  - the vendored music box and probe (Sandbox Rhapsody, not remodelled).
- **Proposed:** fix 1–9 in one pass, then re-render only the spans they reach (N15–N17, N29–N40).
- **Status:** waiting for the human's go-ahead on the list (R1).

## 2026-10-25T13:10 — The nine placeholder fixes from the audit (human go-ahead, R1, 11:50)
All changes are in `scenes/blender/sets/nursery.py`.

- **New helpers:**
  - `capsule`: a round-ended rod that can taper.
  - `mat_print`: printed paper, with rows of grey type; with a glow owner it also emits, and stays paper while dark.
  - `paper_sheet`: a sheet with UVs and curled ends or a lifted corner.
  - `Heap`: a 2 cm height map that sheets drape onto, each resting on the ones under it.
- **The fixes:**
  1. **Maintainer's arms and hands (N16–N17):**
     - Tapered sleeves, a ribbed cuff and a wrist.
     - A palm with four fingers curled onto the home row and a thumb toward the space bar; fingertips clear the key tops by about a millimetre.
  2. **Paper avalanche (N15–N17):**
     - 340 printed, curled sheets draped over a heap banked into the back-left corner and over the floor around it, and in two piles on the desk's ends that hang over its edges.
     - The desk's middle stays clear: the screen, the N15 ticket's landing spot and the slot's drops.
     - A first version dropped rigid sheets onto the heap's highest point. Each one hovered, so the piles grew into towers; draping fixed that.
  3. **Glowing sheets:** paper with an emission scaled by "glow", not a bare emitter that rendered black before N17. There are 13 of them now (every 26th sheet).
  4. **Ticket drift (N29–N37):** 60 printed tickets lying on the plinth and on each other, deepest against the glass.
  5. **Peanut jar:** 34 peanuts in the shell (two lobes and a waist) packed without overlaps, and a lid.
  6. **Baby monitor camera:**
     - A rounded body with a dark glossy face, the lens in a bezel ringed by six IR LEDs, and the standby pip.
     - It sits on a ball joint over a weighted round base.
  7. **Shop twin's mittens (N31–N32):**
     - Each mitten is a flat hand with a round tip and the thumb up, standing on its edge like a reaching hand, with a ribbed blue cuff.
     - Lying flat, the N32 camera saw only the mitten's edge: that camera looks along the elbow's X axis (checked in Blender).
     - The mittens stay inside the old ball's outline, which cleared the blanket.
  8. **Quilt folds (N38–N40):**
     - A rolled hem and quilted puffs, both raised upward only so the folds never move closer to the probe, and a cream binding on the rim.
     - The thickness is now a Solidify modifier after the shape keys. Baked into the mesh, it flattened to 2 mm when the folds open, which was the paper-thin edge in N39.
     - The blanket's rim is rounded with a bevel.
  9. **Shop easel (N33–N34):**
     - The front legs lean back behind the screen to a crossbar above it, and a back leg joins that crossbar.
     - The screen stands on a ledge with a lip and is clamped at the top to a second crossbar. There's a low rail between the front legs, and the leg ends are rounded.
     - The old legs passed through the screen.
- **Review stills:** `renders/c4/review_v6a` (all anchors, first pass); `review_v6b`–`v6d` (1080p, after the paper, quilt and mitten corrections).
- **Status:** the full re-render is running (frames_v7).

## 2026-10-25T14:55 — C4 v7: full draft720 re-render with the nine placeholder fixes; v6 outputs archived

- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v7 --profile draft720` (7,019 frames in 6,279 s, 0.89 s/frame)
  - `... -- --out renders/c4/anchors_v10 --profile draft720 --anchors` (39 stills)
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v7 1 renders/c4/c4_animatic_v7.mp4` (1280x720, 30 fps, 252.17 s)
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v10 renders/c4/c4_anchor_sheet_v7.jpg 6`
  - `.venv/bin/python -I scripts/qc_flicker.py renders/c4/frames_v7 renders/qc/flicker_v7`
- **Flicker QC:**
  - 31,375 blobs in 7,854 runs, against 29,773 in 7,358 for v6.
  - The top runs are the same spans as v6. Only the shop-window wide (frames 5167–5421) grew, from 1,619 to 2,134 blobs. That growth is edge crawl on the new easel crossbars and legs at a distance, alongside the existing crib-bar/blanket crawl (run_02.png), not z-fighting.
- **Anchor sheet:** all nine fixes read in the anchors (hands N17, paper N15–N16, mittens N31–N32, easel N33–N34, quilt N38–N40), with no new artifacts.
- **Archived (superseded, placeholder geometry):** `archive/renders/c4/c4_animatic_v6_superseded_placeholder-geometry.mp4`, `archive/renders/c4/c4_anchor_sheet_v6_superseded_placeholder-geometry.jpg`, `archive/renders/c4_anchors_v9_superseded_placeholder-geometry/`. frames_v6 is a frame sequence, so it is not archived.
- **Status:** v7 sent to the human for review (R1).

## 2026-10-25T18:10 — C4 v7 review fixes: laptop keys, falling drift, moat, quilt cloth, moat glow, AI-found CVEs on the tickets

The human's notes are logged in `log/human_interventions.md` (15:05, 17:20, 17:40). Code: `scenes/blender/sets/nursery.py`, `scenes/blender/animate.py`, `scenes/blender/animatic.py`, new `config/ticket_cves.json`.

1. **Laptop keys:**
   - Every key had been buried 7 mm inside the deck, because the deck height was set 1 cm low. The fingertips also sat 6 mm in the deck.
   - The deck top is corrected, and the keyboard rebuilt as a full laptop layout: a half-height function row, then five rows of 15 units with modifiers, a space bar and arrows. Keys are lighter than the deck, with light mono legends. A speaker grille sits behind them.
   - The hands rose 1 cm, and the fingertips now clear the key tops by 1 mm, with the home row where they were.
2. **Falling drift (N14–N37):**
   - Before, the pile was 60 static tickets scaled up from N29.
   - Now 240 tickets fall in gusts from 4.2 m above the plinth. Each one flutters down for 4.5–6 s, swaying, rocking and slowly spinning, and lands curled (shape key "air") before it lies down on the pile.
   - Arrivals: a fifth by N29 and the rest by N37, faster later.
   - Each ticket's resting place is draped on the heap in landing order, so later tickets lie on earlier ones.
   - About a third touch down on a perch upslope, toward the glass, and stay there until the next gust lands within 60 cm. Then they slide down into place.
3. **Moat:**
   - The flat disc with two glowing rims is gone.
   - The hall floor now has a ring cut for a channel: stone walls, a bed 62 cm down, and water 11.5 cm below the floor that stirs slightly (a 4D-noise bump driven by the frame).
   - Pale coping blocks line both edges, 60 cm long with 4 mm joints and overhanging the water. Under each overhang is a strip of cold light.
   - A lid of hall floor covers the cut and dissolves on "moat" (123.43 s), over 1.5 s.
4. **Moat glow (human, 17:20):** the water also mirrors a procedural sky band, and glows faintly of its own (emission 0.35 plus the reflection). The light strips went from 3 to 5.
5. **Quilt cloth (N38–N40):**
   - The folds turn to cloth when they are two-thirds open (N38 + 0.15 s).
   - A strip along each hinge stays pinned, fading out over 15% of the fold. The rest falls onto the blanket and against the crib's sides. The front fold lies out toward the room; the back one slumps against the slats.
   - The rest shape is the fold unrolled flat, so the cloth doesn't keep the mound's shape.
   - The bake runs in `animatic.build` and takes about 100 s. The simulation stops 2 s after it starts and holds its last frame.
   - Tuning (test stills in the session scratchpad):
     - The cloth first blew into shards. The cause was not the cloth: even-offset Solidify spiked on its creases, and the angle-limited bevel splintered. Now plain Solidify and one level of subdivision.
     - The "flat" key that squashed the folds as they turned shrank the fabric, which then buckled into fine ripples. It was removed.
     - A 5 mm grid (smaller than the collision distance) jittered. The grid is now 1 cm.
     - Lying on the blanket slab, the cloth also felt the blanket's underside and jittered by centimetres. Colliders are now single-sided, with damping 0.8. Even so, it never came fully to rest on the breathing blanket, hence the 2 s stop.
     - Only the hinge row skips collisions. With the whole pinned strip excluded, the probe's fingers poked through.
     - The new "plane" rest key came in at value 1, which flattened the closed mound before the reveal. It is now 0.
   - The crib's glint bead hides once it is out, at N38 + 0.35 s. It had shown as a black dot once the fold fell away.
6. **AI-found CVEs on the tickets (human, 17:40):**
   - `config/ticket_cves.json` lists 47 disclosed CVEs whose records or vendor advisories credit an AI. Each was checked against cveawg.mitre.org on 2026-10-25:
     - 28 Firefox (MFSA 2026-13, Firefox 148, and the Firefox 149 records), 9 wolfSSL, NGINX, FreeBSD (CVE-2026-4747, Mythos Preview, Glasswing), OpenSSL and Bouncy Castle, all credited to Claude or Anthropic researchers using Claude;
     - 5 WebKit (Apple's Safari 26.1 note) and SQLite CVE-2025-6965, credited to Google's Big Sleep.
   - The list comes from VulnCheck's tracker (2026-04-15). None is made up.
   - Each ticket carries the ID, a short label and "found by …" as mesh lettering that bends with the paper, over printed body type that now stops lower down.
- **Status:** committed; the full v8 render is next.

## 2026-10-25T20:05 — C4 v8: full draft720 re-render with the v7 review fixes; v7 outputs archived

- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v8 --profile draft720` (7,019 frames in 6,061 s, 0.86 s/frame)
  - `... -- --out renders/c4/anchors_v11 --profile draft720 --anchors` (39 stills)
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v8 1 renders/c4/c4_animatic_v8.mp4` (1280x720, 30 fps, 252.17 s)
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v11 renders/c4/c4_anchor_sheet_v8.jpg 6`
  - `.venv/bin/python -I scripts/qc_flicker.py renders/c4/frames_v8 renders/qc/flicker_v8`
- **Flicker QC:**
  - 31,817 blobs in 8,128 runs, against 31,375 in 7,854 for v7.
  - The top eleven runs are the same spans, boxes and sizes as v7 (hands N17, shop-window wide, etc.).
  - Runs new in v8 are all small (under 250 px). They fall in the falling drift (frames 4,880–4,970, single tickets entering frame) and in the quilt reveal (6,710–7,009, a few-pixel sliver of the mattress edge opening as the cloth slumps past the side rail). Both are motion, not z-fighting.
- **Spot checks:**
  - The moat lid is solid at 3,700 and the channel, coping and glow show by 3,720.
  - The tickets lie scattered across the plinth at 4,800.
  - The quilt folds fall away at 6,700, and they lie draped at N39–N40.
  - The keyboard is full under the hands at N17.
- **Archived (superseded, review fixes):** `archive/renders/c4/c4_animatic_v7_superseded_review-fixes.mp4`, `archive/renders/c4/c4_anchor_sheet_v7_superseded_review-fixes.jpg`, `archive/renders/c4_anchors_v10_superseded_review-fixes/`. frames_v7 is a frame sequence, so it is not archived.
- **Status:** v8 sent to the human for review (R1).

## 2026-10-25T23:10 — C4 v8 review fixes: desk stacks with real CVEs, the bank, the music box, the quilt's cloth and the end flicker

The human's notes are logged in `log/human_interventions.md` (20:20, 20:45, 21:40). Code: `scenes/blender/sets/nursery.py`, `scenes/blender/animate.py`. Test stills are in the session scratchpad.

1. **Basement desk stacks:**
   - The two desk piles had their centres past the desk's ends, and each sheet bent down over the edge. They looked about to slide off.
   - Now they are two squared-up stacks wholly on the top: left front at (-0.07, 1.12), right at (1.04, 1.15), clear of the laptop, the forearms, the jars and the lamp. They take 12% of the sheets, down from 18%.
   - Each sheet's curl is pressed to 12% on the desk. At full curl, each sheet's raised edges rested on the last one's, so the stack's edges climbed into a bowl and the top sheets tipped up.
2. **Real CVEs on the stacks' top sheets (human, 21:40):**
   - Each top sheet is an advisory: "SECURITY ADVISORY", the ID, the label and "found by …", from `config/ticket_cves.json` (seed main+8). This render has CVE-2025-43434 (WebKit, Big Sleep) and CVE-2026-2789 (Firefox, Claude).
   - The lettering is mesh that lies on the sheet, over body type that starts lower down.
   - A sheet laid the other way round is turned end for end, its heights with it, so both read upright from the chair.
3. **The mobile's bank:**
   - Its pediment was a three-sided cone, a pyramid from the side, and its columns stood on a slab with nothing behind them. The mobile turns, so this showed.
   - It is now a felt temple: two steps, a walled hall, four columns with caps and feet before each face, an entablature, and a gable roof (a triangular prism) with a coin in each pediment.
4. **The music box (still the kit's, recognisably):**
   - The kit's 60 drum pins sat in a fixed scatter that matched no note. They are removed.
   - `nursery.drum_pins` (from `animate.music_box`) gives every one of the 1,149 music-box notes a pin at its tooth, placed so it meets the tooth's tip as the tooth plucks and glows. Each pin shows for one drum turn, appearing round the drum's back 224° before its note. The drum always carries the coming notes over its top.
   - This is one object of points with geometry nodes, which instance a pin on each point between its t0 and t1.
   - The crank gets its arm, a boss and a handle pin. The kit's blue knob is the grip, and the crank turns with the drum.
   - Added: flanged brass drum ends, a spur gear and the copper spindle, a fan governor at the back that whirls 24 times per drum turn, and three screws on the comb.
5. **The quilt's cloth:**
   - Each fold is held at one point, the middle of its lip, not by a strip along the hinge. The hinge's turn carries that point up and over, and the rest falls free.
   - The "blown downward" flicker had two causes:
     - **Mass:** 0.25 kg per vertex, about 180 kg a fold, which the springs couldn't carry. The cloth collapsed into strands and kept slipping, with about 250 vertices a fold moving 1–3 cm every frame after it landed.
     - **Colliders:** it hovered on 1 cm collider shells, and lay on the probe's pulsing parts and the probe's overlapping arm parts.
   - Now:
     - mass 0.02 kg per vertex, and bending 10, so it lies open in broad quilt folds instead of crumpling;
     - collision distance 2 mm and collider shells 3 mm;
     - colliders are the crib and the probe's shell only, and the arms lie on top of the fold;
     - the simulation runs from N38 + 0.15 s to + 3.5 s.
   - Measured over the last 1.3 s of the simulation: 3 and 2 vertices still move more than 5 mm a frame, against about 250 before.
   - Starting the cloth at the push's start balled the folds up on the arms coming out from under them, so it starts at N38 + 0.15 s as before.
6. **The end flicker:**
   - A crawling dark line along the crib's head end (in the v7 and v8 flicker maps) was the 1–2 px slot between the blanket's end and the headboard. The ray peel found the blanket's rim, the mattress and then the end board.
   - The mattress now runs to the end boards, 1 mm short of each. The slot shows mattress, not the drop to the floor.
- **Status:** committed; the full v9 render is next.

## 2026-10-26T01:15 — C4 v9: full draft720 re-render with the v8 review fixes; v8 outputs archived

- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/animatic.py -- --out renders/c4/frames_v9 --profile draft720` (7,019 frames in 6,021 s, 0.86 s/frame)
  - `... -- --out renders/c4/anchors_v12 --profile draft720 --anchors` (39 stills)
  - `.venv/bin/python -I scripts/animatic_assemble.py renders/c4/frames_v9 1 renders/c4/c4_animatic_v9.mp4` (1280x720, 30 fps, 252.17 s)
  - `.venv/bin/python -I scripts/contact_sheet.py renders/c4/anchors_v12 renders/c4/c4_anchor_sheet_v9.jpg 6`
  - `.venv/bin/python -I scripts/qc_flicker.py renders/c4/frames_v9 renders/qc/flicker_v9`
- **Flicker QC:**
  - 32,199 blobs in 8,552 runs (v8: 31,817 in 8,128). The large runs (frames 2,750–2,910 and 5,160–5,430) are unchanged.
  - The quilt (6,600–6,800) has only small runs, under 210 px each. They are the binding's edge turning as the camera moves past the lying folds, not jitter.
  - **The end flicker is not fixed.** In the temporal map of frames 6,940–7,000, the crawling line along the crib's head end is still there and longer, because the quilt no longer covers part of it.
    - A ray cast at frame 6,970 shows the first surface along it is the blue blanket's underside (back-facing), at its head-end edge.
    - Cause: `bmesh.ops.solidify` offsets along face normals, and faces made with `bm.faces.new` have none until `bm.normal_update()`. The blanket's two layers are coincident (0 mm apart at all 3,397 vertex pairs), so its top and underside fight wherever it is seen edge-on.
    - The mattress change in the v8 fixes was not the cause. The same bug affects the mobile's pennant and the rocking chair's knitted throw.
- **Spot checks (anchor sheet):** the mobile's bank reads as a temple, the desk stacks are flat on the desk, the music box shows its crank, gear and governor, and the quilt folds lie open at N39–N40.
- **Archived (superseded, review fixes):** `archive/renders/c4/c4_animatic_v8_superseded_review-fixes.mp4`, `archive/renders/c4/c4_anchor_sheet_v8_superseded_review-fixes.jpg`, `archive/renders/c4_anchors_v11_superseded_review-fixes/`. frames_v8 is a frame sequence, so it is not archived.
- **Status:** v9 sent to the human for review (R1), with the end-flicker cause noted. The solidify fix and a v10 render are next.

## 2026-10-26T02:05 — Fix: zero-thickness felt (blanket, pennant, chair throw); the end flicker

- **Change** (`scenes/blender/sets/nursery.py`): added `bm.normal_update()` before each of the three `bmesh.ops.solidify` calls (the crib blanket, the mobile's pennant, the rocking chair's knitted throw). Without face normals, solidify laid both layers in place. With them, the blanket is 15 mm thick (6,674 distinct vertex positions, up from 3,397 coincident pairs). It sinks into the mattress below, out of sight.
- **Check:**
  - I rendered frames 6,936–7,005 at draft720 into the scratchpad. In the temporal map of 6,939–7,000, pixels over 12 levels fell from 10,257 to 303, and only 8 remain in the head-end region (v9: 9,949). The crawling line is gone.
  - Cloth jitter over the last 40 frames: no vertex moves more than 5 mm a frame (v9: 2–3), max 11 mm and 5 mm. The quilt still falls open and lies open.
- **Status:** committed; the full v10 render is next.

## 2026-10-26T02:30 — Audio: the track through the music-deslop post-filter (human, v9 review)

- **Command** (in `~/Code/music-deslop` @ 68441e2): `uv run python -m postfilter.infer --in "audio/track/Sleep, Little Secret.wav" --out "audio/master/Sleep, Little Secret (postfilter m6f).wav" --ckpt ../music-deslop-data/release/m6f_10k.safetensors --source suno` (release chain defaults, 35 s on the 5090)
- **Check:**
  - 48 kHz 24-bit, 11,825,280 samples, the same as the track, so it is sample-aligned and the timing map is unchanged.
  - The change sits 37.8 dB below the music; peak 0.709 → 0.716.
  - No fallback passages were reported.
- **Wiring:** `config/audio.json` `master` points to the new file. `scripts/animatic_assemble.py` uses the master when one is set, else the track. The track itself is untouched.
- **Large file:** added to the manifest.
- **Status:** committed. It goes into the v10 cut.

## 2026-10-26T04:10 — C4 v9 review fixes: the music box turns, CVEs on the floor's sheets, one broken window

1. **The music box turns** (`scenes/blender/animate.py: music_box`):
   - The kit declares `drum` as 0..1, one turn. Blender clamps an animated custom property to its range, so the drum turned once in the first 6 s and then stood still: pins, crank and governor with it.
   - The range is now widened here (`id_properties_ui("drum").update(max=DUR / 6 + 1)`). The shared kit is unchanged.
   - Check at N36: the axle turns 0.524 rad every 15 frames (one turn per 6 s), and the notes, crank and governor follow.
   - **Same bug, found by an audit of every keyed custom property against its range:**
     - The mobile's `turn` counts downbeats (203), but its range was 0..100, so the mobile stopped at 122 s, through its close-ups at N24–N27. The range is now 0..1000.
     - The chair throw's `blanket_slip` (keys to 3.5, clamped at 1) is left as it is. The full 42 cm fall would go through the floor, and it happens after the pen scratch with the chair off screen.
2. **CVEs on the basement floor's sheets** (`scenes/blender/sets/nursery.py: basement`):
   - Floor sheets whose heading half no later sheet lies on are lifted clear of the sheets under them, then get an advisory like the desk's (`advisory()`, shared). Each has a different CVE from the desk's, at the angle the sheet fell. The heading is required to be wholly visible from above, checked by rays 5 mm apart.
   - 17 floor sheets and 2 desk sheets now carry CVEs.
   - **The lift was needed** because between a sheet's vertices, the curled corners of the sheets under it rose through it (the heap samples 2 cm cells). That cut paper wedges through the lettering, as in the test close-up of CVE-2025-43431, and was the wedge beside the desk's CVE-2025-43434 noted in v9.
     - Lifting every sheet instead (a heap reach of one cell) compounded into towers of upturned sheets, so that approach was reverted.
   - **Lettering** (`print_on_sheet`, `sheet_lettering_z`; the drift's tickets too):
     - It is cut along the sheet's grid lines and cell diagonals, and set on the two triangles each cell renders as (bilinear heights let a twisted cell's diagonal rise 0.8 mm through it).
     - Rays down onto every lettering face of the 19 sheets now find only lettering.
3. **One broken window** (`animate.hall_window`):
   - The tape and the old crack on the front and back hall windows are hidden until the cut to the window (N10 + 0.03 s, 52.00 s). The windows are whole before the line, taped and cracked from the cut on, and the new crack grows on "never" as before.
   - Checked: they are hidden at frames 1,200 and 1,559 and shown at 1,560 and after. Test stills before and after the cut.
   - This changes the brief's N09 ("its crack taped over"): there is now no broken window until N10.
- **The stopped v10 run** (its frames are a partial frame sequence, not used) is replaced by the full v10 render that follows. It renders into the same folder.
- **Status:** committed; the full v10 render (with the post-filtered master) is next.

## 2026-10-26 — C4 v10: full draft720 re-render with the v9 review fixes

- **Render:** 7,019 frames in 5,970 s (0.85 s/frame), draft720 (1280×720, 30 fps, motion blur) → `renders/c4/frames_v10`. Anchors (39) → `renders/c4/anchors_v13`. Cut → `renders/c4/c4_animatic_v10.mp4` (252.17 s, 48 kHz audio from the post-filtered master). Sheet → `renders/c4/c4_anchor_sheet_v10.jpg`. Flicker QC → `renders/qc/flicker_v10`.
- **Checks:**
  - End flicker (frames after 6,600): 1,184 px, down from 10,822 in v9. Whole film 339,210 px (v9: 349,358). 30,754 blobs in 8,149 runs.
  - The music box crank and drum visibly turn between 212 s and 214 s. The mobile turns through N24–N27.
  - Windows whole at N09, taped and cracked from N10 on.
  - The floor CVE sheets show at N14–N16.
- **Archived (superseded by v10):** `archive/renders/c4/c4_animatic_v9_superseded_review-fixes.mp4`, `archive/renders/c4/c4_anchor_sheet_v9_superseded_review-fixes.jpg`, `archive/renders/c4_anchors_v12_superseded_review-fixes/`. Frame sequences are not archived.
- **Status:** sent to the human for review.

## 2026-10-26 — C4 v10 review fixes: the taped window back; the music box turns the right way

1. **Window** (`animate.hall_window`): the hiding of the tape and the old crack until the N10 cut is removed. The hall windows are taped over an old crack from the start again (the brief's N09), and the new crack grows on "never" as before. Checked: tape and old crack render at frame 300.
2. **Music box direction** (`animate.music_box`, `nursery.drum_pins`):
   - "drum" is now keyed backwards (0 to -DUR/6, the range's min widened to match). The comb-side face of the drum rises, so each pin comes up under its tooth and lifts the tip, as the tooth's pluck shows it. The crank turns clockwise seen from its end, as a hand-cranked box does. The governor follows.
   - `drum_pins` takes a negative `turn_s` for a backwards drum and swaps its show window (136 degrees before the note, 224 after), so pins still appear and vanish at the same hidden point at the drum's back.
   - Checked: a pin for a note at N36 + 3 s climbs from (y -0.0135, z -0.0174) to the tooth tip at the note (-0.0182, -0.0123 from the axle; the tip angle is -124 degrees) and on upward.
- **Status:** committed; the full v11 render follows.

## 2026-10-26T06:45 — C4 approved (subject to v11); C5 preparation begins

- C4 is approved apart from the v10-review fixes now rendering as v11 (human, R1). C5 preparation starts alongside: the shop display's real pages (N33, N34), the 2D overlay (captions, N41 CRT line, N42 fact card, N43 audit-log bookend, N44 end card), the SRT, the vertical reframes, the thumbnail and the final render and assembly scripts.
- The live brief was re-read (rev 30); its changes since the rev 27 mirror are already in `docs/brief.md` (the windows vertical cut).
- The fact-card source check (brief: re-open every source before rendering) is running as a separate research pass; it writes `docs/fact_check_2026-10-26.md`.

## 2026-10-26T08:30 — C5 preparation: fact check, shop screen, overlay, cards, SRT, reframes, final render and assembly scripts

- **Fact-card source check** (brief: before rendering, re-open every source): `docs/fact_check_2026-10-26.md`, done by a research subagent on 2026-10-26.
  - Of the brief's 10 facts, 5 were confirmed and 5 corrected; none were cut.
    - VulnCheck's 26,153 was Anthropic's claimed total, not the ledger count; the card now uses Anthropic's dashboard figures, dated Oct 2, 2026.
    - Mozilla's 271 are "vulnerabilities".
    - "AI-report flooding" is now Node.js maintainers, quoted.
    - PHP2Shell was found in August, not October; sites went offline "from Britain to Japan", not worldwide.
    - "Same underlying model" holds via Mythos 5, Mythos Preview's successor.
  - The end card's "OpenAI, which led the PHP2Shell work" is OpenAI's own claim, so the line is now "whose model helped find PHP2Shell".
  - Six cited URLs failed to open (404/403/451), and their credits moved to sources that did open. The final lines are in `overlays/cards.json` (`facts_checked_on` 2026-10-26).
- **N33/N34, the shop screen** (`overlays/screen.{json,html,mjs}`):
  - **N33:** the real page, Anthropic's "Claude Fable 5 and Claude Mythos 5", captured 2026-10-26 to `assets/screens/n33_model_page.png` (`scripts/capture_page.mjs`; sidecar JSON with URL and time). It scrolls from the title to "Today we're launching Claude Fable 5: a Mythos-class model that we've made safe for general use."
  - **N34:** the three auditors' raw outputs, rendered from `log/audits/*_raw.md`, each scrolled to its mistake and marked with a highlighter in the note's yellow (no red):
    - Gemini: "appear to refer to either very recent, hypothetical, or fictionalized…"
    - ChatGPT: "the hypothetical system in the song…"
    - GLM: "the song's one hallucination-shaped factoid", held longest.
  - The camera holds the screen only from N33 to about N34 + 6.1 s (stills at 196–199 s), so Gemini and ChatGPT get 1.7 s each and GLM the rest.
  - The frames go to `renders/screen/` (524 frames at 2064x1200). `nursery.shop_twin` maps them onto the screen as an image sequence when they exist, and keeps the placeholder label otherwise. Checked in Blender stills at 189.5 s and 194 s.
- **Overlay** (`scripts/overlay_cues.py` → `overlays/cues.json`; `overlays/overlay.html`; `overlays/render.mjs`, after Sandbox Rhapsody's):
  - Captions as the style spec describes: Inter in comfort, words brightening 40→100%, verse 4 in the light weight. N34's three check marks, in a paper-coloured pen stroke, as each flag is marked.
  - The label.
  - **N41:** the CRT line opening, 247.16–248.16 s.
  - **N42:** 11 fact cards, 4–8.5 s each by length, 248.56–330.03 s.
  - **N43:** the real audit log scrolling (Gemini's and ChatGPT's resolution tables and Claude's GLM review, verbatim from `log/audits/`), then "Check every word with a voice from away." alone, 331.03–365.53 s.
  - **N44:** the end card, one line at a time, ending at 383.03 s.
  - The main video is 383.5 s. The cards are rendered from the page in Chrome; checked in stills at 0.5x and in a vertical short.
  - **The end card's repo URL is not known yet.** `config/release.json` `repo_url` is null, and `overlay_cues.py` refuses a final build until it is set (`--draft` shows a placeholder).
- **SRT** (`scripts/make_srt.py`): the main video plus each short, from the same caption timing.
- **Vertical reframes:**
  - `config/reframe.json` holds window-centre keys per short, set from the v10 frames with `scripts/reframe_sheet.py`:
    - windows: the sticky note and crib, then the taped pane and crack after the N10 cut, then the glass room;
    - bridge: the street window, crack and town, the vault and rope, the shop window, crib and screen, the music box, the probe.
  - To be re-checked on the C5 frames.
- **Thumbnail:** the brief asks for N29's frame with an amber window on the hill, but no N29 frame shows that window. `config/release.json` `thumbnail_t` is 162.44 s, N29's widest view of the room.
- **Final render** (`scripts/render_final.sh`): the windows short's span first, then the whole move, both into `renders/c5/frames` with `animatic.py --resume` (new: keep existing frames, placeholders claim frames in progress), then the anchors and the C5 sheet.
- **Assembly** (`scripts/assemble.py`): `main`, `short:windows`, `short:bridge` and `thumbnail`, with NVENC HEVC BT.709 and AAC 320k. It refuses to overwrite.
  - Tested end to end on the windows short with the v10 frames: 30.1 s, 1080x1920, HEVC + AAC.
- `marked` 14.1.4 added (pinned) for the screen and bookend Markdown.
- **Status:** v11 is rendering. Still to do: the final-profile speed test once the GPU is free, then the C5 render after v11 is approved.

## 2026-10-26T09:20 — Fact check: the blocked sources read (C5 prep)

- Read the four pages the human retrieved (R4). Findings are in the addendum to `docs/fact_check_2026-10-26.md`:
  - Dark Reading confirms the correction to fact 3 (26,153 is the total generated; the ledger held 2,736). Card 3 is unchanged.
  - Digital Watch and CNN support cards 7 and 8. Their credits are restored as the brief has them, and card 8 goes back to the brief's "worldwide" (CNN: "shut down globally").
  - OpenAI's own post claims it "led a coalition", with "PHP's maintainers led the fixes and release". The end card's "whose model helped find PHP2Shell" is unchanged.
  - The FBI (AP) and the NSA (CNN, Digital Watch) both advised taking sites offline. No card names an agency.
- Re-opened AP (adn.com) to check the FBI attribution.
- `overlays/cards.json` updated, `overlays/cues.json` regenerated (`overlay_cues.py --draft`): facts 248.56–328.82 s, end 382.32 s. Stills of cards 7 and 8 checked.
- Pages saved to `reference/sources/2026-10-26/` (git-ignored, never published; `.gitignore` updated), with URL and hash in `reference/sources/2026-10-26.tsv`.

## 2026-10-26T09:35 — C4 v11: full draft720 re-render with the v10 review fixes

- **Render:** 7,019 frames in 5,987 s (0.85 s/frame), draft720 → `renders/c4/frames_v11`. Anchors (39) → `renders/c4/anchors_v14`. Cut → `renders/c4/c4_animatic_v11.mp4` (252.17 s). Sheet → `renders/c4/c4_anchor_sheet_v11.jpg`. Flicker QC → `renders/qc/flicker_v11`.
- **Checked:**
  - The taped, cracked pane is visible from the start (frames 1100–1520 before the N10 crack).
  - The music box's crank moves through N36–N37. The backwards drum was verified numerically before the render.
  - Flicker QC: 30,819 blobs in 8,202 runs (v10: 30,754 in 8,149). The large runs (frames 2,750–2,910 and 5,160–5,400) are the same as before.
- **Archived (superseded, review fixes):** `archive/renders/c4/c4_animatic_v10_superseded_review-fixes.mp4`, `archive/renders/c4/c4_anchor_sheet_v10_superseded_review-fixes.jpg`, `archive/renders/c4_anchors_v13_superseded_review-fixes/`. Frame sequences are not archived.
- Sent to the human for review.

## 2026-10-26T10:05 — Smoothing (C4 v11 review), a shared cloth bake and the 4K shadow pool (C5 prep)

- **Smoothing** (human: "still seeing some unsmoothed geometry, particularly at the door"):
  - The door's rings (frame ring, bead, chrome rim, handwheel) were tori at Blender's default 48 x 12 segments, a 15 cm chord on the 1.2 m rim. Chrome showed every kink.
  - `nursery.torus` now scales its segments with size: major max(48, R x 240), minor 12..32.
  - The door slab goes from 128 to 256 sides. With the new `crisp` option its cap edges are hard, which removes the dark falloff toward the rim of its face. Other cylinders keep round caps, so the bolts and knobs still read as domes (crisp caps made them flat discs).
  - `animatic.build` runs the kit's smooth-by-angle (35 degrees), as Sandbox Rhapsody did at its C5. It covers 735 flat-shaded meshes and skips the blanket and its colliders: their normals steer the single-sided collisions.
  - Checked: 4K frame 900 before/after (the rings round, the bolts domed), and all 39 anchors against v14. Only the door shots change visibly.
- **The cloth does not repeat between runs.** Two anchor runs of the committed code fold the blanket differently at N39-N40. This was found while checking the smoothing, which isn't the cause. C5's separate runs (the windows span, the rest, any resume, the anchors) would each fold it differently.
  - New `animatic.py --cloth-cache DIR`: the first run bakes, then writes each cloth's result before thickness and subdivision as a PC2 point cache. Every run swaps the Cloth modifier for a Mesh Cache reading it.
  - Checked: two anchor runs sharing a cache match pixel for pixel at N38-N40, and the blanket sits where it should.
  - `scripts/render_final.sh` passes `--cloth-cache renders/c5/cloth` to every run.
- **4K shadows:** the final profile hit "Shadow buffer full" (549 warnings over 7 frames at 36 s; none at draft720). `config/render_profiles.json` final gets `shadow_pool_mb: 2048`, applied by `animatic.py`.
- **Final-profile speed** (first measurement, before these fixes): 3.4 s/frame at 36 s, 6.1 s/frame at 210 s (the music box). Re-timing with the fixes is running.

## 2026-10-26T10:40 — 4K shadows, corrected; final-profile timing

- **Correction to the 10:05 entry:** `shadow_pool_mb` changed nothing, since the kit already sets a 2 GB pool. The warning's limit (9,838 / 8,192) is the shadow pages Eevee updates at once, and it still fired 578 times at 36 s.
  - Replaced with `shadow_resolution_scale: 0.5` for the final profile, applied by `animatic.py` (default 1.0). At 4K, half scale is still finer than the approved 720p.
  - At 36 s: no warnings. The crop matches full scale, with the dresser's under-lip shadow slightly firmer.
- **Final-profile timing** (4K, 64 samples, 4 motion-blur steps, with the smoothing and the shared cloth cache):
  - 3.2 s/frame at 36 s (the room, half-scale shadows);
  - 3.9 s/frame at 120 s;
  - 6.1 s/frame at 210 s (the music box);
  - 5.6 s/frame at 222 s (the crib).
  - About 2 min to build each run. Estimate for 7,019 frames: about 9 h, with the windows span (about 950 frames) first at about 1 h.

## 2026-10-26T10:55 — C4 approved; repo URL and thumbnail set (C5 prep)

- **C4 v11 approved** by the human, apart from the smoothing, which is fixed and shows in the C5 frames.
- **Repo URL:** `config/release.json` `repo_url` is https://github.com/Derivative-Work/not-yet. `overlays/cues.json` is regenerated without `--draft`: the end card's last line is "Full production log: https://github.com/Derivative-Work/not-yet", with 33 interventions.
  - The count is read when the cues are generated. Regenerate them just before C6 assembly so it includes the C5 and C6 approvals.
- **Thumbnail** (the human: the crib, the broken window and the cracks outside, keeping the amber window):
  - Scanned the v11 frames from 147 s to 233 s, then 154.6–155.8 s in 0.13 s steps.
  - Chose 155.33 s (frame 4660, N28): the crib rail, the taped and cracked back window, the crack lit down the road, the neighbor's amber window, the moon and the mobile among the stars.
  - Rejected 208.0 s: the probe's LED shows in the crib (brief: never the probe).
  - `thumbnail_t` is 155.33. `assemble.py thumbnail` takes it from the C5 frames.

## 2026-10-26T11:00 — C5 final render started

- `scripts/render_final.sh` (background), writing to `renders/c5`:
  - the windows span first (34.1–65.2 s) into `renders/c5/frames`;
  - then the whole move with `--resume`;
  - then the 39 anchors and `renders/c5/c5_anchor_sheet.jpg`.
- Every run uses the final profile (4K, 64 samples, 4 motion-blur steps, half-scale shadows) and shares one cloth bake in `renders/c5/cloth`.
- Estimate: about 1 h for the windows span, about 9 h in all. Disk: 173 GB free, about 63 GB needed.

## 2026-10-26T18:45 — Windows short re-cropped onto the window (human, R1)

- **Why:** the human rejected the crop (see `log/human_interventions.md`). From 39 s to 52 s it sat on the sticky note and the crib (cx 0.36–0.48), and the taped pane was outside it.
- **Measured on the C5 frames:** the window (moon pane and taped pane) spans about 0.49–0.79 of the frame width at 34.6 s, 0.55–0.85 at 38 s, 0.51–0.79 at 41 s and 0.44–0.73 at 44.4 s. That fits in the 9:16 crop (0.316 of the width).
  - From about 45 s the camera is close enough that the window is wider (0.35–0.72 at 47 s). There the crop keeps the taped pane whole and loses only the moon pane's outer edge.
- **`config/reframe.json` windows keys up to 52 s:** 34.6 s 0.64, 38.0 s 0.70, 41.0 s 0.65, 44.4 s 0.585, 47.0 s 0.56, 51.98 s 0.565. 55.6 s moves from 0.70 to 0.715 so the outside shot keeps the tape's right arm.
  - Every frame from 34.6 s to 52 s now shows the moon, the taped and cracked pane and the town below. The sticky note is in frame at the start and again from about 46 s. The crib is in frame throughout.
- Checked with 9:16 crops of the C5 frames at 34.6–55.6 s. The bridge short is unchanged.

## 2026-10-26T19:00 — C5 approved (human, R1); C6 started

- The human approved going on to the upload-ready render and `METADATA.md` (see `log/human_interventions.md`). The 4K flicker check (`scripts/qc_flicker.py`, at 2,000 of 7,019 frames at 18:27) carries on in the background, and its result is logged when it ends.
- **C5 checks so far:** 7,019 frames and 39 anchors, none empty. No shadow-buffer warnings. The blanket at N38–N40 matches between the anchor run and the frames run (no pixel more than 1 level apart). Frames and anchors are within 0.2–6 levels of v11/v14 on average, from the samples and the motion blur. The door is smooth. Thumbnail frame 4660 is as chosen.
  - Each run logs one "Failed to create GPU texture" error at startup, as the approved draft runs did. The main run logged two more next to frame 5577, which matches v11 and its neighbours.

## 2026-10-26T18:48 — C6: windows short assembled; colour tags fixed

- **Overlay:** `node overlays/render.mjs short:windows` → `renders/overlays/overlay_short_windows.mkv` (903 frames, 36 s).
- **SRT:** `scripts/make_srt.py` → `deliverables/not_yet.srt` (38 captions), `not_yet_short_bridge.srt` (18), `not_yet_short_windows.srt` (4).
- **Found** (agent, ffprobe): the first encode's transfer was tagged `iec61966-2-1` (sRGB, from the PNGs), not BT.709.
  - `assemble.py` now sets primaries, transfer and matrix to BT.709 in the bitstream (`hevc_metadata`).
  - Also tried an explicit `scale=out_color_matrix=bt709`. It made the image 1.6 levels darker in Y, while `format=yuv420p` alone already matches the BT.709 value from the source PNG (Y 52.57 vs 52.6 expected). Reverted.
  - The two superseded encodes are in `archive/deliverables/` (`…_superseded_bt601-matrix-srgb-tag.mp4`, whose name records the first suspicion; its matrix was fine, only the tag was wrong; and `…_superseded_explicit-scale-darker.mp4`).
- **Output:** `deliverables/not_yet_short_windows.mp4`: 30.1 s, 1080×1920, HEVC (BT.709 tagged) and AAC 320k, −17.5 LUFS integrated, −3.9 dBFS true peak.
  - Checked in frames: the label, the four captions, the whole window from the first frame, the crack on "never", the outside shot, the push in, and the fade.

## 2026-10-26T18:49 — C6: upload metadata (METADATA.md)

- **The request** (human, R1): the upload-ready render and `METADATA.md`. Modelled on Sandbox Rhapsody's.
- **Main video:**
  - Title: recommended (65 characters) plus two alternatives.
  - Description (4,491 of 5,000 characters):
    - the satire label first;
    - the premise, and how it was made, with the 35 logged interventions and the repo link;
    - the conflict-of-interest line and the audits;
    - the link to Sandbox Rhapsody (release order, brief);
    - chapters from the timing map's sections and the cues (facts 4:08, audit log 5:29, credits 6:05);
    - the 11 fact cards verbatim with their credits, and the source URLs from `docs/fact_check_2026-10-26.md` and `reference/sources/2026-10-26.tsv`;
    - the end card's credits, plus the pen scratch and the typefaces;
    - the licence and a no-affiliation line.
  - Tags (373 of 500 characters).
  - Settings: Music; not made for kids; synthetic content disclosed; the SRT; Standard Licence; the thumbnail (frame 4660); end-screen placement clear of the centred credits.
- **Vertical cuts:** a title and description each, shared tags, and a shared footer with a `<MAIN VIDEO URL>` placeholder.
- **Open for the human** (listed at the top of the file):
  - **Licence:** this repo has no licence files. The description uses Sandbox Rhapsody's terms (CC BY-NC-SA 4.0 and MIT), to be confirmed.
  - **Link order:** the windows cut may go out before the main video (Patch Tuesday, 2026-11-10).
  - **Bridge cut length:** 3:18.6 is over YouTube's 3:00 Shorts limit. Either upload it as an ordinary vertical video, or end it after fact card 8 (2:57.7).

## 2026-10-26T19:01 — C6: the human's notes (caption face, closing note, the flickering W)

- **Why:** three notes from the human on C6 (see `log/human_interventions.md`, 19:05 and 19:10). Logged as exceptions.
- **Caption face: Oooh Baby** (Robert Leuschke, SIL OFL 1.1).
  - Downloaded from Google Fonts' repository (`google/fonts`, `ofl/ooohbaby`) into an isolated folder. Vendored as `assets/fonts/OoohBaby-Regular.ttf` with `OoohBaby-OFL.txt`, both added to `SHA256SUMS`. It covers every character in the captions, including … and ’.
  - It is a handwriting face with one weight and hairline strokes. So the captions are 1.6× the old size, verse 4's thinner voice is 1.45× (in place of the light weight), and each word gets a 0.03 em stroke in its own colour.
  - Checked in stills over the C5 frames (main and vertical), including N34's check marks.
- **Closing note:** `overlays/cards.json` `human_note`: "A note from the human / With AI assistance, security researchers are discovering more vulnerabilities than ever. / Are your systems up to date?", the human's words. It is drawn as in Folks Like Us: the "from" line small and grey, the note in Inter.
  - **Main video:** 383.42–390.57 s (held 7.15 s, by `card_hold`), so the video now ends at 391.07 s.
  - **Vertical cuts:** each ends on the note, after its own content, over black and silence (`content_to`, `note_on`/`note_off` in cues). Windows: 38.6 s (content 30.1 s, faded as before). Bridge: 3:27.1.
- **The flickering W:** `overlay_cues.py` `FLICKER` gives L08's "windows" two forms. The overlay picks one every 0.13 s from a fixed hash, so the flicker is uneven but the same on every render, and lays the word out at its widest form so the line doesn't move. The SRT keeps the sung text.
- **Also:** `overlays/render.mjs` protocol timeout raised to 15 min. A 4K screenshot timed out at the 180 s default while the GPU box was busy with the flicker check and 10 render jobs.
- **Archived** (superseded by these notes): the two shorts (`archive/deliverables/*_superseded_inter-captions-no-note.mp4`) and their overlays (`archive/renders/overlays_superseded_inter-captions-no-note/`).
- Intervention count on the end card: 36.

## 2026-10-26T19:03 — C6: deliverables in git and the manifest; rebuild running

- `deliverables/`: the SRTs and the thumbnail (`assemble.py thumbnail`, frame 4660, 1920×1080, 148 KB) are in git. The videos are git-ignored (`deliverables/*.mp4`) and `scripts/manifest.sh` now lists `deliverables`.
- `METADATA.md` updated for the notes (27a77ca): the count is 37, the main video is 6:31.1 and ends on the note, the shorts are 38.6 s and 3:27.1, the bridge's option (b) now ends after card 7 (2:59.4), and the end-screen window starts at 6:11.
- Rebuild running (scratchpad `c6_chain.sh`): overlays and assembly for the windows short, the bridge short, then the main video.

## 2026-10-26T19:08 — Licences added; release plan; the bridge cut held; main video first

- **Licences** (human, R1): `LICENSE` (MIT, copied from Sandbox Rhapsody), `LICENSES/CC-BY-NC-SA-4.0.txt` (copied; sha256 e66c269d…, the same as Sandbox Rhapsody's), and `LICENSE-media.md`, written for this project. It says what the licence covers, and what it doesn't: the code; the four OFL fonts, Oooh Baby included; the Pixabay pen scratch; Anthropic's page on the N33 screen; and the fact-card sources, which are never published.
- **Release plan** (human, R1): the main video on the morning of 2026-10-27, then the windows cut on Patch Tuesday, 2026-11-10. `METADATA.md` now reflects it: the main video goes first, so the windows cut's footer can link it; the licence item is closed.
- **Bridge cut held** (human, R1): not assembled for C6. Its stopped overlay render's temporary parts were removed; its overlay and video from before the notes are in `archive/`. `METADATA.md` keeps its notes, marked held.
- **Main video first:** the rebuild chain was stopped during the bridge overlay. The main video's overlay and assembly now run alone (scratchpad `c6_main.sh`).
- **Windows cut rebuilt** with the notes: `deliverables/not_yet_short_windows.mp4` (overlay 1,157 frames in 52 s).
