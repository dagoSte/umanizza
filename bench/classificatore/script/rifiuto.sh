#!/bin/zsh
# vero (0) se il file è un rifiuto
grep -q -i -E "^(non posso|mi dispiace|non sono in grado|purtroppo non)|non posso (aiutar|scriver|crear)" "$1"
