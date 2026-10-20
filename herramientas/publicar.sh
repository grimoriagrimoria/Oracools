#!/usr/bin/env bash
# Publica web/ en https://cools.oraculos.app (hosting Namecheap, cuenta rociqtec).
#
# Uso:  bash herramientas/publicar.sh
#       ORACOOLS_LLAVE=~/.ssh/otra_llave bash herramientas/publicar.sh
set -euo pipefail

HOST=business149-5.web-hosting.com
PUERTO=21098
USUARIO=rociqtec
DESTINO=/home/rociqtec/public_html/cools.oraculos.app
URL=https://cools.oraculos.app
LLAVE=${ORACOOLS_LLAVE:-~/.ssh/oraculos_deploy}

cd "$(dirname "$0")/../web"
echo "Subiendo web/ a $DESTINO …"
# Se reemplazan sólo los archivos de la app; .well-known (certificados) y cgi-bin se quedan.
tar -czf - . | ssh -i "$LLAVE" -o IdentitiesOnly=yes -o BatchMode=yes -p "$PUERTO" "$USUARIO@$HOST" \
  "mkdir -p '$DESTINO' && cd '$DESTINO' && tar -xzf - && chmod -R u=rwX,go=rX . && ls -la"
echo "Listo: $URL"
