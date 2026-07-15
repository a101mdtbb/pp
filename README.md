# PP Launcher v8.1

## Requisitos

- Python 3.9+
- GTK4 y PyGObject
- xdg-utils

## Instalación

### Dependencias (Ubuntu/Debian)

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 xdg-utils
```

### Dependencias (Arch / Manjaro)

```bash
sudo pacman -S gtk4 python-gobject xdg-utils
```

### Ejecutar

```bash
cd PP
python3 gtk_launcher.py
```

## Instalación automática (cualquier distro)

Descarga el repo y ejecuta el instalador. Crea un acceso directo en el menú
de aplicaciones (con icono) y un lanzador en `~/.local/bin/pp-launcher`.
Detecta automáticamente el gestor de paquetes (apt, dnf, pacman, zypper, apk)
para instalar las dependencias.

```bash
git clone https://github.com/a101mdtbb/pp
cd pp
./install.sh
```

Para desinstalar (no borra los juegos ni tu configuración):

```bash
./install.sh uninstall
```

## Actualizar

Dentro del launcher, abre el menú (⋮) y usa **Actualizar lista de juegos**
(o **Actualizar programa** para bajar la última versión del código). Los
juegos ya descargados en `~/PP-Games` no se vuelven a bajar.



