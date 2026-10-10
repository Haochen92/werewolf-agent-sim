#!/bin/bash
cd /home/ubuntu/projects/werewolf-agent-sim
OUT=evidence/game_play_enhancement/data/phase3_balance_3
run() { poetry run python -m evaluation.experiments.phase3_capture --label $1 --out $OUT --lone-killer $2 --neutral $3 > $OUT/logs/$1.log 2>&1; echo "$1 exit $? $(date +%T)" >> $OUT/logs/waves.log; }
echo "batch 3 (necromancer body reuse + conceal hides the carrier's visit, on top of batch 2's rules), two at a time, start $(date +%T)" >> $OUT/logs/waves.log
run d01 necromancer speculator & run d02 necromancer fortune_teller & wait
run d03 serial_killer speculator & run d04 serial_killer fortune_teller & wait
run d05 necromancer speculator & run d06 necromancer fortune_teller & wait
echo "done $(date +%T)" >> $OUT/logs/waves.log
