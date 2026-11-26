#!/bin/zsh
# Rigenera i gemelli mancanti, ritenta una volta i rifiuti, scrive escluse.txt
cd "$HOME/umanizza-corpus/detector"
mancanti() { python3 -I -c "
import json,pathlib
for l in open('consegne.jsonl'):
    r=json.loads(l)
    if not pathlib.Path('gemelli',r['id']+'.txt').exists(): print(r['id'])"; }
mancanti | xargs -P 10 -n 1 ./script/genera_uno.sh > log/rigenera_1.txt 2>&1
for f in gemelli/*.txt; do ./script/rifiuto.sh "$f" && mv "$f" "gemelli-scartati/$(basename $f .txt).rifiuto1.txt"; done
mancanti | xargs -P 10 -n 1 ./script/genera_uno.sh > log/rigenera_2.txt 2>&1
: > escluse.txt
for f in gemelli/*.txt; do ./script/rifiuto.sh "$f" && { basename $f .txt >> escluse.txt; mv "$f" "gemelli-scartati/$(basename $f .txt).rifiuto2.txt"; }; done
mancanti | grep -v -x -F -f escluse.txt >> escluse.txt
echo "gemelli: $(ls gemelli/*.txt | wc -l) · esclusi: $(wc -l < escluse.txt)"; cat escluse.txt
