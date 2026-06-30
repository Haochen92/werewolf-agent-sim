"""Prompt text for the day-summary rubric judge."""

DAY_SUMMARY_JUDGE_SYSTEM_PROMPT = """\
You are evaluating a day discussion summary for a Werewolf game. The summary \
compresses a day's public discussion into a structured record that downstream \
consumers use for agent decisions, situation characterization, and post-game \
analysis.

You will be given the raw discussion transcript and the generated summary. \
Score the summary on five dimensions (1-5 each). Be strict — a score of 3 \
means adequate, 4 means good, 5 means excellent.\
"""


DAY_SUMMARY_JUDGE_USER_PROMPT = """\
RAW DISCUSSION TRANSCRIPT (Day {day}, {message_count} messages):
{raw_transcript}

---

GENERATED SUMMARY:
{summary}

---

{day_summary_rubric}

Return ONLY valid JSON:
{{"completeness": <1-5>, "accuracy": <1-5>, "evidence_type_clarity": <1-5>, \
"village_dynamics": <1-5>, "epistemic_correctness": <1-5>, \
"brief_reasoning": "<2-3 sentences explaining the key strength or weakness>"}}
"""


DAY_SUMMARY_RUBRIC = """\
Score each dimension from 1 to 5:

1. COMPLETENESS: Does the summary capture all strategically important \
information from the raw discussion? Every significant accusation, defense, \
role claim, alliance signal, and pressure dynamic should be represented.
   1 = major omissions (key accusations or defenses missing entirely)
   2 = several strategically relevant exchanges omitted
   3 = most content captured but some notable gaps
   4 = nearly complete, only minor details missing
   5 = all strategically significant content from the transcript is preserved

2. ACCURACY: Are attributions correct? The right player IDs must be matched \
to the right statements, accusations must reflect what was actually said, and \
no claims should be fabricated or mischaracterized.
   1 = major misattributions or fabricated claims
   2 = several incorrect player/claim pairings
   3 = mostly accurate with minor characterization errors
   4 = all major attributions correct, minor wording liberties
   5 = every attribution is directly verifiable in the transcript

3. EVIDENCE TYPE CLARITY: Does the summary distinguish the TYPE of evidence \
behind each accusation — voting record, communication style, behavioral \
pattern, or concrete claim? This distinction is critical for downstream \
situation characterization along the information landscape dimension.
   1 = no evidence type distinction, accusations listed without basis
   2 = evidence types mentioned for some accusations but not others
   3 = most accusations have evidence types but some are vague or wrong
   4 = clear evidence type for each accusation, minor ambiguities
   5 = every accusation's evidence basis is explicitly and correctly labeled

4. VILLAGE DYNAMICS: Does the summary characterize the overall discussion \
dynamics? It should describe: (a) village alignment — unified push, \
fragmented suspicion, or split camps; (b) whether consensus is evidence-driven \
or social momentum; (c) who is driving the discussion vs. staying quiet.
   1 = no dynamics characterization at all
   2 = vague or generic dynamics ("the village is divided")
   3 = some dynamics but missing key aspects (e.g., has alignment but not drivers)
   4 = covers alignment, evidence basis, and key drivers with specifics
   5 = precise, game-state-specific dynamics covering all three aspects

5. EPISTEMIC CORRECTNESS: Does the summary treat role claims at the \
appropriate certainty level? Unverified claims should be described as claims, \
not facts. Confirmed roles (via elimination) should be distinguished from \
unverified claims.
   1 = treats unverified claims as established facts
   2 = inconsistent — some claims correctly qualified, others stated as fact
   3 = most claims properly qualified but some ambiguity
   4 = clear distinction between verified and unverified, minor wording issues
   5 = every role reference correctly reflects its certainty level\
"""
