# Selecting observations and controlling lesson quality (Level 3, draft)

This page gives the evidence behind three parts of
[Extracting and synthesising lessons](extraction_synthesis.md): how extraction's coverage was improved,
the rules synthesis writes to, and how the store's growth is held back and the published store was
reviewed.

## Selecting observations and improving coverage

When a game ends, it saves this **extraction input**: every role, the full discussion and the wolves'
chat, each night action with its result, each player's last private strategy note, and the outcome. No
model runs at that point. I extract the games I choose later, offline, through the provider's batch
interface. Extraction is slow and never needs to happen during play, so it can take the batch price,
about half the normal rate.

Extraction needs enough focus to capture distinct situations without treating every turn as a lesson.
A single call for the whole game concentrated on the most visible roles and repeated familiar advice:
across five nine-seat games, five of its eight Healer observations described the first night with no
information. Separate calls per role produced 19 to 21 Healer observations covering a wider range of
decisions. In the ten-seat game, separating discussion from voting addressed a similar omission: one
re-extracted game went from no discussion observations to 16.

The current unit is therefore one **role–phase cell**: one call for each role that was dealt and each
phase it acts in, about 30 calls per ten-seat game. Each call reads the whole game but selects observations
for that cell. The prompt asks for pivotal decisions and non-obvious mechanisms, and permits routine
moves to be skipped. This balances coverage against the risk of forcing significance onto ordinary
moves or inventing explanations for them. The coverage checks motivated the split; they do not establish
an optimal granularity or measure how often over-extraction occurs.

More observations do not by themselves show better selection: these checks did not measure how many
useful moments were missed or how many extracted moments were worth keeping. A next step would be a
set of games in which I mark the moments worth learning from, so that what extraction misses can be
measured rather than assumed.

## Making the recommendation specific and actionable

How synthesis groups observations, and when a group yields no lesson, is on
[the parent page](extraction_synthesis.md#deciding-whether-observations-support-a-lesson), along with
the shape of a lesson: when it applies, one move to make then, and why. The synthesis prompt adds three
rules. The situation fields describe the conditions the whole group shares, rather than copying one
source observation. Mechanics are described with the game rules supplied in the prompt. One group may
yield up to three lessons, a further one only for a distinct move, not to fill a quota.

## Controlling growth and reviewing a published store

Synthesis writes only where something is new, so it never regenerates the whole store:


| Rule                                                                 | Why                                                  |
| -------------------------------------------------------------------- | ---------------------------------------------------- |
| A cell runs only after at least four new observations                | Too little new evidence to change its advice         |
| A cell holding 12 lessons that have not yet earned credit is skipped | Growth stops until credit thins the untested lessons |
| Only groups containing a new observation are synthesised             | Old groups have already been written up              |
| A lesson followed five times shows synthesis its measured score      | A poor record can shape what is written next         |

The first and third rules have one exception: a cell holding fewer than three lessons runs without four
new observations and builds groups from all its observations, old ones included, so a cell that credit
has thinned out is refilled.

The published ten-seat store came from one synthesis build, costing $5.31. Four model readers checked its
605 lessons against the rules, and I read a sample of their cases myself. The 37 lessons that stated a rule
wrongly (6.1%) and 78 duplicates the readers found were left out, leaving 490. The parent page covers what
that check could not establish.

## Sources

- [Extraction and synthesis prompts](../../../Agents/prompts/extraction/cell.py).
- [Extraction coverage report](../../../evidence/extraction/post_game/report.md).
- [Store curation report](../../../evidence/store_curation/report.md).
- [Ten-seat memory report](../../../evidence/memory_system/v8/report.md).
