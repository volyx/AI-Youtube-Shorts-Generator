set -e
XF=0.35
for n in 01 02 03 04 05; do
  in="output/shorts2_split/short_${n}.mp4"
  out="output/shorts2_final/short_${n}.mp4"
  dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$in")
  off=$(awk "BEGIN{printf \"%.3f\", $dur-$XF}")
  ffmpeg -y -loglevel error -i "$in" -i output/outro.mp4 -filter_complex "\
[0:v]fps=30,format=yuv420p,setsar=1,settb=AVTB[v0];[1:v]fps=30,format=yuv420p,setsar=1,settb=AVTB[v1];\
[v0][v1]xfade=transition=fadeblack:duration=$XF:offset=$off[v];\
[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];\
[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];\
[a0][a1]acrossfade=d=$XF:c1=tri:c2=tri[a]" \
    -map "[v]" -map "[a]" -c:v h264_videotoolbox -b:v 8M -allow_sw 1 -pix_fmt yuv420p -c:a aac -b:a 160k "$out"
  echo "done short_${n} (off=$off)"
done
echo "ALL DONE"
