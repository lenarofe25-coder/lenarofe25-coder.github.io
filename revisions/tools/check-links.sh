#!/usr/bin/env bash
# Vérifie une liste d'URL (une par ligne) : code HTTP final, URL finale, titre de la page.
# Usage : tools/check-links.sh urls.txt
while read -r u; do
  [ -z "$u" ] && continue
  out=$(curl -sL --max-time 25 -A "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36" -H "Accept-Language: fr-FR,fr;q=0.9" -o /tmp/.lc_body -w "%{http_code} %{url_effective}" "$u")
  title=$(tr '\n' ' ' < /tmp/.lc_body | grep -oiP '<title[^>]*>\K[^<]*' | head -1 | sed 's/&#039;/'"'"'/g;s/&amp;/\&/g;s/  */ /g' | cut -c1-110)
  echo "$out | $title"
done < "$1"
