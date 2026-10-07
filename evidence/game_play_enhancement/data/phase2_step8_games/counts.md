# Phase 2 step 8 counts

Written by evaluation/experiments/phase2_step8_counts.py; n/a = the record lacks the field.

## step8 game1 (Phase 2 (HEAD): opening, sweep + echo gate, closing)

winner villagers, 4 days, 415.2 s, model calls 118 (outside the day 23), cost $0.4432

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9 | 0/9 | 0 | 0 | 0 | 0/0 | 0 | 0 | 0/27 | none | nobody | 16.5 | 12.2 | 10 |
| 2 | 8 | 1/8 | 0 | 5 | 1 | 3/7 | 4 | 0 | 5/24 | player_9 (lynched) | player_9 (investigator) | 91.7 | 8.9 | 34 |
| 3 | 6 | 0/6 | 1 | 3 | 1 | 2/6 | 4 | 0 | 3/18 | none | player_7 (villager) | 133.7 | 65.7 | 27 |
| 4 | 4 | 0/4 | 0 | 11 | 8 | 3/4 | 0 | 1 | 11/12 | player_2 (lynched) | player_2 (serial_killer) | 119.9 | 8.2 | 24 |

Judge (21 agent messages): turn_taking 5/21, reveal_timing 1/21; evil claims 0 (in an opening 0); counterclaims none

## step8 game2 (Phase 2 (HEAD): opening, sweep + echo gate, closing)

winner villagers, 4 days, 397.6 s, model calls 93 (outside the day 20), cost $0.3421

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9 | 0/9 | 0 | 0 | 0 | 0/0 | 0 | 0 | 0/27 | none | nobody | 41.4 | 37.4 | 10 |
| 2 | 7 | 0/7 | 0 | 6 | 0 | 6/8 | 1 | 1 | 6/21 | none | nobody | 171.6 | 10.7 | 29 |
| 3 | 5 | 0/5 | 0 | 5 | 2 | 3/4 | 1 | 0 | 5/15 | player_8 (lynched) | player_8 (wolf) | 68.7 | 6.8 | 21 |
| 4 | 3 | 0/3 | 0 | 6 | 4 | 2/2 | 0 | 0 | 6/9 | none | player_7 (serial_killer) | 71.7 | 6.9 | 13 |

Judge (18 agent messages): turn_taking 0/18, reveal_timing 1/18; evil claims 0 (in an opening 0); counterclaims none

## step8 game3 (Phase 2 (HEAD): opening, sweep + echo gate, closing)

winner wolves, 4 days, 380.4 s, model calls 119 (outside the day 25), cost $0.3652

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9 | 0/9 | 0 | 0 | 0 | 0/0 | 0 | 0 | 0/27 | none | nobody | 31.8 | 28.0 | 10 |
| 2 | 8 | 0/8 | 0 | 6 | 0 | 6/11 | 1 | 4 | 6/24 | none | nobody | 96.0 | 7.5 | 34 |
| 3 | 6 | 0/6 | 0 | 7 | 2 | 5/5 | 0 | 0 | 7/18 | none | nobody | 113.3 | 11.2 | 27 |
| 4 | 4 | 1/4 | 0 | 10 | 6 | 3/3 | 0 | 0 | 10/12 | player_6 (lynched) | player_6 (serial_killer) | 90.9 | 11.7 | 23 |

Judge (23 agent messages): turn_taking 5/23, reveal_timing 1/23; evil claims 0 (in an opening 0); counterclaims none

## step8 game4 (Phase 2 (HEAD): opening, sweep + echo gate, closing)

winner villagers, 4 days, 494.2 s, model calls 137 (outside the day 31), cost $0.5472

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9 | 0/9 | 0 | 0 | 0 | 0/0 | 0 | 0 | 0/27 | none | nobody | 15.6 | 10.9 | 10 |
| 2 | 8 | 1/8 | 0 | 6 | 2 | 3/7 | 4 | 0 | 6/24 | player_9 (lynched) | player_9 (investigator) | 98.5 | 10.0 | 34 |
| 3 | 7 | 1/7 | 0 | 11 | 6 | 4/7 | 3 | 0 | 11/21 | player_4, player_2 (lynched) | player_4 (villager) | 181.2 | 8.2 | 39 |
| 4 | 4 | 1/4 | 0 | 8 | 4 | 3/4 | 1 | 0 | 8/12 | player_2 (lynched) | player_2 (serial_killer) | 103.1 | 11.5 | 23 |

Judge (29 agent messages): turn_taking 0/29, reveal_timing 4/29; evil claims 0 (in an opening 0); counterclaims none

## 4c-catalogue (Phase 2 step 4c, first gate prompt (capture at f6d539b6))

winner serial_killer, 3 days, n/a s, model calls n/a (outside the day n/a), cost $n/a

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9 | 0/9 | 0 | 0 | 0 | 0/0 | 0 | 0 | 0/27 | none | nobody | n/a | n/a | n/a |
| 2 | 8 | 1/8 | 0 | 8 | 2 | 5/9 | 4 | 0 | 8/24 | player_4 (lynched) | player_4 (investigator) | n/a | n/a | n/a |
| 3 | 5 | 0/5 | 0 | 7 | 2 | 5/7 | 2 | 0 | 7/15 | player_5 (lynched) | player_5 (wolf) | n/a | n/a | n/a |

## 4c-rerun (Phase 2 step 4c after the rulings: two days replayed on the catalogue board)

winner None, 2 days, n/a s, model calls n/a (outside the day n/a), cost $n/a

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 8 | 1/8 | 0 | 7 | 2 | 4/7 | 3 | 0 | 7/24 | player_4 | n/a | 121 | n/a | n/a |
| 3 | 5 | 1/5 | 0 | 7 | 3 | 3/3 | 0 | 0 | 7/15 | none | n/a | 57 | n/a | n/a |

## 4b-smoke (Phase 2 step 4b: parallel proactive rounds, no filters yet)

winner villagers, 4 days, 305 s, model calls n/a (outside the day n/a), cost $n/a

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | n/a | 0/9 | 0 | 0 | 0 | 0/0 | 0 | 0 | n/a | none | n/a | n/a | n/a | n/a |
| 2 | n/a | 1/9 | 0 | 19 | 3 | 15/16 | 0 | 1 | n/a | none | n/a | n/a | n/a | n/a |
| 3 | n/a | 3/9 | 0 | 25 | 12 | 10/13 | 0 | 3 | n/a | player_2, player_9 | n/a | n/a | n/a | n/a |
| 4 | n/a | 1/8 | 0 | 11 | 3 | 7/7 | 0 | 0 | n/a | player_3, player_8 | n/a | n/a | n/a | n/a |

## v2-832404e9 (v2 prompts, June scheduler (no rounds); one human seat)

winner serial_killer, 5 days, n/a s, model calls n/a (outside the day n/a), cost $n/a

| day | alive | openings spoken/turns | held by filter | lines before closing | reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended | lynched | day s | opening s | LLM calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9 | n/a | n/a | 0 | 0 | 0/3 | 0 | 3 | 0/27 | n/a | nobody | n/a | n/a | n/a |
| 2 | 8 | n/a | n/a | 9 | 4 | 5/10 | 3 | 2 | 9/24 | n/a | player_1 (wolf) | n/a | n/a | n/a |
| 3 | 6 | n/a | n/a | 8 | 0 | 8/13 | 2 | 3 | 8/18 | n/a | nobody | n/a | n/a | n/a |
| 4 | 5 | n/a | n/a | 6 | 0 | 6/9 | 3 | 3 | 6/15 | n/a | player_9 (villager) | n/a | n/a | n/a |
| 5 | 3 | n/a | n/a | 9 | 6 | 3/3 | 0 | 0 | 9/9 | n/a | player_8 (villager) | n/a | n/a | n/a |

Judge (30 agent messages): turn_taking 0/30, reveal_timing 5/30; evil claims 0 (in an opening 0); counterclaims none
