#!/bin/zsh
# uso: genera_uno.sh ID  (legge la consegna da consegne.jsonl, scrive gemelli/ID.txt; non rifà quelli già fatti)
D="$HOME/umanizza-corpus/detector"; id="$1"; out="$D/gemelli/$id.txt"
[ -s "$out" ] && exit 0
riga=$(grep -F "\"id\": \"$id\"" "$D/consegne.jsonl")
m=$(print -r -- "$riga" | python3 -I -c 'import json,sys;print(json.loads(sys.stdin.read())["generatore"])')
p=$(print -r -- "$riga" | python3 -I -c 'import json,sys;print(json.loads(sys.stdin.read())["prompt"])')
for t in 1 2; do
  if [[ "$m" == claude-* ]]; then
    (cd "$D/vuota" && claude -p --model "$m" --setting-sources "" --tools "" --disable-slash-commands "$p" < /dev/null > "$out.tmp" 2> "$D/log/$id.log")
  else
    codex exec --ignore-user-config --ephemeral --skip-git-repo-check --sandbox read-only -C "$D/vuota" -m "$m" \
      -c model_reasoning_effort="medium" -o "$out.tmp" "$p" < /dev/null > "$D/log/$id.log" 2>&1
  fi
  if [ "$(wc -w < "$out.tmp" 2>/dev/null || echo 0)" -ge 15 ]; then mv "$out.tmp" "$out"; echo "$id $m $(wc -w < "$out")"; exit 0; fi
done
rm -f "$out.tmp"; echo "$id $m FALLITO"
