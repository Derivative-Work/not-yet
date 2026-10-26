# Upload metadata

YouTube metadata for the main video and the windows cut, ready to paste at upload. Written by the agent (C6); the human uploads (R4).

**Before uploading:**
- **Intervention count.** Update the number in the main description (`grep -c '^## ' log/human_interventions.md`). The end card says 39, the count when its overlay was rendered (2026-10-26).
- **The main video's link.** Fill in `<MAIN VIDEO URL>` in the windows cut's footer once the main video is up. In YouTube Studio, also set the windows cut's **Related video** to the main video.

**Release plan (human, 2026-10-26):** the main video on the morning of 2026-10-27, after the .NET out-of-band security updates (https://devblogs.microsoft.com/dotnet/dotnet-october-2026-oob-security-updates/); then the windows cut on the next scheduled Patch Tuesday, 2026-11-10. Both come after Sandbox Rhapsody (https://www.youtube.com/watch?v=zq79yQ3164w), which introduces the series' probe (brief). The licences (video and assets CC BY-NC-SA 4.0, code MIT) are confirmed by the human and in the repo (`LICENSE`, `LICENSE-media.md`).

---

## Main video (16:9, 3840×2160)

**File:** `deliverables/not_yet_main.mp4` (C6; 6:31.1). It ends on the human's closing note (6:23–6:31).

### Title

Recommended (65 characters):

```
Not Yet — an AI-made lullaby for a model too dangerous to release
```

Alternatives:
- `Sleep, Little Secret (Not Yet) — AI-made animated lullaby`
- `Not Yet: a lullaby for the AI that finds the bugs`

### Description

```
AI-generated satire about real events.

A lullaby sung to an AI model too capable at finding security flaws to release: one slow, continuous push through a glass nursery where that model sleeps, while the stars on the wall keep multiplying and a light comes on down the street. Keeping one model asleep doesn't keep the street dark.

Every frame, note and word was made by AI: the song by Suno, the words by Claude, the animation and edit by Claude Code. A human only approved or rejected work, fixed sync and technical failures, and ran tools the agents couldn't reach. Each of those 39 interventions is logged, along with every prompt and production step:
https://github.com/Derivative-Work/not-yet

Conflict of interest: Claude is made by Anthropic, whose model is the one in the crib. The words were audited by Gemini, ChatGPT and GLM. Their audits scroll past at the end, verbatim.

The thing in the crib is a probe of the same make as the ones in Sandbox Rhapsody, with a different light: a different house's child.
Sandbox Rhapsody: https://www.youtube.com/watch?v=zq79yQ3164w

CHAPTERS
0:00 Intro
0:11 Verse 1
0:34 Chorus
1:04 Verse 2
1:23 Verse 3
1:47 Chorus
2:11 Bridge
2:56 Verse 4
3:22 Final chorus
3:41 Outro
4:08 The facts
5:29 The audit log
6:05 Credits

WHAT ACTUALLY HAPPENED
(The fact cards at the end, with their sources. Checked against each source on 2026-10-26.)
• Anthropic's restricted model, Claude Mythos Preview, found a 27-year-old bug in OpenBSD, among thousands of high-severity vulnerabilities it says it found. (Anthropic; The Register)
• Access went to a limited group of partners through Project Glasswing, with up to $100M in usage credits. (Anthropic; The Register)
• By October 2, 2026, Anthropic counted 29,439 candidate findings: 6,157 disclosed, 516 patched. (Anthropic disclosure dashboard)
• Anthropic says the limit is now how fast bugs can be verified, disclosed and patched. (Anthropic)
• Mozilla found and fixed 271 vulnerabilities in a single Firefox release while testing the model. (Anthropic)
• Node.js maintainers report "an incredible amount of AI slop" in vulnerability reports. (HeroDevs)
• In August 2026, researchers using OpenAI and Google models found PHP2Shell, flaws in the language behind about 70% of websites whose server-side language is known. (Digital Watch; CNN)
• When the fix shipped on October 21, sites went offline worldwide while operators patched. (CNN; Digital Watch)
• Anthropic's stated reason for withholding: without safeguards, such models would make exploiting flawed software cheaper for almost anyone. (SecurityAffairs)
• Critics call the arrangement "a private club." (SecurityPal, citing Georgia Tech's Internet Governance Project)
• Mythos Preview's successor is the same underlying model as Claude Fable, which Anthropic sells publicly with added safeguards. (Anthropic)

SOURCES
Anthropic, Project Glasswing: https://www.anthropic.com/glasswing
Anthropic, Glasswing: an initial update: https://anthropic.com/research/glasswing-initial-update
Anthropic disclosure dashboard: https://red.anthropic.com/2026/cvd/
Anthropic, Claude Fable 5 and Claude Mythos 5: https://www.anthropic.com/news/claude-fable-5-mythos-5
The Register: https://www.theregister.com/2026/04/10/project_glasswing/
The Register: https://www.theregister.com/2026/04/15/project_glasswing_cves/
HeroDevs: https://www.herodevs.com/webinars/from-node-20-eol-to-node-27-lts-and-everything-in-between
Digital Watch: https://dig.watch/updates/php2shell-php-flaws-ai-emergency-patches
CNN: https://www.cnn.com/2026/10/21/tech/php2shell-vulnerability-ai-intl
SecurityAffairs: https://securityaffairs.com/192576/ai/anthropics-glasswing-10000-vulnerabilities-found-in-one-month-and-the-patching-problem-has-never-been-more-obvious.html
SecurityPal: https://www.securitypalhq.com/blog/anthropic-project-glasswing-explained

CREDITS
Words: Claude, in conversation, revised after three audits
Audited by: Gemini (Google, a Glasswing partner), ChatGPT (OpenAI, whose model helped find PHP2Shell), GLM
Music: Suno V6 (take 8289b42f), post-filtered with music-deslop (checkpoint M6f 10k)
Animation and edit: Claude Code with Opus 5.5 (Blender, HTML overlays, ffmpeg)
Pen scratch: "scribble" (Pixabay sound effect 6144), Pixabay Content License
Type: Oooh Baby (captions), Inter, JetBrains Mono and Instrument Serif (SIL OFL)

Video and assets: CC BY-NC-SA 4.0 · Code: MIT
Satire. Not affiliated with or endorsed by any company named here.

#AIgenerated #musicvideo #AIsafety
```

### Tags

Paste as one comma-separated line (373 of 500 characters):

```
Not Yet, Sleep Little Secret, AI music video, AI generated, AI satire, AI safety, lullaby, Claude Mythos, Project Glasswing, PHP2Shell, vulnerability disclosure, open source maintainers, AI slop, cybersecurity, animated music video, Blender, Suno, Claude, Claude Code, Sandbox Rhapsody, MIDI animation, music box, AI model release, responsible disclosure, security research
```

### Settings

| Setting | Value |
|---|---|
| Category | Music |
| Audience | Not made for kids. It's a lullaby, but it isn't for children; "made for kids" would also turn off comments and the end screen. |
| Altered or synthetic content | **Yes.** The singing voice is AI-generated. The animation isn't realistic, but disclosing is the safe reading of YouTube's policy, and it matches the on-screen label. |
| Language / caption language | English / English |
| Captions | Upload `deliverables/not_yet.srt` as English subtitles. The video also has burned-in captions; the SRT gives search text and lets viewers restyle them. |
| License | Standard YouTube License. YouTube's only Creative Commons option is CC BY, which would drop the NC-SA terms; the description states the licence instead. |
| Thumbnail | `deliverables/not_yet_thumbnail.jpg` (1920×1080): 2:35.33 (frame 4660), chosen by the human. It shows the crib rail, the taped and cracked window, the crack lit down the road, the neighbour's amber window, the moon and the mobile among the stars, and never the probe. |
| Chapters | From the description (first chapter at 0:00; each over 10 s). |
| End screen | From 6:23 to the end (7.6 s), over the human's note (approved by the human, 2026-10-26). Elements: the Sandbox Rhapsody video (https://www.youtube.com/watch?v=zq79yQ3164w) bottom left, Subscribe bottom right. The note is centred and three lines tall, so the corners are clear; starting earlier would put the elements over the credits and the repo link (6:05–6:22). Once the windows cut is up (2026-11-10), it can be added as a third element. |
| Comments | Open. |
| Visibility | Unlisted for a check pass, then public. |

---

## Vertical cuts (9:16, 1080×1920)

**What they have in common:**
- Reframed from the 4K render (`config/reframe.json`), with burned-in captions and their own SRT, timed from the first frame.
- Each ends on the human's closing note, over black and silence (7.2 s).
- Settings as the main video: Music; not made for kids; altered/synthetic content: yes; English captions from the cut's SRT; Standard YouTube License. Related video: the main video.
- No custom thumbnail (Shorts pick a frame in the app) and no chapters or end screen.

**Shared tags** (paste for both):

```
Not Yet, Sleep Little Secret, AI music video, AI generated, AI satire, AI safety, lullaby, PHP2Shell, cybersecurity, open source, Blender, Suno, Claude, shorts
```

**Shared footer** (end of both descriptions):

```
Full video, facts and sources: <MAIN VIDEO URL>
Production log, with every prompt and every human intervention: https://github.com/Derivative-Work/not-yet
Music: Suno · Words: Claude · Animation and edit: Claude Code
Video and assets CC BY-NC-SA 4.0. Satire; not affiliated with any company named.

#AIgenerated #AIsafety #Shorts
```

### 1. The windows (Chorus 1), before Patch Tuesday

34.6–64.7 s of the song, then the human's note: **38.6 s**. File `deliverables/not_yet_short_windows.mp4`, captions `deliverables/not_yet_short_windows.srt`. It opens with the "AI-generated satire" label. The camera passes the sticky note and the crib, with the taped window in frame throughout. The pane cracks on "never", then the one cut to the window from outside and the push back in, with picture and music fading out together. No fact card; the human's note follows.

**Title:**
```
"We'll wake you when all of the windows are mended…" #Shorts
```

**Description** (then the footer):
```
AI-generated satire about real events. A lullaby for an AI model kept from the public because it's too good at finding security flaws, while the patches take time. In October 2026, a flaw in PHP that researchers found with AI models sent sites offline around the world while operators patched (CNN; Digital Watch). The first chorus of Not Yet, an AI-made music video.
```

### 2. The bridge, through the facts (not being released for now)

**Held** (human, 2026-10-26: "just the windows short is fine for now"). Not assembled for C6; the notes below stand if it goes out later.


130.82–329.42 s, then the human's note: **3:27.1**. File `deliverables/not_yet_short_bridge.mp4`, captions `deliverables/not_yet_short_bridge.srt`. From "Hush, can you hear it? A light down the street" through verse 4, the final chorus, the reveal and the CRT line, then the 11 fact cards and the human's note.

**Length.** The brief asks for the bridge through the CRT line and then the fact card. With the human's note that runs 3:27.1, over YouTube's 3:00 limit for Shorts. The human decides one of:
- **(a)** Upload as is, as an ordinary vertical video (it won't show in the Shorts feed).
- **(b)** Cut it to fit: end after the seventh fact card (PHP2Shell), then the note (2:59.4). The last four cards (sites offline, the stated reason for withholding, "a private club", the Fable twin) stay in the main video.

**Title:**
```
"Some locks are for danger, and some are for class" #Shorts
```

**Description** (then the footer):
```
AI-generated satire about real events. Anthropic withheld its Claude Mythos Preview model as too dangerous to release, while researchers using other labs' models found PHP2Shell, a flaw in the language behind about 70% of websites whose server-side language is known (Anthropic; Digital Watch; CNN). The bridge of Not Yet, an AI-made music video, through to the facts.
```
