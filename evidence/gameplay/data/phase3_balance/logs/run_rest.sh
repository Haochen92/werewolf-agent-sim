#!/bin/bash
cd /home/ubuntu/projects/werewolf-agent-sim
OUT=evidence/game_play_enhancement/data/phase3_balance
run() { poetry run python -m evaluation.experiments.phase3_capture --label $1 --out $OUT --lone-killer $2 --neutral $3 > $OUT/logs/$1.log 2>&1; echo "$1 exit $? $(date +%T)" >> $OUT/logs/waves.log; }
echo "rerun (two at a time, rescue-stall fix applied) start $(date +%T)" >> $OUT/logs/waves.log
run b02 serial_killer fortune_teller & run b07 serial_killer fortune_teller & wait
run b06 necromancer speculator & run b08 necromancer fortune_teller & wait
run b09 serial_killer speculator & run b10 necromancer speculator & wait
echo "rerun done $(date +%T)" >> $OUT/logs/waves.log
