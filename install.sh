#!/usr/bin/env bash
# PP Launcher - instalador multi-distro
# Instala la app en ~/.local (sin root, salvo para las dependencias del sistema)
# Uso:  ./install.sh        -> instala/actualiza
#       ./install.sh uninstall -> elimina
set -euo pipefail

APP_NAME="PP Launcher"
REPO_RAW="https://raw.githubusercontent.com/a101mdtbb/pp/main"
INSTALL_DIR="$HOME/.local/share/pp-launcher"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

download() {
    local url="$1" out="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$out"
    else
        wget -qO "$out" "$url"
    fi
}

install_deps() {
    echo "==> Instalando dependencias del sistema..."
    if command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y python3 python3-gi python3-gi-cairo \
            gir1.2-gtk-4.0 xdg-utils p7zip-full unrar
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-gobject gtk4 xdg-utils p7zip-plugins unrar
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm python gtk4 python-gobject xdg-utils p7zip unrar
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y python3 python3-gobject gtk4 xdg-utils p7zip unrar
    elif command -v apk >/dev/null 2>&1; then
        sudo apk add python3 py3-gobject3 gtk4 xdg-utils p7zip unrar
    else
        echo "ADVERTENCIA: no se reconoció el gestor de paquetes."
        echo "Instala manualmente: python3, PyGObject (python3-gobject), GTK4, xdg-utils."
    fi
}

do_install() {
    echo "==> Instalando $APP_NAME..."
    mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

    echo "==> Descargando archivos del repositorio..."
    for f in gtk_launcher.py download_manager.py catalog.json README.md pp.svg; do
        download "$REPO_RAW/$f" "$INSTALL_DIR/$f"
    done
    chmod +x "$INSTALL_DIR/gtk_launcher.py"

    install_deps

    echo "==> Creando lanzador en $BIN_DIR/pp-launcher"
    cat > "$BIN_DIR/pp-launcher" <<EOF
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/gtk_launcher.py" "\$@"
EOF
    chmod +x "$BIN_DIR/pp-launcher"

    echo "==> Creando acceso directo en el menú..."
    cat > "$DESKTOP_DIR/pp-launcher.desktop" <<EOF
[Desktop Entry]
Name=PP Launcher
Comment=Tienda de descargas de juegos
Exec=$BIN_DIR/pp-launcher
Icon=pp
Terminal=false
Type=Application
Categories=Game;
StartupNotify=true
EOF
    cp "$INSTALL_DIR/pp.svg" "$ICON_DIR/pp.svg"
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" || true
    command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" || true

    echo
    echo "==> ¡Listo! Abre 'PP Launcher' desde el menú de aplicaciones."
    echo "    (Si no aparece, cierra sesión y vuelve a entrar, o ejecuta: $BIN_DIR/pp-launcher)"
}

do_uninstall() {
    echo "==> Desinstalando $APP_NAME..."
    rm -f "$BIN_DIR/pp-launcher" "$DESKTOP_DIR/pp-launcher.desktop" "$ICON_DIR/pp.svg"
    rm -rf "$INSTALL_DIR"
    echo "==> Hecho. Los juegos en ~/PP-Games y tu configuración en ~/.pp-launcher NO se borraron."
}

if [ "${1:-}" = "uninstall" ]; then
    do_uninstall
else
    do_install
fi
