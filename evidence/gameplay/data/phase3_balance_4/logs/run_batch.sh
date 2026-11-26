#!/bin/bash
cd /home/ubuntu/projects/werewolf-agent-sim
OUT=evidence/game_play_enhancement/data/phase3_balance_4
run() { poetry run python -m evaluation.experiments.phase3_capture --label $1 --out $OUT --lone-killer $2 --neutral $3 > $OUT/logs/$1.log 2>&1; echo "$1 exit $? $(date +%T)" >> $OUT/logs/waves.log; }
echo "batch 4 (cover story + claim-by-action + sightings on the ledger, on batch 3's rules), two at a time, start $(date +%T)" >> $OUT/logs/waves.log
run e01 serial_killer speculator & run e02 necromancer fortune_teller & wait
run e03 serial_killer fortune_teller & run e04 necromancer speculator & wait
run e05 serial_killer speculator & run e06 necromancer fortune_teller & wait
echo "done $(date +%T)" >> $OUT/logs/waves.log
