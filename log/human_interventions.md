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
- **Then (21:10):** the human saved the three raw auditor outputs to `~/Downloads` (production log, step 2b) and gave ChatGPT's version: "whatever the current free model is as of yesterday." Supplying inputs is not a touch on the work.

## 2026-10-23T22:10 — C1 review: darker; rethink the tall window — R1

- **What:** The human reviewed the C1 sheet and asked for changes in words, not by hand.
- **Note from the human:** "it could be a little darker. I'm also not sold on the "tall window" -- it seems like it would be difficult to make the play on Microsoft Windows at "windows are never quite mended" with this format"
- **Rule:** R1 (rejecting a render, with the reason in words). The agent makes the change (production log, C1 v2).

## 2026-10-23T22:40 — C1 v2 approved at 30 fps — R1

- **What:** The human approved C1 v2 and chose 30 fps over the proposed 60.
- **Note from the human:** "this one is fine at 30fps. keep going"
- **Rule:** R1 (approving a plan and a render).

## 2026-10-23T23:25 — C2 approved — R1

- **What:** The human approved the C2 kit import: the probe in this set's light with the green LED, the 3x crib scale, the reveal and glint frames.
- **Note from the human:** "looks great, keep going"
- **Rule:** R1 (approving a render and a plan).

## 2026-10-24T00:50 — C3 review: lanes hard to read, beat detection poor, crosstalk; beat_this approved — R1

- **What:** The human rejected the C3 preview and approved installing beat_this, which the permission classifier had blocked.
- **Note from the human:** "As with Sandbox Rhapsody this is still hard for me to read -- a score is best, like it generated for that step. That said, it seems the beat detection was not good, which would make it difficult to generate a legible score, and it seems there is significant crosstalk based off this alone. Go ahead with beat_this"
- **Rule:** R1 (rejecting a render, reasons in words). Approving a tool install is a technical decision the agent couldn't make alone (R3).

## 2026-10-24T02:05 — C3 re-review: notes accurate enough; the "Celesta" staff is the music box — R1

- **What:** The human judged the notes accurate enough for a convincing video, as in Sandbox Rhapsody. They identified the instrument labelled Celesta in the score (the Percussion stem) as the music box, and asked how much the beat and measure accuracy matters.
- **Note from the human:** "The notes seem accurate enough to make a convincing video (which was good enough for Sandbox). What you have marked in the score as notated for Celesta *is* the music box. How much does the beat/measure accuracy actually matter for this"
- **Rule:** R1 (judging a render); identifying an instrument by ear is a correction of the timing data's labels (R2).

## 2026-10-24T02:20 — Instrumentation identified by ear in a DAW — R2

- **What:** The human brought the stems into a DAW and identified the instruments: the music box is split between the Keyboard and Percussion stems. Bass and Guitar are one fingerstyle guitar, with crosstalk between them. Strings is real orchestral arco strings, with a lot of crosstalk from the other instruments.
- **Note from the human:** "the music box is split between what the stems call keyboard and percussion. What the stems call bass and guitar, I would perform manually as one fingerstyle guitar (but there are places where it only plays the bass notes of it where I would have performed the chords too; maybe these got masked by the music box). There is some crosstalk between the two. What it calls "strings" contains actual orchestral strings -- of the part of this stem that is actually strings, I only hear arco strings, but there's quite a bit of crosstalk from the other instruments."
- **Rule:** R2 (correcting the timing data's labels, the A/V mapping). It is not a creative choice; the agent changes the grouping (production log).

## 2026-10-24T03:00 — C3 approved; stars on the music box melody; ending: pen scratch over the existing audio — R1

- **What:** The human approved the C3 timing data. They chose the music box's melody for the star births, and for the ending chose to keep Suno's audio as it is, with the pen scratch added on top, rather than the proposed music cut.
- **Note from the human:** "Score is good enough to animate to -- let's only revisit if something's visually wrong. Yes, use the music box melody for the stars. For the ending: just add the pen scratch on top of what's existing. Don't try to silence it yourself -- that did not work well for Folks."
- **Rule:** R1 (approving data and choosing between proposed plans).

## 2026-10-24T03:25 — Pen scratch: the synthesised one rejected; a royalty-free recording chosen — R1, and an EXCEPTION

- **What:** The human rejected the code-synthesised pen scratch and chose a stock recording instead: Pixabay "scribble" (sound effect 6144), https://pixabay.com/sound-effects/film-special-effects-scribble-6144/ (royalty-free, no attribution required).
- **Note from the human:** "the synthesized sound is not reading as a pen scratch -- just use this royalty free, attribution not required audio instead"
- **Rule:** R1 for rejecting the synthesised sound. Using a recorded, human-chosen sound in an AI-generated video is an EXCEPTION to "everything is AI-generated by default". It will be credited in the end card's notes and the README even though attribution isn't required.
- **Pending:** Pixabay blocks automated downloads (a Cloudflare challenge for both curl and headless Chrome), so the human downloads the file (R4: an interface the agent can't reach).
