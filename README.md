# Not Yet

An AI-made lullaby music video, "Sleep, Little Secret", sung to an AI model too capable at finding security flaws to
release. The video is one slow, continuous camera push through a glass nursery where that model sleeps. Nothing
frightening happens on screen: the stars on the wall keep multiplying, a window down the street is taped and cracked,
and a light comes on in the neighbour's house. At the end, the thing in the crib turns out to be a probe of the same
make as the ones in [Sandbox Rhapsody](https://github.com/Derivative-Work/sandbox-rhapsody), with a different light.

Claude Code (Opus 5.5) built and rendered every frame with Blender, JavaScript and ffmpeg, with the mobile, the music
box and the stars driven by the song's MIDI. Suno V6 made the music, and Claude wrote the words. A human only approved
or rejected work, corrected sync, fixed technical failures and ran tools the agent couldn't reach, and every such
action is logged.

AI-generated satire about real events. The fact cards at the end of the video say what actually happened, with their
sources; [docs/fact_check_2026-10-26.md](docs/fact_check_2026-10-26.md) checks each line against them.

> **A note from the human:** With AI assistance, security researchers are discovering more vulnerabilities than ever.
> Are your systems up to date?

## Watch

- **YouTube:** https://www.youtube.com/watch?v=1G2CS3i1cPE (scheduled for the morning of 2026-10-27). The vertical
  windows cut follows on Patch Tuesday, 2026-11-10.
- **Files:** the videos, captions, music, stems and the session transcript are in the
  [v1.0 release](https://github.com/Derivative-Work/not-yet/releases/tag/v1.0).
- **Sandbox Rhapsody,** the video that introduces the probe: https://www.youtube.com/watch?v=zq79yQ3164w

## The making-of record

- [The drafting chat](https://claude.ai/share/b0788d14-90a8-4d6e-adbf-8ad3011e43c1) that led to the song and the
  brief, archived in [docs/drafting_chat/](docs/drafting_chat/drafting_chat.md).
- [log/audits/](log/audits/README.md): the three model audits of the lyrics (Gemini, ChatGPT and GLM), verbatim. They
  appear in the video: on the shop screen in verse 4, and scrolling past after the fact cards.
- [docs/brief.md](docs/brief.md): the production brief, set and shot list (mirrored from the live brief).
- [log/production_log.md](log/production_log.md): every action the agent took, with commands and outputs.
- [log/human_interventions.md](log/human_interventions.md): every human action, with the rule that allowed it.
- [log/prompts/](log/prompts/): the prompts sent to Suno and other models, and Suno's record of the take.
- [timing/timing_map.md](timing/timing_map.md) and [style/style_spec.md](style/style_spec.md): when each shot lands
  in the song, and how it looks.
- [METADATA.md](METADATA.md): the YouTube titles, descriptions and settings.

## Files

Large files stay out of git. [MANIFEST.sha256](MANIFEST.sha256) lists them with SHA-256 hashes: the Suno track, stems
and MIDI, the post-filtered master and the card bounce, the finished videos, and every render, so a rebuild can be
checked against them. The fact-check sources (other publishers' pages) and the page shown on the shop screen
(Anthropic's) are kept locally and never published; [reference/sources/2026-10-26.tsv](reference/sources/2026-10-26.tsv)
and `assets/screens/n33_model_page.json` give their URLs.

## Rebuilding

Versions used: Blender 5.2.3 LTS, ffmpeg 8.0.1 (with NVENC), Node v24.22.0, uv with Python 3.12, an NVIDIA RTX 5090.

```bash
uv sync                                   # .venv from pyproject.toml / uv.lock
npm ci                                    # Puppeteer and its Chrome headless shell
git config core.hooksPath scripts/hooks   # the 50 MiB pre-commit check
```

Put the large audio files back at the paths `MANIFEST.sha256` lists, then, in order (each step's production-log entry
has its exact inputs, outputs and checks; Python runs as `.venv/bin/python -I scripts/<name>.py`):

1. **Timing:** `scripts/timing_map.py`, from the stems, MIDI and transcriptions under `timing/`.
2. **Audio:** `scripts/cards_audio.py`, the instrumental bounce under the cards (needs the music-deslop post-filter).
3. **Frames:** `scripts/render_final.sh` (Blender, the scene in `scenes/blender/`, 3840×2160 at 30 fps, about 7 h on
   an RTX 5090).
4. **Overlays:** `scripts/overlay_cues.py`, then `node overlays/render.mjs main` and
   `node overlays/render.mjs short:windows`; `scripts/make_srt.py` for the captions.
5. **Assembly:** `scripts/assemble.py main` and `short:windows` → `deliverables/`; `scripts/thumbnail.py` for
   the thumbnail.

## Licences

- **Video and assets:** [CC BY-NC-SA 4.0](LICENSE-media.md). That file lists exactly what it covers, and what it
  doesn't (fonts, the pen-scratch sound effect, the page on the shop screen, the fact-check sources).
- **Code:** [MIT](LICENSE).

## Credits

- **Words:** Claude, in the drafting chat, revised after audits by Gemini, ChatGPT and GLM. Conflict of interest:
  Claude is made by Anthropic, whose model is the one in the crib.
- **Music:** Suno V6 (take `8289b42f`), generated and chosen by a human.
- **Mastering:** music-deslop, a post-filter model for AI-generated music that Claude Code built and trained from a
  human-written spec, on Creative Commons audio only (checkpoint M6f 10k). The model is private for now. The agent ran
  it, at the human's request, on the song and on the instrumental bounce under the cards. Settings and provenance are
  in the production log.
- **Animation, edit, captions, cards and thumbnail:** Claude Code with Claude Opus 5.5. The probe rig and the
  note-driven animation library come from Sandbox Rhapsody.
- **Pen scratch:** ["scribble"](https://pixabay.com/sound-effects/film-special-effects-scribble-6144/), Pixabay sound
  effect 6144, Pixabay Content License.
- **Tools:** Blender 5.2 (Eevee), ffmpeg (FFV1, NVENC HEVC), Node.js with Puppeteer, Chrome headless shell and
  marked, and Python with NumPy, SciPy, OpenCV, Pillow, librosa, soundfile, mido, pretty_midi, music21, Verovio,
  PyTorch, Basic Pitch, piano-transcription-inference, Beat This! (beats) and faster-whisper (lyric alignment).
- **Fonts:** [Oooh Baby](https://github.com/googlefonts/oooh-baby) by Robert Leuschke (captions),
  [Inter](https://github.com/rsms/inter), [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) and
  [Instrument Serif](https://github.com/Instrument/instrument-serif), SIL Open Font License 1.1.

### Mastering model training data

The music-deslop model was trained only on audio from these datasets, each licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The audio was cut into
segments, made stereo, mixed, processed (reverb, EQ, compression, mastering, codecs and other degradations) and used
to synthesise training pairs. No dataset audio is in this repository or in the video.

- **Slakh2100** (redux mixes). Ethan Manilow, Gordon Wichern, Prem Seetharaman and Jonathan Le Roux, "Cutting Music
  Source Separation Some Slakh: A Dataset to Study the Impact of Training Data Quality and Quantity", IEEE WASPAA
  2019. https://zenodo.org/records/4599666
- **VocalSet 1.2.** Julia Wilkins, Prem Seetharaman, Alison Wahl and Bryan Pardo, "VocalSet: A Singing Voice
  Dataset", ISMIR 2018. https://zenodo.org/records/1442513
- **CSTR VCTK Corpus 0.92.** Junichi Yamagishi, Christophe Veaux and Kirsten MacDonald, "CSTR VCTK Corpus: English
  Multi-speaker Corpus for CSTR Voice Cloning Toolkit (version 0.92)", University of Edinburgh, The Centre for Speech
  Technology Research, 2019. https://doi.org/10.7488/ds/2645

The degraded training inputs were also made with the
[ACE-Step 1.5 VAE](https://huggingface.co/ACE-Step/Ace-Step1.5) (MIT), the
[Descript Audio Codec](https://github.com/descriptinc/descript-audio-codec) (MIT) and FFmpeg (LAME, the native AAC
encoder and libopus). No generator output (Suno, ElevenMusic or ACE-Step songs) was used for training.

Satire. Not affiliated with or endorsed by any company named here.
