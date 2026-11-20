#!/bin/bash
# Six ten-seat games with gemini-3.5-flash in every seat and as the summariser (2026-10-10), two at a time.
cd /home/ubuntu/projects/werewolf-agent-sim
OUT=evidence/game_play_enhancement/data/phase3_flash_games
export GOOGLE_GENAI_MODEL=gemini-3.5-flash
run() { poetry run python -m evaluation.experiments.phase3_capture --label $1 --out $OUT --lone-killer $2 --neutral $3 > $OUT/logs/$1.log 2>&1; echo "$1 exit $? $(date +%T)" >> $OUT/logs/waves.log; }
echo "flash batch start $(date +%T), commit $(git rev-parse --short HEAD)" >> $OUT/logs/waves.log
run f01 serial_killer speculator & run f02 necromancer fortune_teller & wait
run f03 serial_killer fortune_teller & run f04 necromancer speculator & wait
run f05 serial_killer speculator & run f06 necromancer fortune_teller & wait
echo "done $(date +%T)" >> $OUT/logs/waves.log
