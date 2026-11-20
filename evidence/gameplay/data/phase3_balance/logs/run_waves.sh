#!/bin/bash
cd /home/ubuntu/projects/werewolf-agent-sim
OUT=evidence/game_play_enhancement/data/phase3_balance
run() { poetry run python -m evaluation.experiments.phase3_capture --label $1 --out $OUT --lone-killer $2 --neutral $3 > $OUT/logs/$1.log 2>&1; echo "$1 exit $? $(date +%T)" >> $OUT/logs/waves.log; }
echo "wave 1 start $(date +%T)" >> $OUT/logs/waves.log
run b01 serial_killer speculator & run b02 serial_killer fortune_teller & run b03 necromancer speculator & run b04 necromancer fortune_teller & run b05 serial_killer speculator & wait
echo "wave 2 start $(date +%T)" >> $OUT/logs/waves.log
run b06 necromancer speculator & run b07 serial_killer fortune_teller & run b08 necromancer fortune_teller & run b09 serial_killer speculator & run b10 necromancer speculator & wait
echo "done $(date +%T)" >> $OUT/logs/waves.log
