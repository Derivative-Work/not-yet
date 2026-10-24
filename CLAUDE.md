# Not Yet

An AI-made lullaby music video: one continuous Blender camera push through a glass nursery, animated from the Suno MIDI, ending on the reveal that the crib holds a Sandbox Rhapsody probe. The agent does the production; the human may only approve or reject (R1), correct A/V sync (R2), fix technical failures the agent can't (R3), and run interfaces the agent has no access to, such as Suno and the mastering post-filter (R4).

**Start here:** the brief is the Claude Doc https://claude.ai/artifact/3bSKv5TAFQ4JJLZi5NC6on (read it with the docs tools, not a web fetch; mirrored in `docs/brief.md`). Then read the latest entries of `log/production_log.md` and `log/human_interventions.md`.

Rules that apply to every step:
- **Logs:** append to `log/production_log.md` for every action. Log every human action with its rule in `log/human_interventions.md`. Prompts go in `log/prompts/`; the drafting chat and the three audits go verbatim in `log/audits/`.
- **Commits:** one git commit per logged step.
- **Assets:** never delete or overwrite an asset. Superseded or rejected files go to `archive/` with a log note.
- **Large files** stay out of git; run `scripts/manifest.sh` after adding any. Frame sequences, caches, venvs and node_modules are never archived.
- **Reuse:** the probe rig and note-driven animation library come from Sandbox Rhapsody (`~/Projects/sandbox-rhapsody`, `scenes/blender/lib/`). Import them; don't remodel.
- **Render tiers:** `config/render_profiles.json`. Iterate at 720p on the GTX 970 box; final 4K on the RTX 5090 box.
