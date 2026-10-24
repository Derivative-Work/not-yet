# Audits

The three model audits of the lyrics (brief, "Production rules": source material for N34 and the closing bookend N43), in order, plus the human's closing judgment on verse 3.

| # | Auditor | Version | Date (UTC) | Lyrics it audited | Raw output | Chat messages and resolution |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Gemini (Google) | "Gemini Argon" (Gemini 4 Argon per the chat) | 2026-10-22, by 23:30 | v1 (it quotes "You read the whole kernel the way I read rhyme") | `01_gemini_raw.md` | `01_gemini.md`: its revised lyrics, Claude's v2 and resolution table |
| 2 | ChatGPT (OpenAI) | "whatever the current free model is as of yesterday" (the human, 2026-10-23), i.e. ChatGPT's free-tier default on 2026-10-22 | 2026-10-22, by 23:45 | Gemini's revision (it quotes "memory leaks", "paying guests") | `02_chatgpt_raw.md` | `02_chatgpt.md`: its lyrics, Claude's v3 and second-pass table |
| 3 | GLM (Zhipu) | GLM 5.3 Flash | 2026-10-23, by 00:35 | v3 (it quotes "for nothing a year", "sent free") | `03_glm_raw.md` | `03_glm.md`: Claude's review and the v3.1 change |

The raw files are the human's saves of each auditor's full response (the attachments on chat messages 21, 23 and 25), copied byte for byte from `~/Downloads/not-yet-{gemini,chatgpt,glm}-audit.md` (saved there 2026-10-23 20:54–20:55 EDT).

**For N34:** GLM's flag is in `03_glm_raw.md`, section II.1: "Right now this is the song's one hallucination-shaped factoid, and given it survived Claude, ChatGPT, *and* Gemini, I'd treat that as a cautionary tale rather than a coincidence." The number is sourced (Mythos Preview's 27-year-old OpenBSD bug; `03_glm.md`).
| — | The human | — | 2026-10-23 09:47 | `docs/drafting_chat/drafting_chat.md`, message 33; logged as an R1 approval in `log/human_interventions.md` | — |

Full chat: `docs/drafting_chat/` (fetched from https://claude.ai/share/b0788d14-90a8-4d6e-adbf-8ad3011e43c1).
