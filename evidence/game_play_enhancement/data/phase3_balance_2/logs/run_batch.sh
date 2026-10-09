#!/bin/bash
cd /home/ubuntu/projects/werewolf-agent-sim
OUT=evidence/game_play_enhancement/data/phase3_balance_2
run() { poetry run python -m evaluation.experiments.phase3_capture --label $1 --out $OUT --lone-killer $2 --neutral $3 > $OUT/logs/$1.log 2>&1; echo "$1 exit $? $(date +%T)" >> $OUT/logs/waves.log; }
echo "batch 2 (sigil no-effect + 2 checks + 2 watches), two at a time, start $(date +%T)" >> $OUT/logs/waves.log
run c01 serial_killer speculator & run c02 serial_killer fortune_teller & wait
run c03 necromancer speculator & run c04 necromancer fortune_teller & wait
run c05 serial_killer speculator & run c06 necromancer fortune_teller & wait
echo "done $(date +%T)" >> $OUT/logs/waves.log
