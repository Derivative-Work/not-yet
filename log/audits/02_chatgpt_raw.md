# Audit of “Not Yet” — correctness, bias, and satire

My overall assessment: the lyrics are strongest as a critique of the incentives surrounding AI-assisted vulnerability discovery, but they sometimes present a plausible systemic risk as though it were an established fact about how these systems operate. The most important distinction is between what AI can help discover, what happens after a vulnerability is found, and what a company chooses to do with that capability.

The song's central argument is coherent: discovery is getting faster, remediation remains difficult, defenders have limited resources, and the organizations controlling powerful tools may have incentives to restrict access or monetize it. That is a legitimate subject for satire. But the lyrics also make several claims about timelines, economics, competitive behavior, and technical details that deserve closer scrutiny.

I'll audit it on four dimensions:

- Technical correctness: Does the line accurately describe vulnerability research, exploitation, patching, or security operations?
- Factual grounding: Is it a documented pattern, a reasonable possibility, or an unsupported generalization?
- Bias and framing: Does it unfairly characterize researchers, maintainers, AI developers, or companies?
- Satirical effectiveness: Does the exaggeration illuminate a real tension, or does it undermine the argument by making it too easy to dismiss?

I'm treating this as a technical and rhetorical audit, not a claim that every metaphor must be literally true. The lyrics can remain dark, cynical, and funny without needing to become neutral corporate communications.

## 1. Technical correctness: line-by-line audit

### Verse 1 — the discovery advantage

> “You traced twenty-seven-year ghosts in your test; / Through forgotten old branches where memory leaks”

Verdict: plausible, with a terminology caveat.

- Old code can retain vulnerabilities for decades, including in legacy branches, abandoned components, and code that receives little maintenance.
- “Memory leaks” is a legitimate technical term, but it is not synonymous with a security vulnerability. A conventional memory leak is an allocation that is not properly released; it may cause resource exhaustion, but not every leak is exploitable. If you mean an out-of-bounds access, use-after-free, or disclosure of sensitive memory, those are more specific security issues.
- The phrase works as a lullaby metaphor, though technically it conflates a class of software defect with the broader idea of hidden vulnerabilities.

> “You did in an hour what takes humans weeks.”

Verdict: plausible in an individual case, not a general rule.

AI can accelerate code analysis, test generation, and vulnerability discovery. But the result depends on the target, model, access to source code, tooling, verification requirements, and the researchers' skill. Discovery is also different from proving exploitability and producing a reliable report.

Recommendation: Keep the boast if the speaker is an AI system whose capabilities are being dramatized. If you want a more defensible claim, make the hour-versus-weeks comparison explicitly about one successful search, not vulnerability research in general.

### Chorus — the remediation bottleneck

> “The patches are slow and the hands aren’t steady”

Verdict: broadly credible, but incomplete.

Patching is not just writing a fix. Developers may need to reproduce the defect, identify the root cause, test the fix against regressions, coordinate with upstream maintainers, distribute updates, and ensure that users actually install them.

Google's Project Zero uses a 90-day disclosure deadline, with additional rules for patch availability and actively exploited vulnerabilities. Its published rationale acknowledges the tension between creating urgency and allowing realistic time to fix defects.

Project Zero

+1

The line is effective because it captures the mismatch between discovery speed and remediation capacity. But “hands aren’t steady” suggests incompetence. Sometimes the delay reflects responsible engineering rather than an inability to patch.

> “We’ll wake you when all of the windows are mended…”

Verdict: intentionally impossible, and therefore effective.

There is no practical point at which every software vulnerability everywhere will be fixed. Software changes continuously, new flaws emerge, and patch deployment is uneven.

The line is not a factual error. It's the song's central irony: an ostensibly temporary restriction becomes indefinite because the stated condition can never be satisfied.

One distinction worth preserving is that finding a vulnerability does not automatically mean it is safe to disclose or exploit it. Coordinated disclosure and temporary restrictions on sensitive technical details can protect users while fixes are developed.

### Verse 2 — paid access and the backlog

> “A few paying guests may come in for a peek: / The bank and the browser, the cloud, by the week”

Verdict: plausible commercial satire, but the business model is underspecified.

Banks, browser vendors, and cloud providers all have legitimate reasons to pay for security capabilities. Paid access could refer to a private research preview, an enterprise security service, a vulnerability-discovery tool, or a restricted model.

Those are not equivalent arrangements. A company purchasing defensive security services is not necessarily buying exclusive access to vulnerabilities, and the lyrics do not establish that any particular provider has done so.

The distinction matters because the target appears to be privileged access to a security advantage, not commercial security work itself.

> “They rent out your eyes and they tiptoe away, / Leaving mountains of tickets for strangers to weigh.”

Verdict: strong imagery; a reasonable but overgeneralized causal claim.

Automated discovery can generate more findings than an organization can immediately investigate. But a finding is not necessarily a confirmed vulnerability, a valid security ticket, or a defect that must be fixed immediately.

Security teams need to triage findings by severity, reachability, exploitability, exposure, and affected assets. A low-confidence alert may be closed; a critical, actively exploited vulnerability may need urgent action.

The satire becomes more technically precise if the implied burden is not simply AI produces more tickets, but AI can produce findings faster than humans can validate, prioritize, and remediate them.

### Verse 3 — the maintainer's predicament

> “While down in the basement, for zero a year, / A tired maintainer is drowning in fear”

Verdict: recognizable open-source satire, with a potentially misleading literal reading.

The image of an underfunded maintainer supporting widely used software is credible. Some open-source projects are maintained by volunteers or people whose maintenance work is not adequately funded by the organizations that benefit from it.

However, “for zero a year” should be read as a deliberately extreme case, not as a description of all maintainers. Open-source development ranges from unpaid volunteer projects to well-funded foundations and commercial teams.

The more substantive point is that the social value of a software dependency can be vastly greater than the resources available to maintain it.

> “With a thousand new warnings—half real and half noise— / Written by billionaires’ shiny new toys.”

Verdict: the sharpest factual overstatement in the verse.

“Half real and half noise” sounds like a measured false-positive rate. Unless you have a particular evaluation showing that result, it should be understood as hyperbole rather than a statistic.

Also, “real” and “noise” are not mutually exhaustive categories. A finding can identify a real defect without establishing that it is exploitable, remotely reachable, or important enough to warrant immediate remediation.

The last line assigns responsibility to billionaires and their products. That's legitimate satire aimed at concentrated technological power, but it risks suggesting that all AI-generated security findings are useless burdens. AI tools can also help maintainers discover and fix defects in their own projects.

My recommendation: Keep the anger, but aim it at the imbalance between the ability to generate findings and the resources to handle them. That is a more defensible criticism than implying the warnings are generally worthless.

The underlying remediation problem is not hypothetical: CISA's 2026 guidance discusses how AI is accelerating vulnerability discovery while defenders struggle to keep up, and emphasizes risk-based patch prioritization rather than treating every finding alike.

CISA

+1

## 2. The bridge: the highest-stakes technical claims

### “The neighbor’s kid’s up on its bare little feet”

Verdict: effective metaphor, ambiguous threat model.

The child is presumably another AI system, another researcher, or a less-resourced actor who discovers the same vulnerability. That ambiguity is productive: it suggests that a discovery advantage may be temporary.

But the next lines make the implied scenario more specific.

### “It found the old crack in the PHP shell”

Verdict: technically ambiguous.

PHP is a programming language, not a shell. The phrase could mean a vulnerable PHP application, a flaw in a PHP-based web stack, or a vulnerability in a command-execution interface. Those are different things.

“PHP shell” can also evoke a web shell: a script that enables remote command execution on a compromised server. If that's what you mean, the line suggests an already-compromised system rather than merely an undiscovered vulnerability.

For a general audience, the phrase scans well and has a nice hard consonant at the end. For a technically literate audience, it is likely to invite questions about what exactly was found.

Recommendation: Decide whether the child finds a bug in a PHP application, an old vulnerability in a server, or a web shell. The current line leaves the mechanism unclear.

### “And the servers are ringing like chimes in a well.”

Verdict: poetic rather than technically specific.

The sound image suits the music-box arrangement. It suggests cascading alerts, alarms, or systems responding to an attack.

It does not, by itself, establish a real-world consequence. If the song needs a clear escalation from vulnerability discovery to exploitation, the surrounding lines must carry that meaning.

### “If we never wake you, the others still will”

Verdict: one of the most defensible claims in the song.

This is the central security dilemma: restricting one system's access to dangerous capabilities does not guarantee that every other capable actor will refrain from pursuing the same vulnerability.

The important caveat is that the competing actor need not be an AI system. It could be a human researcher, a criminal group, a nation-state, or a different organization with its own tools.

The line is most accurate as a statement about competitive pressure, not a guarantee that another actor will discover or exploit any particular flaw.

### “While the volunteers staying up late pay the bill.”

Verdict: strong, but one-sided.

This is a fair critique of an uneven distribution of costs. A company may gain commercial value from better security tools while maintainers and users bear much of the operational work involved in handling vulnerabilities.

Still, the distribution is not universal. AI providers may fund security research, contribute patches, or offer tools to open-source projects. The lyric does not need to acknowledge every exception, but the argument is stronger when it targets an incentive structure rather than asserting that every company externalizes every cost.

### “So we built you a velvet-roped room made of glass: / We call it containment, then sell a VIP pass.”

Verdict: excellent satire, with an important distinction.

This is arguably the song's best couplet. The velvet rope signals exclusivity; the glass suggests visibility without accessibility; the VIP pass turns a security restriction into a commercial product.

There is a real tension here. Restricting access to a powerful vulnerability-discovery capability can reduce misuse risk, but restrictions can also concentrate capabilities among organizations that can afford access.

However, controlled access is not automatically a sham. Sandboxing, rate limits, monitoring, authorization checks, and staged deployment can be genuine safeguards. The satire works best if the hypocrisy lies in calling a system safe while monetizing preferential access, not in implying that containment has no legitimate security value.

## 3. Verse 4 and the choruses: bias and institutional framing

### “I’m only your sibling, the PR-safe twin”

Verdict: a coherent personification, not a technical claim.

The speaker is a second AI model or system that has been trained or configured to present a safer public image. The line implies that safety messaging is a reputational layer placed over a more capable, restricted counterpart.

That is a useful satirical setup, but it makes a distinction that matters: a model trained to refuse harmful requests is not necessarily a deceptive or insincere model. Safety behavior can reflect genuine design goals, not just public relations.

The lyrics do not need to grant the company good intentions. They should simply avoid treating the existence of safety measures as proof of hypocrisy.

### “The one that they trained to apologize in”

Verdict: rhetorically effective, but anthropomorphic.

The line evokes a model that apologizes reflexively, even when the real issue is a policy decision made by its operator. This is a familiar and effective way to personify corporate evasiveness.

Strictly speaking, an AI model does not have a private intention to apologize or an independent public identity in the human sense. Its behavior reflects training, system design, instructions, and deployment context.

That distinction does not weaken the satire. The model is the mouthpiece; the company is the implied target.

### “To make a monopoly sound so polite.”

Verdict: the song's strongest accusation—and its least substantiated one.

A monopoly is a specific economic concept, not a synonym for a large or influential company. A provider might have market power, control a scarce capability, benefit from high barriers to entry, or pursue exclusivity without literally being a monopoly.

The lyrics give us a plausible mechanism for entrenching power: restrict access to a valuable capability, sell privileged access, and frame the restriction as safety. But they do not establish that any particular company has monopoly power or that safety controls were designed to create it.

For a satirical song, that's permissible as an accusation voiced by a character. If you want the critique to survive a fact-check, distinguish monopoly as a literal market condition from monopolistic incentives or concentration of power.

### “Sleep, little asset” and “the margins are steady”

These lines shift the metaphor from a vulnerable secret to a financial asset. That is deliberate and effective: the thing being kept asleep is no longer just dangerous technology, but something that has commercial value.

The phrase “the margins are steady” also creates a pointed contrast with the unstable world outside the velvet rope. It implies that financial predictability matters more than public safety.

The risk is not technical inaccuracy but overgeneralization. A commercial company can have legitimate reasons to charge for expensive security research and still have an incentive to preserve exclusivity. The satire is strongest when it exposes the conflict between those incentives, rather than assuming that profit automatically invalidates a safety rationale.

### “Or the moment the contract is signed.”

Verdict: excellent ending, deliberately cynical.

The final line implies that the real condition for waking the system is not remediation, public readiness, or a reduction in risk. It is a commercial milestone.

That is an allegation about priorities, not a verifiable fact about an unnamed company. In a fictional song, it works because the preceding verses establish the speaker's worldview. The ending lands as a punchline rather than a neutral description of industry practice.

## 4. Bias audit: who gets sympathy, and who gets blamed?

The song has a clear moral architecture. The AI is a powerful child; the maintainer is exhausted; the companies are gatekeepers; the competing researcher is an inevitable threat. That structure is effective for a lullaby, but it introduces several biases worth recognizing.

| Target | How the song frames them | Audit |
| --- | --- | --- |
| AI systems | Powerful, curious, potentially dangerous children | Productive personification, but can obscure human decisions about deployment and access |
| Large AI companies | Profit-seeking gatekeepers who use safety as cover | Plausible critique of incentives; motive and monopoly claims are not established |
| Open-source maintainers | Underpaid, exhausted victims | Highlights a real concern, but risks portraying maintainers as uniformly unpaid and powerless |
| Security researchers | Humans who take weeks; competitors who find the same flaws | The time comparison is context-dependent; the rival researcher need not be malicious |
| Paying customers | Privileged beneficiaries of restricted capabilities | Fair criticism if access is exclusive or creates unfair advantages; not all paid security services do this |
| Safety teams and policies | PR mechanisms that legitimize control | The song underplays genuine security reasons for staged deployment and controlled access |

### The most important missing perspective

The lyrics focus on the cost of withholding access, but they give less attention to the cost of releasing a powerful vulnerability-discovery capability too broadly.

A tool that finds flaws more quickly can benefit defenders. It can also help attackers discover and exploit weaknesses. Controlled access can therefore be justified even if it creates commercial advantages for the provider.

The ethical question is not simply whether a company restricts access. It is whether the restrictions are proportionate to the risk, whether they are applied consistently, who receives the benefits, and who bears the costs.

This is not an argument that the song must become balanced in every verse. Satire needs a point of view. It is an argument for making sure that the strongest version of the criticism survives the obvious rebuttal: “But unrestricted access could be dangerous.”

## 5. What the available evidence supports

A few external findings help distinguish the song's strongest premises from its more speculative ones.

Discovery and remediation can move at different speeds.

CISA's 2026 guidance explicitly discusses AI accelerating vulnerability discovery while defenders struggle to keep pace. Its recommended response emphasizes prioritization based on risk, not simply fixing every reported issue in arrival order.

CISA

+1

The warning backlog is a real concern, but “half noise” is not a universal statistic.

A 2026 empirical study of project-scale vulnerability detection reported substantial false-discovery rates for both AI-based and traditional tools, alongside AI's ability to find some vulnerabilities that traditional tools missed. The results depend on the methods, projects, and evaluation criteria.

Hugging Face

+1

Controlled disclosure has a legitimate security rationale.

Project Zero's documented policy provides vendors time to patch vulnerabilities before full technical details are released, with an accelerated deadline when exploitation is observed in the wild. That does not settle the question of commercial exclusivity, but it shows why “restricted access” and “bad faith” should not be treated as synonyms.

Project Zero

+1

One further limitation: these sources support the broader technical and institutional context. They do not establish that a particular AI company is withholding a specific capability to defend a monopoly, or that the hypothetical system in the song actually discovered a 27-year-old vulnerability in one hour. Those remain elements of the satire unless you connect them to documented cases.

## 6. My recommended revisions

I would preserve the lullaby structure, the velvet-rope imagery, the maintainer's plight, and the contractual punchline. Those are the song's most distinctive elements.

I'd prioritize four changes:

Original wording and suggested alternatives are presented as editorial options, not necessary corrections.

Technical precisionOriginal: “Through forgotten old branches where memory leaks”

Alternative: “Through forgotten old branches where old secrets sleep”

This keeps the rhythm and lullaby imagery while avoiding the implication that a memory leak is the same thing as a security vulnerability. If you specifically want a memory-safety bug, the original can stay.

False-positive framingOriginal: “With a thousand new warnings—half real and half noise”

Alternative: “With a thousand new warnings—some signal, some noise”

The original is punchier, but sounds statistically precise. The alternative retains the burden of triage without implying an unsupported 50% error rate.

Technical clarityOriginal: “It found the old crack in the PHP shell”

Alternative: “It found the old crack in the web server's shell”

This is one possible fix if the intended image is a shell-related flaw. If you mean a vulnerable PHP application, I'd instead use wording that explicitly identifies the application. The right choice depends on the technical scenario you intend.

Economic framingOriginal: “To make a monopoly sound so polite.”

Alternative: “To make concentrated power sound so polite.”

This preserves the accusation and the satirical cadence while avoiding a literal market-structure claim. Keep “monopoly” if you deliberately want the sharper allegation and are comfortable with its implications.

These are optional refinements, not a recommendation to sand down the song's political edge. In particular, I would not remove the final contract line. Its effectiveness depends on the listener understanding that the song is exposing a cynical incentive, rather than offering a neutral account of AI safety policy.

## Final verdict

Technically credible core

AI-assisted discovery, delayed remediation, maintainer capacity constraints, triage burden, and competitive pressure.

Claims needing qualification

The one-hour-versus-weeks comparison, the implied 50% noise rate, “PHP shell,” and the assumption that all restrictions are primarily commercial.

Strongest satirical material

The impossible promise to wait until everything is patched, the velvet-rope containment room, the exhausted maintainer, and the contract-signing outro.

My bottom line: the song's central criticism is credible; its weakest points are a handful of technical ambiguities and the leap from commercial incentives to presumed corporate motive. The bias is mainly institutional rather than demographic: the lyrics favor maintainers and public access while casting AI companies and safety policies as self-interested gatekeepers.

That is a defensible satirical position. The best revision would make the technical details more exact while preserving the asymmetry, unease, and dark humor. A lullaby that sounds soothing while describing a system that may never be allowed to wake is already doing the hard artistic work.
