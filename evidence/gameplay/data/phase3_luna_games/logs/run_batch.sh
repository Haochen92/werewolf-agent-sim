#!/bin/bash
# Six ten-seat games with GPT-6 Luna (medium reasoning) in every seat and as the summariser, 2026-10-10, two at a time.
cd /home/ubuntu/projects/werewolf-agent-sim
OUT=evidence/game_play_enhancement/data/phase3_luna_games
export GOOGLE_GENAI_MODEL=openai/gpt-6-luna
run() { poetry run python -m evaluation.experiments.phase3_capture --label $1 --out $OUT --lone-killer $2 --neutral $3 > $OUT/logs/$1.log 2>&1; echo "$1 exit $? $(date +%T)" >> $OUT/logs/waves.log; }
echo "luna batch start $(date +%T), commit $(git rev-parse --short HEAD) + working tree" >> $OUT/logs/waves.log
run l01 serial_killer speculator & run l02 necromancer fortune_teller & wait
run l03 serial_killer fortune_teller & run l04 necromancer speculator & wait
run l05 serial_killer speculator & run l06 necromancer fortune_teller & wait
echo "done $(date +%T)" >> $OUT/logs/waves.log
