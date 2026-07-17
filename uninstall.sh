#!/usr/bin/env bash
# PP Launcher - Desinstalación completa
set -e

echo "=== PP Launcher - Desinstalador ==="
echo ""
echo "Esto eliminará:"
echo "  1. El launcher        (~/.local/share/pp-launcher)"
echo "  2. Configuración      (~/.pp-launcher)"
echo "  3. Juegos descargados  (~/PP-Games)"
echo ""
read -p "¿Continuar? [s/N] " resp
if [[ "$resp" != "s" && "$resp" != "S" ]]; then
    echo "Cancelado."
    exit 0
fi

echo ""
echo "Eliminando launcher..."
rm -rf ~/.local/share/pp-launcher

echo "Eliminando configuración y covers..."
rm -rf ~/.pp-launcher

echo "Eliminando juegos descargados..."
rm -rf ~/PP-Games

echo ""
echo "PP Launcher desinstalado completamente."
echo "Si descargaste el código fuente, elimínalo también con:"
echo "  rm -rf ~/Downloads/pp-main"
