# Human interventions

Every human action: timestamp, what, why, and which production rule allows it. Rules:
(R1) approve/reject a take, render or plan; (R2) correct A/V sync; (R3) fix technical failures the agent cannot; (R4) run an interface the agent has no access to (Suno, the mastering post-filter). Anything else is an EXCEPTION.

## 2026-10-23T20:29 (from the files' mtimes) — Source files supplied to the agent

- **What:** A human placed the Suno mix (WAV, MP3) and the stems-and-MIDI archive for "Sleep, Little Secret" in `~/Downloads`, and pointed the agent at the brief and the sibling projects.
- **Why:** Inputs listed in the brief.
- **Rule:** Not a touch on the work (supplying inputs). Logged for completeness.
- **Note from the human:** "I have not yet run it through the mastering model -- that will come later." Also: work at 720p on this box for iteration; the full render moves to the 5090 box.

## 2026-10-23T09:42Z (from Suno's tag) — Track generated in Suno — R4 (choice of take: R1)

- **What:** A human ran Suno V6 (`chirp-hawk`, `aug_creativity` 1) with the v3.1 lyrics, unchanged, and a style prompt drawn from the brief's style intent (`log/prompts/suno/takes.md`). The human made many takes and chose `8289b42f-49cc-4433-b82b-65c70a1fa9ac` (https://suno.com/s/3EJeKdHkJJEsodzS, 246.36 s, created 08:28:20Z). The others were rejected as "all way too busy or too long"; they will be supplied later.
- **Why:** The agent has no access to Suno.
- **Rule:** R4 to run Suno; R1 to choose the take.
- **Lyrics:** the submitted lyrics match v3.1, so there is no lyric exception. The doubled bridge line in the MP3's lyrics tag (production log, step 1) is a Suno export artifact. Suno's page doesn't have it, and the human confirms it isn't sung: "the bridge line is not doubled in the audio."

## 2026-10-23T09:47Z (from the drafting chat, message 33) — Audits closed: verse 3 judged fair — R1

- **What:** After three model audits (Gemini, ChatGPT, GLM), the human judged verse 3's portrayal of maintainers fair and closed the audits. v3.1 is final.
- **Note from the human:** "I think we're good on audits now: having interacted with a few maintainers myself after having tickets and changes dismissed (or presumably ignored) effectively as slop, the portrayal here seems fair"
- **Rule:** R1 (approving a plan).
- **Vantage point:** a submitter's, not a maintainer's. The human has filed tickets and changes; they have not maintained the projects. That is the side of the relationship verse 3 depicts. A maintainer's own read was suggested in the chat (message 24) and not done.

## 2026-10-23T21:00 — Inputs pointed to; probe design confirmed final — R1

- **What:** The human gave the Suno share link and the drafting chat's share link, said the audits are in that chat, and confirmed: "Sandbox Rhapsody's probe is final (it's rendering on the other box)."
- **Why:** These answer the brief's open items on the generator, the probe lock and the audit sources.
- **Rule:** R1 for the probe (approving a design to reuse). Supplying links is not a touch on the work.
- **Still open:** the raw auditor outputs were attachments the share doesn't expose (production log, step 2).
