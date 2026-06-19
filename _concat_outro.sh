set -e
XF=0.35
for n in 01 02 03 04 05; do
  in="output/shorts_split/short_${n}.mp4"
  out="output/shorts_final/short_${n}.mp4"
  dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$in")
  off=$(python3 -c "print(f'{$dur-$XF:.3f}')")
  ffmpeg -y -loglevel error -i "$in" -i output/outro.mp4 -filter_complex "\
[0:v]fps=30,format=yuv420p,setsar=1,settb=AVTB[v0];\
[1:v]fps=30,format=yuv420p,setsar=1,settb=AVTB[v1];\
[v0][v1]xfade=transition=fadeblack:duration=$XF:offset=$off[v];\
[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a0];\
[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a1];\
[a0][a1]acrossfade=d=$XF:c1=tri:c2=tri[a]" \
    -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
    -c:a aac -b:a 160k "$out"
  echo "done short_${n} (offset=$off)"
done
echo "ALL DONE"
