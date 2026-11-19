#!/usr/bin/env bash
# Add the generated background music to the rendered videos.
#   ./add_music.sh voice  in.mp4 music.wav out.mp4   # music ducks under speech
#   ./add_music.sh silent in.mp4 music.wav out.mp4   # music replaces audio
set -euo pipefail
mode=$1 in=$2 music=$3 out=$4
if [ "$mode" = silent ]; then
  ffmpeg -v error -y -i "$in" -i "$music" -map 0:v -map 1:a -c:v copy \
    -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k -ar 44100 -shortest -movflags +faststart "$out"
else
  ffmpeg -v error -y -i "$in" -i "$music" -filter_complex \
    "[0:a]asplit=2[v][sc];[1:a]volume=0.30[m];[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350:makeup=1[md];[v][md]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 44100 -movflags +faststart "$out"
fi
