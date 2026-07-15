# PP Launcher v8.1

**Tienda de Juegos y Herramientas Moderna para Linux**

PP Launcher es una aplicación de escritorio moderna construida con GTK4 y Python, diseñada como una tienda de descargas de juegos profesional con interfaz tipo Steam/Lutris. Incluye gestor de descargas, carátulas desde SteamGridDB y vista previa de gameplay en YouTube.

## Características

- **Interfaz Moderna**: Diseño tipo tienda con tema oscuro y acentos configurables
- **Búsqueda en Tiempo Real**: Filtra juegos y herramientas mientras escribes
- **Catálogo Completo**: 35+ juegos y herramientas
- **Gestor de Descargas**: Extrae enlaces directos y descarga con barra de progreso
- **Carátulas**: Gradientes con emoji y descarga automática desde SteamGridDB
- **Carátula manual**: Elige la imagen exacta desde SteamGridDB (como Heroic), con búsqueda y vista previa
- **Preferencias**: Tema GTK, color de acento, zoom, orden y más
- **Atajos**: Ctrl+Q (salir), Ctrl+F (buscar)

## Requisitos

- Python 3.9+
- GTK4 y PyGObject
- xdg-utils (para abrir URLs en el navegador)

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

## Estructura del Proyecto

```
PP/
├── gtk_launcher.py        # Aplicación GTK4 principal (entry point)
├── download_manager.py    # Gestor de descargas (extracción de enlaces y descarga)
└── catalog.json           # Catálogo de juegos/herramientas
```

## Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl+Q` | Salir |
| `Ctrl+F` | Buscar |
| `Esc` | Limpiar búsqueda |

## Licencia

GPL-3.0-or-later

## Autor

- **a101mdtbb** - [GitHub](https://github.com/a101mdtbb)
