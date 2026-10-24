# Audit: GLM 5.3 Flash

Verbatim from the drafting chat (https://claude.ai/share/b0788d14-90a8-4d6e-adbf-8ad3011e43c1), messages 25 (human) and 26 (Claude's resolution). The auditor's full response was pasted into the chat as an attached file (`file_count: 1` on message 25), which the public share does not expose (`viewer_can_access_files: false`). That file is still to be supplied by the human and saved here as `03_glm_raw.*`.

- **Submitted to the auditor:** 2026-10-23T00:35:26.157707Z or earlier (the human's message carrying its output)
- **Resolved by Claude:** 2026-10-23T00:35:59.053992Z

## Message 25: human, 2026-10-23T00:35:26.157707Z

Here is what GLM 5.3 Flash had to say

## Message 26: Claude, 2026-10-23T00:35:59.053992Z

GLM's audit is the most useful of the three on how it went about checking, and the weakest on facts. Its search failed, so it guessed what each verse refers to, and most of the guesses are wrong. That includes its headline finding.

**Where it's wrong**
- **"Twenty-seven-year ghosts" is not a hallucination.** It's Mythos Preview's 27-year-old OpenBSD bug, reported by The Register and in Glasswing launch coverage. GLM couldn't find a source, treated that as evidence the claim was false, and then said the number had "survived three models." That's the exact failure the song is about, and worth a line in the audit log.
- **"The town killed its lights" is documented.** It's PHP2Shell this week: government sites worldwide went offline, and the NSA told PHP users to patch or take their systems offline.
- **Its referent table is mostly misidentified.** It read the song as Google's Big Sleep and SQLite, the glass room as generic sandboxing, and the guests as Big Sleep's early-access program. The song's actual subjects are Glasswing, PHP2Shell and Fable.

**Where it's right**
- **The "billionaires' toys" line blurs two different actors.** The flood of junk reports comes mostly from bounty hunters using consumer models, not from the labs' own research agents. That makes the line sharper, not weaker: the hunters are using the labs' products.
- **"For nothing a year" is overbroad.** ChatGPT flagged it too, and some maintainers are paid. Two auditors agreeing is enough to soften it.
- **Verse 4 needs something checkable.** That's fair, and it's better fixed in the video than in the lyric: during verse 4, show the real public model page on screen, so the claim can be checked against a source.

**Smaller points**
- It's right that the song leaves out fast fixes. Mozilla fixed 271 Firefox bugs in one release. That fits better on the fact card than in a lullaby.
- I'd keep the contract outro aimed where it is. A safeguarded version of the gated model is sold commercially, so the line is about the research lab, not just the bounty market.

**v3.1 changes (verse 3 only)**

> While down in the basement, for peanuts a year,
> A tired maintainer is drowning in fear;
> A thousand new warnings, some signal, some noise,
> Sent in by the hunters with billionaires' toys.

**A process fix for the remaining audits:** every auditor so far either had no sources or couldn't search, and each one made confident mistakes about what the song refers to. Paste the fact-card source list into the prompt with the lyrics, and ask the model to check claims against those sources, not to identify them. That leaves the auditor doing judgment, which is the part it's useful for. Do the same for the maintainer's read.

Sources:
- [The Register on Glasswing CVEs](https://www.theregister.com/2026/04/15/project_glasswing_cves/)
- [Let's Data Science on Glasswing](https://letsdatascience.com/news/anthropic-deploys-mythos-to-find-critical-vulnerabilities-3efbbac8)
- [CNN on PHP2Shell](https://www.cnn.com/2026/10/21/tech/php2shell-vulnerability-ai-intl)
- [TechCrunch on PHP2Shell](https://techcrunch.com/2026/10/21/the-internet-is-having-a-very-bad-cybersecurity-day/)
- [Anthropic: Glasswing initial update](https://anthropic.com/research/glasswing-initial-update)
