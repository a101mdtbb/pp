#!/usr/bin/env python3
"""PP Launcher v8.1 - GTK4 nativo estilo Lutris + Descargas + YouTube"""
import os as _os
_typelib = _os.path.join(_os.path.expanduser("~"), ".local", "lib", "girepository-1.0")
if _os.path.isdir(_typelib):
    _old = _os.environ.get("GI_TYPELIB_PATH", "")
    _os.environ["GI_TYPELIB_PATH"] = _typelib + (":" + _old if _old else "")
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib, Pango
import json
import os
import re
import shlex
import unicodedata
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

# Asegura que el módulo download_manager (en el mismo directorio) sea importable
# sin importar desde dónde se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from download_manager import DownloadManager, DOWNLOADS_DIR, find_exe_in_dir, _sanitize_filename

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Catálogo de juegos (junto al launcher, con fallback a la ubicación empaquetada).
CATALOG_PATH = os.path.join(APP_DIR, "catalog.json")
if not os.path.exists(CATALOG_PATH):
    CATALOG_PATH = os.path.join(APP_DIR, "pp_launcher", "data", "catalog.json")
SETTINGS_FILE = os.path.join(Path.home(), ".pp-launcher", "settings.json")
COVERS_DIR = os.path.join(Path.home(), ".pp-launcher", "covers")
SGDB_BASE = "https://www.steamgriddb.com/api/v2"
SGDB_UA = "PP-Launcher/8.1"

# Repositorio remoto para actualizaciones (lista de juegos y programa)
REPO_OWNER = "a101mdtbb"
REPO_NAME = "pp"
_repo_branch = None


def get_repo_raw_base():
    global _repo_branch
    if _repo_branch is None:
        branch = "main"
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}",
                headers={"User-Agent": "PP-Launcher",
                         "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                branch = json.loads(r.read()).get("default_branch", "main")
        except Exception:
            branch = "main"
        for cand in (branch, "master", "main"):
            try:
                req = urllib.request.Request(
                    f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{cand}/catalog.json",
                    headers={"User-Agent": "PP-Launcher"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    if r.status == 200:
                        _repo_branch = cand
                        break
            except Exception:
                continue
        if _repo_branch is None:
            _repo_branch = branch
    return f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{_repo_branch}"

COVERS = {
    "Assassin's Creed II": ("#8b0000", "#4a0000", "\u2694\ufe0f"),
    "Assassin's Creed IV": ("#1a1a2e", "#0a0a15", "\u2694\ufe0f"),
    "Balatro": ("#2d1b69", "#1a0f3d", "\U0001f0cf"),
    "Bully": ("#8b6914", "#5c4610", "\U0001f393"),
    "Cuphead": ("#b8860b", "#8b6508", "\u2615"),
    "Dragon Ball Impact": ("#ff6600", "#cc4400", "\U0001f525"),
    "Dragon Ball FighterZ": ("#ff4500", "#cc3600", "\U0001f525"),
    "Far Cry 2": ("#556b2f", "#3a4a1f", "\U0001f33f"),
    "Far Cry 3": ("#006400", "#004200", "\U0001f33f"),
    "Geometry Dash": ("#00bfff", "#008ccc", "\u25b2"),
    "GTA IV": ("#2f4f4f", "#1a2d2d", "\U0001f3ce\ufe0f"),
    "GTA IV Lite": ("#2f4f4f", "#1a2d2d", "\U0001f3ce\ufe0f"),
    "GTA San Andreas": ("#4a3728", "#2d2118", "\U0001f3ce\ufe0f"),
    "GTA V": ("#1a472a", "#0e2d1a", "\U0001f3ce\ufe0f"),
    "GTA V Lite": ("#1a472a", "#0e2d1a", "\U0001f3ce\ufe0f"),
    "GTA V Super Lite": ("#1a472a", "#0e2d1a", "\U0001f3ce\ufe0f"),
    "GTA V Hyper Lite 2 GB": ("#1a472a", "#0e2d1a", "\U0001f3ce\ufe0f"),
    "Hollow Knight": ("#191970", "#0f0f4a", "\U0001f41e"),
    "Jump Force": ("#8b0000", "#5c0000", "\U0001f44a"),
    "Naruto Storm 4": ("#ff8c00", "#cc7000", "\U0001f34c"),
    "NFS Most Wanted": ("#483d8b", "#2d2760", "\U0001f3ce\ufe0f"),
    "Mortal Kombat XL": ("#8b0000", "#5c0000", "\U0001f480"),
    "Outlast": ("#2f2f2f", "#1a1a1a", "\U0001f47b"),
    "Resident Evil 4": ("#3d0000", "#200000", "\U0001f9e0"),
    "Roblox": ("#cc0000", "#880000", "\U0001f3ae"),
    "Red Dead Redemption": ("#8b4513", "#5c2e0d", "\U0001f920"),
    "Sonic 3 AIR": ("#0066cc", "#004499", "\U0001f300"),
    "Sonic Mania": ("#0077dd", "#0055aa", "\U0001f300"),
    "Stardew Valley": ("#228b22", "#166b16", "\U0001f33e"),
    "Minecraft APK X86": ("#556b2f", "#3a4a1f", "\U0001f9f1"),
    "Minecraft Bedrock": ("#556b2f", "#3a4a1f", "\U0001f9f1"),
    "The Forest": ("#1a3300", "#0d1a00", "\U0001f332"),
    "Terraria": ("#8b4513", "#5c2e0d", "\u26cf\ufe0f"),
    "Walking Dead S1": ("#2f2f2f", "#1a1a1a", "\U0001f9df"),
    "Blasphemous": ("#8b0000", "#5c0000", "\u2620\ufe0f"),
}
CUSTOM_COVERS = ("#6a0dad", "#4a0080", "\U0001f3ae")

SGDB_NAME_MAP = {
    "Assassin's Creed IV": "Assassin's Creed IV Black Flag",
    "GTA IV": "Grand Theft Auto IV",
    "GTA IV Lite": "Grand Theft Auto IV",
    "GTA San Andreas": "Grand Theft Auto San Andreas",
    "GTA V": "Grand Theft Auto V",
    "GTA V Lite": "Grand Theft Auto V",
    "GTA V Super Lite": "Grand Theft Auto V",
    "GTA V Hyper Lite 2 GB": "Grand Theft Auto V",
    "Naruto Storm 4": "Naruto Shippuden Ultimate Ninja Storm 4",
    "NFS Most Wanted": "Need for Speed Most Wanted",
    "Mortal Kombat XL": "Mortal Kombat XL",
    "Sonic 3 AIR": "Sonic 3 Angel Island Revisited",
    "Minecraft APK X86": "Minecraft",
    "Minecraft Bedrock": "Minecraft",
    "Walking Dead S1": "The Walking Dead",
    "Dragon Ball Impact": "Dragon Ball Z Budokai Tenkaichi",
    "Resident Evil 4": "Resident Evil 4",
    "Jump Force": "Jump Force",
    "The Witcher 3: Wild Hunt": "The Witcher 3",
    "Dark Souls III": "Dark Souls III",
    "Hades 2": "Hades II",
    "Red Dead Redemption 2": "Red Dead Redemption II",
    "Resident Evil 2 Remake": "Resident Evil 2",
    "Resident Evil 3 Remake": "Resident Evil 3",
    "Resident Evil Village": "Resident Evil Village",
    "God of War (2018)": "God of War",
    "Spider-Man (2018)": "Marvel's Spider-Man",
    "Tomb Raider (2013)": "Tomb Raider",
    "Rise of the Tomb Raider": "Rise of the Tomb Raider",
    "Red Dead Redemption 2": "Red Dead Redemption 2",
    "Fallout 4": "Fallout 4",
    "Fallout: New Vegas": "Fallout New Vegas",
    "Far Cry 5": "Far Cry 5",
    "Far Cry 6": "Far Cry 6",
    "Far Cry Primal": "Far Cry Primal",
    "Left 4 Dead 2": "Left 4 Dead 2",
    "Portal 2": "Portal 2",
    "BioShock Infinite": "BioShock Infinite",
    "Mafia: Definitive Edition": "Mafia Definitive Edition",
    "Just Cause 4": "Just Cause 4",
    "Halo Infinite": "Halo Infinite",
    "Sonic Frontiers": "Sonic Frontiers",
    "Persona 5": "Persona 5",
    "Hitman 3": "Hitman 3",
    "Yakuza 0": "Yakuza 0",
    "Street Fighter 6": "Street Fighter 6",
    "Tekken 8": "Tekken 8",
    "Uncharted 4": "Uncharted 4",
    "Watch Dogs": "Watch Dogs",
    "Sleeping Dogs": "Sleeping Dogs",
    "Assassin's Creed Odyssey": "Assassin's Creed Odyssey",
    "Assassin's Creed Valhalla": "Assassin's Creed Valhalla",
    "Assassin's Creed Unity": "Assassin's Creed Unity",
    "Assassin's Creed Brotherhood": "Assassin's Creed Brotherhood",
    "Assassin's Creed Origins": "Assassin's Creed Origins",
    "Dishonored": "Dishonored",
    "Ghost of Tsushima": "Ghost of Tsushima",
    "Horizon Zero Dawn": "Horizon Zero Dawn",
    "Detroit: Become Human": "Detroit Become Human",
    "The Last of Us": "The Last of Us",
    "EA FC 24": "EA Sports FC 24",
    "DOOM (2016)": "DOOM",
}

CSS = b"""
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; } }
@keyframes scaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }

.nav-tab { border-radius: 999px; padding: 7px 16px; font-size: 13.5px; font-weight: 600; transition: background 180ms ease, color 180ms ease, transform 160ms ease; }
.nav-tab:hover { background: alpha(currentColor, 0.08); }
.nav-tab:active { transform: scale(0.98); }
.nav-tab-active { font-weight: 700; background: alpha(@accent_bg_color, 0.18); color: @accent_bg_color; }

.brand-icon { color: @accent_bg_color; -gtk-icon-size: 22px; }
.brand-label { font-size: 17px; font-weight: 800; letter-spacing: -0.4px; }
.search-pill { border-radius: 999px; padding: 5px 12px; background: alpha(currentColor, 0.06); box-shadow: inset 0 0 0 1px alpha(currentColor, 0.08); }

.chip { border-radius: 999px; padding: 2px 9px; font-size: 10px; font-weight: 700; background: alpha(currentColor, 0.13); }
.badge-installed { border-radius: 999px; padding: 2px 8px; font-size: 9.5px; font-weight: 700; background: #26a269; color: white; }

.add-game-cell { border: 2px dashed alpha(currentColor, 0.25); border-radius: 12px; background: transparent; transition: all 200ms ease; }
.add-game-cell:hover { transform: scale(1.03); }

.info-pill { border-radius: 6px; padding: 3px 8px; font-size: 10px; transition: all 200ms ease; }
.info-pill:hover { transform: scale(1.08); }

.hero { padding: 18px 20px; border-radius: 14px; background: alpha(currentColor, 0.05); }
.detail-cover { min-height: 255px; min-width: 170px; border-radius: 12px; box-shadow: 0 6px 20px alpha(black, 0.40); animation: scaleIn 300ms ease; }
.section-title { font-size: 11.5px; font-weight: 800; letter-spacing: 0.7px; text-transform: uppercase; opacity: 0.55; }
.meta-row { font-size: 11px; opacity: 0.7; }
.desc { font-size: 13px; line-height: 1.55; opacity: 0.9; }
.kv { font-size: 12px; }
.kv-key { opacity: 0.55; }

button.suggested-action { border-radius: 10px; font-weight: 700; padding: 9px 18px; transition: all 200ms ease; }
button.suggested-action:hover { transform: translateY(-1px); }
button.suggested-action:active { transform: scale(0.97); }
button.destructive-action { border-radius: 10px; font-weight: 700; padding: 9px 18px; transition: all 200ms ease; }
button.destructive-action:hover { transform: translateY(-1px); }
button.destructive-action:active { transform: scale(0.97); }

.dl-panel { padding: 8px 10px; animation: slideUp 300ms ease; }
.toast-err { border-radius: 12px; padding: 8px 12px; background: alpha(#e01b24, 0.16); box-shadow: inset 0 0 0 1px alpha(#e01b24, 0.40); margin: 4px 6px; }
.dl-pop-title { font-size: 15px; font-weight: 800; letter-spacing: 0.2px; margin: 2px 2px 4px; }
.dl-badge { background: #e01b24; color: white; font-size: 9px; font-weight: 800; border-radius: 999px; padding: 0px 4px; margin-top: -3px; margin-right: -4px; min-width: 12px; }
.dl-card { border-radius: 14px; padding: 13px 15px; margin: 3px 2px; background: alpha(currentColor, 0.06); box-shadow: 0 1px 4px alpha(black, 0.25); animation: fadeIn 250ms ease; }
.dl-card-name { font-size: 14px; font-weight: 800; letter-spacing: 0.2px; }
.dl-pct { font-size: 14px; font-weight: 800; color: @accent_bg_color; }
.dl-bar { min-height: 10px; }
.dl-bar trough { min-height: 10px; border-radius: 999px; background: alpha(currentColor, 0.12); }
.dl-bar progress { min-height: 10px; border-radius: 999px; background: @accent_bg_color; }
.dl-meta { font-size: 12px; opacity: 0.78; }
.dl-eta { font-size: 12px; font-weight: 700; opacity: 0.95; }
.dl-iconbtn { border-radius: 999px; min-width: 32px; min-height: 32px; padding: 3px; transition: all 160ms ease; }
.dl-iconbtn:hover { background: alpha(currentColor, 0.12); }
.slide-item { border-radius: 8px; min-height: 130px; min-width: 200px; background-color: #333; transition: all 200ms ease; animation: fadeIn 400ms ease; }
.slide-item:hover { transform: scale(1.05); }
.slide-item .dim-label { color: white; }

/* --- Tarjetas de juego modernas --- */
.game-cell { margin: 0; border-radius: 16px; background: transparent; transition: transform 220ms cubic-bezier(0.2,0.8,0.2,1); }
.game-cell:hover { transform: translateY(-6px); }
.cover-box { border: 0; border-radius: 16px; overflow: hidden; transition: all 200ms ease; }
.cover-box picture { border-radius: 16px; }
.card-body { padding: 11px 12px 13px; }
.game-title { font-size: 13.5px; font-weight: 800; letter-spacing: 0.2px; line-height: 1.25; }
.game-sub { font-size: 10.5px; opacity: 0.7; }
.game-overlay { background: linear-gradient(to top, alpha(black, 0.78) 10%, alpha(black, 0.0) 70%); opacity: 0; transition: opacity 200ms ease; }
.game-cell:hover .game-overlay { opacity: 1; }
.game-play { border-radius: 999px; min-width: 38px; min-height: 38px; padding: 4px; background: alpha(white, 0.14); color: white; transition: transform 160ms ease, background 160ms ease; }
.game-play:hover { background: @accent_bg_color; transform: scale(1.08); }
.badge-installed { border-radius: 999px; padding: 3px 9px; font-size: 9.5px; font-weight: 800; letter-spacing: 0.4px; background: #26a269; color: white; box-shadow: 0 1px 3px alpha(black, 0.4); }
.chip { border-radius: 999px; padding: 3px 10px; font-size: 10px; font-weight: 700; background: alpha(currentColor, 0.13); }
.chip.accent { background: alpha(@accent_bg_color, 0.18); color: @accent_bg_color; }
.chip-inv { background: alpha(white, 0.22); color: white; }
.game-foot { background: none; padding: 16px 10px 12px; }
.game-foot-title { color: white; font-size: 13px; font-weight: 800; letter-spacing: 0.2px; line-height: 1.2; text-shadow: 0 1px 3px alpha(black, 0.6); }
.game-foot-sub { color: alpha(white, 0.82); font-size: 10px; text-shadow: 0 1px 2px alpha(black, 0.6); }

/* --- Vista de detalle --- */
.hero { border-radius: 18px; background: linear-gradient(135deg, alpha(@accent_bg_color, 0.20), alpha(currentColor, 0.04)); box-shadow: inset 0 0 0 1px alpha(currentColor, 0.06); }
.hero-bg { opacity: 0.32; border-radius: 18px; overflow: hidden; }
.hero-scrim { border-radius: 18px; background: linear-gradient(to bottom, alpha(black, 0.40), alpha(black, 0.18)); }
.detail-cover { min-height: 260px; min-width: 175px; border-radius: 14px; box-shadow: 0 10px 28px alpha(black, 0.45); }
.detail-title { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.detail-action { border-radius: 12px; font-weight: 700; font-size: 14px; padding: 11px 22px; transition: all 180ms ease; }
.detail-action.suggested-action:hover { transform: translateY(-2px); box-shadow: 0 8px 18px alpha(@accent_bg_color, 0.4); }
.detail-action.destructive-action:hover { transform: translateY(-2px); }
.detail-card { border-radius: 14px; padding: 14px 16px; background: alpha(currentColor, 0.045); box-shadow: inset 0 0 0 1px alpha(currentColor, 0.05); }
.section-title { font-size: 11.5px; font-weight: 800; letter-spacing: 0.8px; text-transform: uppercase; opacity: 0.6; }
.desc { font-size: 13.5px; line-height: 1.6; opacity: 0.92; }
.kv { font-size: 12.5px; }
.kv-key { opacity: 0.55; }

/* --- Preferencias (grupos tipo libadwaita) --- */
.pref-group { border-radius: 14px; background: alpha(currentColor, 0.045); padding: 4px 14px; box-shadow: inset 0 0 0 1px alpha(currentColor, 0.05); }
.pref-group-title { font-size: 12px; font-weight: 800; letter-spacing: 0.4px; opacity: 0.65; margin: 12px 2px 6px; text-transform: uppercase; }
.pref-row { padding: 8px 2px; }
.pref-row + .pref-row { box-shadow: inset 0 1px 0 alpha(currentColor, 0.06); }
.sidebar { background: transparent; padding-right: 4px; }
.sidebar row { border-radius: 10px; padding: 4px 8px; }
.sidebar row:selected { background: alpha(@accent_bg_color, 0.18); color: @accent_bg_color; }

/* --- Acerca de --- */
.about-box { border-radius: 18px; padding: 30px; background: linear-gradient(135deg, alpha(@accent_bg_color, 0.18), alpha(currentColor, 0.03)); box-shadow: inset 0 0 0 1px alpha(currentColor, 0.06); }
.about-logo { font-size: 56px; }
.about-title { font-size: 26px; font-weight: 800; letter-spacing: -0.3px; }
.about-sub { font-size: 13px; opacity: 0.7; }

/* --- Scrollbars finos y modernos --- */
scrollbar { background: transparent; }
scrollbar slider { background: alpha(currentColor, 0.26); border-radius: 999px; border: none; min-width: 9px; min-height: 9px; transition: background 160ms ease; }
scrollbar slider:hover { background: alpha(currentColor, 0.42); }
scrollbar.vertical slider { min-width: 9px; }
scrollbar.horizontal slider { min-height: 9px; }

/* --- Estado vacio --- */
.empty-state { opacity: 0.9; }
.empty-icon { opacity: 0.35; }
"""

DEFAULT_SETTINGS = {
    "gtk_theme": "Adwaita",
    "minimize_on_launch": True,
    "show_badges": True,
    "sgdb_api_key": "2e86d68a79a9734c83962b28d21bcb32",
    "auto_fetch_covers": True,
    "accent_color": "#3584e4",
    "accent_hue": 211,
    "cover_radius": 10,
    "grid_spacing": 12,
    "show_title": True,
    "show_category": True,
    "show_cover_border": True,
    "sort_order": "name",
    "animations": True,
    "font_scale": 1.0,
    "card_bg": "#00000000",
    "zoom": 1.0,
}


def detect_gtk_themes():
    dirs = [
        Path("/usr/share/themes"),
        Path.home() / ".themes",
        Path.home() / ".local" / "share" / "themes",
    ]
    themes = set()
    for d in dirs:
        if d.is_dir():
            for child in d.iterdir():
                if child.is_dir() and (child / "gtk-4.0").is_dir():
                    themes.add(child.name)
    for t in ("Adwaita", "Adwaita-dark"):
        themes.add(t)
    return sorted(themes)


def load_catalog():
    try:
        with open(CATALOG_PATH) as f:
            return json.load(f).get("apps", [])
    except Exception:
        return []


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            s = json.load(f)
            merged = {**DEFAULT_SETTINGS, **s}
            for k, v in DEFAULT_SETTINGS.items():
                if k not in merged or not merged[k]:
                    merged[k] = v
            return merged
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(s):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)


def _fmt_size(num_bytes):
    mb = num_bytes / 1024 / 1024
    if mb >= 1000:
        return f"{mb / 1024:.2f} GB"
    return f"{mb:.0f} MB"


def _fmt_eta(secs):
    secs = int(secs)
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def find_terminal():
    for term in ["x-terminal-emulator", "gnome-terminal", "konsole",
                 "xfce4-terminal", "alacritty", "kitty", "xterm"]:
        try:
            if subprocess.run(["which", term], capture_output=True, timeout=3).returncode == 0:
                return term
        except Exception:
            continue
    return None


def _safe_cover_name(name):
    safe = re.sub(r'[^\w\s-]', '', name).strip()
    safe = re.sub(r'\s+', '_', safe)
    return safe[:80] if safe else "unknown"


def get_cached_cover(name):
    path = os.path.join(COVERS_DIR, _safe_cover_name(name) + ".jpg")
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return path
    return None


def _norm_name(s):
    """Normaliza un nombre para comparación: minúsculas, sin acentos ni símbolos."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 ]", "", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def search_sgdb(game_name, api_key):
    if not api_key:
        return None
    search_term = SGDB_NAME_MAP.get(game_name, game_name)
    norm_term = _norm_name(search_term)
    try:
        req = urllib.request.Request(
            f"{SGDB_BASE}/search/autocomplete/{urllib.request.quote(search_term)}",
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": SGDB_UA}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("success") and data.get("data"):
            results = data["data"]
            # 1) Coincidencia exacta normalizada
            for r in results:
                if _norm_name(r.get("name", "")) == norm_term:
                    return r.get("id")
            # 2) Si solo hay un resultado, es confiable
            if len(results) == 1:
                return results[0].get("id")
            # 3) Coincidencia por prefijo con consistencia de numeros:
            #    el resultado debe contener todos los numeros del termino
            #    (evita confundir "Far Cry 5" con "Far Cry", "RE2 Remake"
            #    con "RE2" clasico) y se elige el nombre mas especifico.
            term_nums = set(re.findall(r"\d+", norm_term))
            candidates = []
            for r in results:
                rn = _norm_name(r.get("name", ""))
                if not rn:
                    continue
                rn_nums = set(re.findall(r"\d+", rn))
                if term_nums and not term_nums.issubset(rn_nums):
                    continue
                if rn.startswith(norm_term) or norm_term.startswith(rn):
                    candidates.append((len(rn), r.get("id")))
            if candidates:
                candidates.sort(reverse=True)
                return candidates[0][1]
            # Sin coincidencia fiable: mejor ninguna que una equivocada
            return None
    except Exception:
        pass
    return None


def fetch_sgdb_cover(game_id, api_key):
    if not api_key or not game_id:
        return None
    try:
        req = urllib.request.Request(
            f"{SGDB_BASE}/grids/game/{game_id}?types=static",
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": SGDB_UA}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("success") and data.get("data"):
            grids = data["data"]
            vertical = []
            horizontal = []
            for g in grids:
                w = g.get("width", 0)
                h = g.get("height", 0)
                if w < 100 or h < 100:
                    continue
                if h >= w:
                    vertical.append(g)
                else:
                    horizontal.append(g)
            best = vertical if vertical else horizontal
            if best:
                best.sort(key=lambda g: g.get("height", 0), reverse=True)
                return best[0].get("url") or best[0].get("thumb")
            if grids:
                return grids[0].get("url") or grids[0].get("thumb")
    except Exception:
        pass
    return None


def save_cover_from_url(game_name, url, api_key=None, max_width=600):
    """Descarga una imagen de carátula y la guarda en caché preservando calidad."""
    try:
        os.makedirs(COVERS_DIR, exist_ok=True)
        path = os.path.join(COVERS_DIR, _safe_cover_name(game_name) + ".jpg")
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Referer": "https://www.steamgriddb.com/"
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
        loader = GdkPixbuf.PixbufLoader()
        loader.write(raw)
        loader.close()
        pixbuf = loader.get_pixbuf()
        if pixbuf:
            w = pixbuf.get_width()
            if w > max_width:
                ns = int(pixbuf.get_height() * max_width / w)
                pixbuf = pixbuf.scale_simple(max_width, ns, GdkPixbuf.InterpType.BILINEAR)
            pixbuf.savev(path, "jpeg", ["quality"], ["95"])
            return path
    except Exception:
        pass
    return None


def _scale_pixbuf_fill(pb, w, h):
    """Recorta un pixbuf para llenar exactamente w x h (centrado)."""
    if not pb or not w or not h:
        return pb
    pw, ph = pb.get_width(), pb.get_height()
    if pw and ph:
        scale = max(w / pw, h / ph)
        nw, nh = max(1, int(round(pw * scale))), max(1, int(round(ph * scale)))
        if nw != pw or nh != ph:
            pb = pb.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
        if nw > w or nh > h:
            sx = max(0, (nw - w) // 2)
            sy = max(0, (nh - h) // 2)
            pb = pb.new_subpixbuf(sx, sy, w, h)
    return pb


def load_scaled_pixbuf(path, w, h):
    """Carga una imagen de carátula recortada (cover) desde un archivo."""
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file(path)
        return _scale_pixbuf_fill(pb, w, h)
    except Exception:
        return None


def download_cover(game_name, api_key, retries=3):
    cached = get_cached_cover(game_name)
    if cached:
        return cached
    for attempt in range(retries):
        try:
            game_id = search_sgdb(game_name, api_key)
            if not game_id:
                if attempt < retries - 1:
                    time.sleep(1.0)
                    continue
                return None
            url = fetch_sgdb_cover(game_id, api_key)
            if not url:
                if attempt < retries - 1:
                    time.sleep(1.0)
                    continue
                return None
            saved = save_cover_from_url(game_name, url, api_key)
            if saved:
                return saved
            if attempt < retries - 1:
                time.sleep(1.0)
                continue
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(1.0)
                continue
            return None
    return None


def search_sgdb_results(game_name, api_key):
    """Devuelve lista de juegos coincidentes en SGDB: [{'id', 'name'}, ...]."""
    if not api_key:
        return []
    search_term = SGDB_NAME_MAP.get(game_name, game_name)
    try:
        req = urllib.request.Request(
            f"{SGDB_BASE}/search/autocomplete/{urllib.request.quote(search_term)}",
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": SGDB_UA}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("success") and data.get("data"):
            return [{"id": r.get("id"), "name": r.get("name", "")} for r in data["data"]]
    except Exception:
        pass
    return []


def fetch_sgdb_grids(game_id, api_key):
    """Devuelve las carátulas (grids) de un juego de SGDB, verticales primero."""
    if not api_key or not game_id:
        return []
    try:
        req = urllib.request.Request(
            f"{SGDB_BASE}/grids/game/{game_id}?types=static",
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": SGDB_UA}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("success") and data.get("data"):
            grids = []
            for g in data["data"]:
                w = g.get("width", 0)
                h = g.get("height", 0)
                if w < 100 or h < 100:
                    continue
                grids.append(g)
            grids.sort(key=lambda g: (1 if g.get("height", 0) < g.get("width", 0) else 0,
                                      -g.get("height", 0)))
            return grids
    except Exception:
        pass
    return []


def get_cover(name):
    return COVERS.get(name, CUSTOM_COVERS)


_css_cache = {}  # color -> generated class name
_css_counter = 0


def make_color_css(color):
    global _css_counter
    if color in _css_cache:
        return _css_cache[color]
    _css_counter += 1
    cls = f"pp-cover-{_css_counter}"
    provider = Gtk.CssProvider()
    provider.load_from_data(f".{cls} {{ background-color: {color}; }}".encode())
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display, provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10)
    _css_cache[color] = cls
    return cls


class PPLauncher(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pp.launcher",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.catalog = []
        self.search_term = ""
        self.settings = load_settings()
        self.current_view = "tienda"
        self.zoom = max(0.5, min(2.0, float(self.settings.get("zoom", 1.0))))
        self.store_w, self.store_h = 160, 240
        self.dl_manager = DownloadManager()
        self.dl_widgets = {}
        self._dl_game_names = {}
        self._dl_completion_timers = []
        self._dl_pending_refresh = False

    def do_activate(self):
        css_prov = Gtk.CssProvider()
        css_prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_prov,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.dyn_css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), self.dyn_css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)

        self._apply_theme()

        self.win = Gtk.ApplicationWindow(application=self, title="PP Launcher")
        self.win.set_default_size(1200, 750)
        self.win.connect("close-request", self._on_close)

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_child(main_vbox)

        header = Gtk.HeaderBar()
        self.win.set_titlebar(header)

        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        brand.set_margin_start(6)
        brand_img = Gtk.Image(icon_name="applications-games-symbolic")
        brand_img.add_css_class("brand-icon")
        brand.append(brand_img)
        brand_lbl = Gtk.Label(label="PP Launcher")
        brand_lbl.add_css_class("brand-label")
        brand.append(brand_lbl)
        header.pack_start(brand)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar juegos...")
        self.search_entry.set_hexpand(True)
        self.search_entry.set_size_request(250, -1)
        self.search_entry.add_css_class("search-pill")
        self.search_entry.connect("search-changed", self.on_search_changed)
        header.set_title_widget(self.search_entry)

        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_tooltip_text("Menú")
        popover = Gtk.Popover()
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        menu_box.set_margin_top(4)
        menu_box.set_margin_bottom(4)

        upd_list_item = Gtk.Button()
        upd_list_item.set_has_frame(False)
        _h0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        _h0.append(Gtk.Image(icon_name="view-refresh-symbolic"))
        _h0.append(Gtk.Label(label="Actualizar lista de juegos", xalign=0))
        upd_list_item.set_child(_h0)
        upd_list_item.connect("clicked", self.update_game_list)
        menu_box.append(upd_list_item)

        upd_prog_item = Gtk.Button()
        upd_prog_item.set_has_frame(False)
        _h0b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        _h0b.append(Gtk.Image(icon_name="software-update-available-symbolic"))
        _h0b.append(Gtk.Label(label="Actualizar programa", xalign=0))
        upd_prog_item.set_child(_h0b)
        upd_prog_item.connect("clicked", self.update_program)
        menu_box.append(upd_prog_item)

        menu_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        pref_item = Gtk.Button()
        pref_item.set_has_frame(False)
        _h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        _h.append(Gtk.Image(icon_name="preferences-system-symbolic"))
        _h.append(Gtk.Label(label="Preferencias", xalign=0))
        pref_item.set_child(_h)
        pref_item.connect("clicked", lambda b: self.show_preferences())
        menu_box.append(pref_item)

        menu_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        about_item = Gtk.Button()
        about_item.set_has_frame(False)
        _h3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        _h3.append(Gtk.Image(icon_name="help-about-symbolic"))
        _h3.append(Gtk.Label(label="Acerca de", xalign=0))
        about_item.set_child(_h3)
        about_item.connect("clicked", lambda b: self._show_about())
        menu_box.append(about_item)

        popover.set_child(menu_box)
        menu_btn.set_popover(popover)
        header.pack_end(menu_btn)

        self.dl_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.dl_scroll = Gtk.ScrolledWindow()
        self.dl_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.dl_scroll.set_min_content_width(400)
        self.dl_scroll.set_max_content_height(440)
        self.dl_scroll.set_propagate_natural_height(True)
        self.dl_scroll.set_child(self.dl_list)

        self.dl_empty = Gtk.Label(label="No hay descargas activas")
        self.dl_empty.add_css_class("dim-label")
        self.dl_empty.set_margin_top(28)
        self.dl_empty.set_margin_bottom(28)

        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        pop_box.set_margin_start(10)
        pop_box.set_margin_end(10)
        pop_box.set_margin_top(10)
        pop_box.set_margin_bottom(10)
        pop_box.set_size_request(430, -1)
        dl_hdr = Gtk.Label(label="Descargas")
        dl_hdr.set_xalign(0)
        dl_hdr.add_css_class("dl-pop-title")
        pop_box.append(dl_hdr)
        pop_box.append(self.dl_empty)
        pop_box.append(self.dl_scroll)

        self.dl_popover = Gtk.Popover()
        self.dl_popover.set_child(pop_box)

        badge_overlay = Gtk.Overlay()
        dl_icon = Gtk.Image(icon_name="folder-download-symbolic")
        dl_icon.set_pixel_size(20)
        badge_overlay.set_child(dl_icon)
        self.dl_badge = Gtk.Label(label="")
        self.dl_badge.add_css_class("dl-badge")
        self.dl_badge.set_halign(Gtk.Align.END)
        self.dl_badge.set_valign(Gtk.Align.START)
        self.dl_badge.set_visible(False)
        badge_overlay.add_overlay(self.dl_badge)

        self.dl_menu_button = Gtk.MenuButton()
        self.dl_menu_button.set_child(badge_overlay)
        self.dl_menu_button.set_always_show_arrow(False)
        self.dl_menu_button.set_tooltip_text("Descargas")
        self.dl_menu_button.set_popover(self.dl_popover)
        header.pack_end(self.dl_menu_button)

        self.nav_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.nav_bar.set_margin_start(8)
        self.nav_bar.set_margin_end(8)
        self.nav_bar.set_margin_top(6)
        self.nav_bar.set_margin_bottom(6)
        self.nav_bar.set_halign(Gtk.Align.START)
        main_vbox.append(self.nav_bar)

        self.nav_items = []
        self.build_nav_bar()

        main_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_area.set_hexpand(True)
        main_area.set_vexpand(True)
        main_vbox.append(main_area)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)
        self.stack.set_vexpand(True)
        main_area.append(self.stack)

        self.grid_scroll = Gtk.ScrolledWindow()
        self.grid_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.stack.add_named(self.grid_scroll, "grid")

        self.detail_scroll = Gtk.ScrolledWindow()
        self.detail_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.stack.add_named(self.detail_scroll, "detail")
        self.stack.set_visible_child_name("grid")

        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_homogeneous(False)
        _sp = int(self.settings.get("grid_spacing", 12))
        self.flow_box.set_column_spacing(_sp)
        self.flow_box.set_row_spacing(_sp)
        self.flow_box.set_margin_start(18)
        self.flow_box.set_margin_end(18)
        self.flow_box.set_margin_top(20)
        self.flow_box.set_margin_bottom(20)
        self.flow_box.set_halign(Gtk.Align.CENTER)
        self.flow_box.set_valign(Gtk.Align.START)
        self.flow_box.set_hexpand(False)
        self.flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.grid_scroll.set_child(self.flow_box)
        self.grid_scroll.get_hadjustment().connect(
            "notify::page-size", lambda a, p: self._update_grid_columns())

        self.detail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.detail_scroll.set_child(self.detail_box)

        self.dl_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.dl_panel.add_css_class("dl-panel")
        self.dl_panel.set_visible(False)
        main_area.append(self.dl_panel)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer.set_margin_start(12)
        footer.set_margin_end(12)
        footer.set_margin_top(6)
        footer.set_margin_bottom(6)
        self.status_lbl = Gtk.Label(label="")
        self.status_lbl.set_xalign(0)
        self.status_lbl.add_css_class("dim-label")
        footer.append(self.status_lbl)
        main_vbox.append(footer)

        self.win.present()
        self.load_data()
        GLib.timeout_add(500, self._update_dl_panel)
        threading.Thread(target=self._auto_update_on_start, daemon=True).start()

    def _apply_theme(self):
        gtk_theme = self.settings.get("gtk_theme", "Adwaita")
        s = Gtk.Settings.get_default()
        if s:
            s.set_property("gtk-theme-name", gtk_theme)
        self._apply_appearance()

    def _apply_appearance(self):
        st = self.settings
        accent = st.get("accent_color", "#3584e4")
        radius = int(st.get("cover_radius", 10))
        spacing = int(st.get("grid_spacing", 0))
        font_scale = float(st.get("font_scale", 1.0))
        anim = st.get("animations", True)
        border = st.get("show_cover_border", True)
        card_bg = st.get("card_bg", "#00000000")

        dyn = f"""
@define-color accent_bg_color {accent};
@define-color accent_fg_color #ffffff;

.game-title {{ font-size: {15 * font_scale}px; }}
.game-sub {{ font-size: {10 * font_scale}px; }}
.cover-box {{ border-radius: {radius}px; }}
.cover-box picture {{ border-radius: {radius}px; }}
.game-cell {{ background: {card_bg}; border-radius: {radius}px; }}

.nav-tab-active {{ background: @accent_bg_color; color: @accent_fg_color; }}
.add-game-cell:hover {{ border-color: @accent_bg_color; background: alpha(@accent_bg_color, 0.07); }}
button.suggested-action:hover {{ box-shadow: 0 4px 14px alpha(@accent_bg_color, 0.35); }}
.chip.accent {{ background: alpha(@accent_bg_color, 0.18); color: @accent_bg_color; }}
"""
        if not border:
            dyn += ".cover-box { border: none; }\n"
        if not anim:
            dyn += """.game-cell { animation: none; }
.game-cell:hover { transform: none; }
.game-cell:hover .cover-box { box-shadow: none; }
.nav-tab:hover { background: none; }
.nav-tab:active { transform: none; }
.add-game-cell:hover { transform: none; }
"""
        self.dyn_css.load_from_data(dyn.encode("utf-8"))

        flow = getattr(self, "flow_box", None)
        if flow:
            flow.set_column_spacing(spacing)
            flow.set_row_spacing(spacing)

    def _set_setting(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)
        appearance_keys = {"accent_color", "cover_radius", "grid_spacing",
                           "font_scale", "animations",
                           "show_cover_border", "card_bg"}
        if key in appearance_keys:
            self._apply_appearance()
            self._refresh_current_view()

    def _on_close(self, *args):
        self.win.get_application().quit()
        return False

    def _update_dl_panel(self):
        all_status = self.dl_manager.get_all_status()

        for game_id, status in list(all_status.items()):
            if status["status"] == "needs_browser":
                with self.dl_manager._lock:
                    self.dl_manager.active_downloads.pop(game_id, None)
                w = self.dl_widgets.pop(game_id, None)
                if w:
                    self.dl_list.remove(w)
                name = self._dl_game_names.pop(game_id, game_id)
                url = status.get("url", "")
                GLib.idle_add(self._show_browser_dialog, game_id, name, url)
                continue

            if game_id not in self.dl_widgets:
                name = self._dl_game_names.get(game_id, game_id)
                w = self._make_dl_widget(game_id, name)
                self.dl_widgets[game_id] = w
                self.dl_list.append(w)
            self._update_dl_widget(self.dl_widgets[game_id], status)

        finished = [gid for gid in self.dl_widgets
                    if gid not in all_status or all_status[gid]["status"] in ("complete", "error", "cancelled")]
        for gid in finished:
            status = all_status.get(gid, {})
            w = self.dl_widgets.pop(gid, None)
            if w:
                self.dl_list.remove(w)
            self._dl_game_names.pop(gid, None)
            self._dl_pending_refresh = True

        count = len(self.dl_widgets)
        if count:
            self.dl_badge.set_text(str(count))
            self.dl_badge.set_visible(True)
            self.dl_empty.set_visible(False)
            self.dl_scroll.set_visible(True)
        else:
            self.dl_badge.set_visible(False)
            self.dl_empty.set_visible(True)
            self.dl_scroll.set_visible(False)

        if self._dl_pending_refresh and not self.dl_widgets:
            self._dl_pending_refresh = False
            if self.stack.get_visible_child_name() == "grid":
                GLib.idle_add(self._refresh_current_view)

        return True

    def _show_error_toast(self, game_name, error):
        toast = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toast.add_css_class("toast-err")
        ic = Gtk.Image(icon_name="dialog-error-symbolic")
        ic.set_pixel_size(16)
        toast.append(ic)
        lbl = Gtk.Label(label=f"Error descargando {game_name}: {error[:60]}")
        lbl.set_xalign(0)
        lbl.set_hexpand(True)
        lbl.add_css_class("dim-label")
        toast.append(lbl)
        self.dl_panel.append(toast)
        self.dl_panel.set_visible(True)
        def remove():
            self.dl_panel.remove(toast)
            if not any(self.dl_list):
                self.dl_panel.set_visible(False)
            return False
        GLib.timeout_add(5000, remove)

    def _make_dl_widget(self, game_id, display_name):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        card.add_css_class("dl-card")

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        name_lbl = Gtk.Label(label=display_name)
        name_lbl.set_xalign(0)
        name_lbl.set_hexpand(True)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        name_lbl.add_css_class("dl-card-name")
        top.append(name_lbl)

        pct_lbl = Gtk.Label(label="0%")
        pct_lbl.add_css_class("dl-pct")
        top.append(pct_lbl)
        card.append(top)

        bar = Gtk.ProgressBar()
        bar.set_hexpand(True)
        bar.set_show_text(False)
        bar.add_css_class("dl-bar")
        card.append(bar)

        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        meta_lbl = Gtk.Label(label="")
        meta_lbl.set_xalign(0)
        meta_lbl.set_hexpand(True)
        meta_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        meta_lbl.add_css_class("dl-meta")
        bottom.append(meta_lbl)

        eta_lbl = Gtk.Label(label="")
        eta_lbl.set_xalign(1)
        eta_lbl.add_css_class("dl-eta")
        bottom.append(eta_lbl)

        pause_btn = Gtk.Button()
        pause_btn.set_icon_name("media-playback-pause-symbolic")
        pause_btn.set_has_frame(False)
        pause_btn.add_css_class("dl-iconbtn")
        pause_btn.set_tooltip_text("Pausar")
        pause_btn.connect("clicked", lambda b, gid=game_id: self._toggle_pause(gid))
        bottom.append(pause_btn)

        cancel_btn = Gtk.Button()
        cancel_btn.set_icon_name("window-close-symbolic")
        cancel_btn.set_has_frame(False)
        cancel_btn.add_css_class("dl-iconbtn")
        cancel_btn.set_tooltip_text("Cancelar")
        cancel_btn.connect("clicked", lambda b, gid=game_id: self.dl_manager.cancel(gid))
        bottom.append(cancel_btn)

        card.append(bottom)

        card._bar = bar
        card._meta_lbl = meta_lbl
        card._eta_lbl = eta_lbl
        card._pct_lbl = pct_lbl
        card._name_lbl = name_lbl
        card._pause_btn = pause_btn
        return card

    def _toggle_pause(self, game_id):
        status = self.dl_manager.get_status(game_id) or {}
        if status.get("status") == "paused":
            self.dl_manager.resume(game_id)
        else:
            self.dl_manager.pause(game_id)

    def _update_dl_widget(self, w, status):
        st = status["status"]
        pct = status.get("progress", 0)
        w._bar.set_fraction(pct / 100.0)

        if st == "extracting_link":
            w._pct_lbl.set_text("")
            w._meta_lbl.set_text("Obteniendo enlace...")
            w._eta_lbl.set_text("")
            w._bar.set_pulse_step(0.1)
            w._bar.pulse()
            w._pause_btn.set_sensitive(False)
        elif st in ("downloading", "paused"):
            w._pause_btn.set_sensitive(True)
            w._pct_lbl.set_text(f"{pct}%")
            speed = status.get("speed", 0)
            downloaded = status.get("downloaded", 0)
            total = status.get("total", 0)
            eta = status.get("eta", 0)
            if total > 0:
                dl_s = f"{_fmt_size(downloaded)} / {_fmt_size(total)}"
            else:
                dl_s = _fmt_size(downloaded)
            if st == "paused":
                w._pause_btn.set_icon_name("media-playback-start-symbolic")
                w._pause_btn.set_tooltip_text("Reanudar")
                w._meta_lbl.set_text(f"{dl_s}  \u00b7  En pausa")
                w._eta_lbl.set_text("")
            else:
                w._pause_btn.set_icon_name("media-playback-pause-symbolic")
                w._pause_btn.set_tooltip_text("Pausar")
                speed_s = f"{speed / 1024 / 1024:.1f} MB/s" if speed > 1024 else f"{speed / 1024:.0f} KB/s"
                w._meta_lbl.set_text(f"{dl_s}  \u00b7  {speed_s}")
                if eta > 0 and eta < 86400:
                    w._eta_lbl.set_text(f"\u23f1 quedan {_fmt_eta(eta)}")
                else:
                    w._eta_lbl.set_text("")
        elif st == "extracting":
            w._pct_lbl.set_text("")
            w._meta_lbl.set_text("Extrayendo archivo...")
            w._eta_lbl.set_text("")
            w._pause_btn.set_sensitive(False)
        elif st == "needs_browser":
            w._meta_lbl.set_text("Descarga manual")
            w._eta_lbl.set_text("")
        elif st == "cancelled":
            w._meta_lbl.set_text("Cancelado")
            w._eta_lbl.set_text("")
        elif st == "error":
            w._pct_lbl.set_text("")
            w._meta_lbl.set_text(f"Error: {status.get('error', '?')[:40]}")
            w._eta_lbl.set_text("")

    def start_download(self, game_id, game_name, url):
        self._dl_game_names[game_id] = game_name
        self.dl_manager.download(game_id, game_name, url,
                                 progress_callback=lambda *a: None,
                                 done_callback=self._on_download_done)
        GLib.idle_add(self.dl_popover.popup)

    def _on_download_done(self, gid, gname, path):
        self.dl_manager.mark_installed(gid, gname, path)

    def _show_browser_dialog(self, game_id, game_name, url):
        win = Gtk.Window(title=f"Descargar {game_name}", transient_for=self.win, modal=True)
        win.set_default_size(420, -1)
        win.set_resizable(False)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        win.set_child(vbox)

        icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        icon.set_pixel_size(48)
        icon.set_halign(Gtk.Align.CENTER)
        icon.set_margin_bottom(4)
        vbox.append(icon)

        msg = Gtk.Label(label=f"<b>{game_name}</b>\n\nEste enlace requiere descarga manual desde el navegador.")
        msg.set_use_markup(True)
        msg.set_xalign(0.5)
        msg.set_wrap(True)
        vbox.append(msg)

        vbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        dest_dir = os.path.join(DOWNLOADS_DIR, _sanitize_filename(game_name))
        dir_lbl = Gtk.Label(label=f"Guarda el archivo en:\n<tt>{dest_dir}</tt>")
        dir_lbl.set_use_markup(True)
        dir_lbl.set_xalign(0.5)
        dir_lbl.set_wrap(True)
        vbox.append(dir_lbl)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_row.set_halign(Gtk.Align.CENTER)
        btn_row.set_margin_top(8)

        open_btn = Gtk.Button(label="Abrir página de descarga")
        open_btn.add_css_class("suggested-action")
        open_btn.connect("clicked", lambda b: subprocess.Popen(
            ["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        btn_row.append(open_btn)

        mark_btn = Gtk.Button(label="Marcar como instalado")
        mark_btn.add_css_class("suggested-action")
        def on_mark(b):
            os.makedirs(dest_dir, exist_ok=True)
            self.dl_manager.mark_installed(game_id, game_name, dest_dir)
            win.close()
            GLib.idle_add(self.render_view)
        mark_btn.connect("clicked", on_mark)
        btn_row.append(mark_btn)

        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda b: win.close())
        btn_row.append(cancel_btn)

        vbox.append(btn_row)
        win.present()

    def _open_in_browser(self, url):
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _launch_exe(self, exe_path):
        try:
            subprocess.Popen(
                ["xdg-open", exe_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def _uninstall_game(self, game_id):
        import shutil
        path = self.dl_manager.get_install_path(game_id)
        if path and os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except Exception:
                pass
        self.dl_manager.mark_uninstalled(game_id)
        self.render_view()

    def load_data(self):
        self.catalog = load_catalog()
        self.build_sidebar()
        self.render_view()
        if self.settings.get("auto_fetch_covers") and self.settings.get("sgdb_api_key"):
            threading.Thread(target=self._batch_fetch_covers, args=(self.status_lbl,), daemon=True).start()

    def build_sidebar(self):
        self.build_nav_bar()

    def _show_info(self, title, msg):
        dlg = Gtk.AlertDialog()
        dlg.set_message(title)
        dlg.set_detail(msg)
        dlg.set_modal(True)
        dlg.show(self.win)
        return False

    def _fetch_repo_file(self, filename, timeout=30):
        url = f"{get_repo_raw_base()}/{filename}?nocache={int(time.time())}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "PP-Launcher",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()

    def _auto_update_on_start(self):
        GLib.idle_add(self._set_status, "Buscando actualizaciones...")
        catalog_changed = False
        program_changed = False

        try:
            data = self._fetch_repo_file("catalog.json")
            old = b""
            if os.path.exists(CATALOG_PATH):
                with open(CATALOG_PATH, "rb") as f:
                    old = f.read()
            json.loads(data.decode("utf-8"))
            if data.strip() != old.strip():
                os.makedirs(os.path.dirname(CATALOG_PATH), exist_ok=True)
                tmp = CATALOG_PATH + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, CATALOG_PATH)
                catalog_changed = True
        except Exception:
            pass

        for fn in ("gtk_launcher.py", "download_manager.py"):
            try:
                data = self._fetch_repo_file(fn, timeout=60)
                dest = os.path.join(APP_DIR, fn)
                old = b""
                if os.path.exists(dest):
                    with open(dest, "rb") as f:
                        old = f.read()
                if data and data != old:
                    tmp = dest + ".tmp"
                    with open(tmp, "wb") as f:
                        f.write(data)
                    os.replace(tmp, dest)
                    program_changed = True
            except Exception:
                pass

        GLib.idle_add(self._after_auto_update, catalog_changed, program_changed)

    def _after_auto_update(self, catalog_changed, program_changed):
        if catalog_changed:
            self.load_data()
        if program_changed:
            self._set_status("Actualización del programa lista \u2014 reinicia para aplicarla.")
        elif catalog_changed:
            self._set_status("Lista de juegos actualizada.")
        else:
            self._set_status("")
        return False

    def _set_status(self, text):
        if getattr(self, "status_lbl", None):
            self.status_lbl.set_text(text)
        return False

    def update_game_list(self, widget=None):
        self._show_info("Actualizando lista de juegos...",
                        "Descargando el catálogo desde el repositorio.")
        threading.Thread(target=self._update_game_list_work, daemon=True).start()

    def _update_game_list_work(self):
        try:
            url = f"{get_repo_raw_base()}/catalog.json?nocache={int(time.time())}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "PP-Launcher",
                "Cache-Control": "no-cache, no-store, max-age=0",
                "Pragma": "no-cache"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            os.makedirs(os.path.dirname(CATALOG_PATH), exist_ok=True)
            tmp = CATALOG_PATH + ".tmp"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, CATALOG_PATH)
            GLib.idle_add(self._after_game_list_update, True, "")
        except Exception as e:
            GLib.idle_add(self._after_game_list_update, False, str(e))

    def _after_game_list_update(self, ok, err):
        if ok:
            self.load_data()
            self._show_info("Lista actualizada",
                            "La lista de juegos se actualizó correctamente.")
        else:
            self._show_info("Error al actualizar",
                            f"No se pudo descargar la lista:\n{err}")
        return False

    def update_program(self, widget=None):
        self._show_info("Actualizando programa...",
                        "Descargando la última versión desde el repositorio.")
        threading.Thread(target=self._update_program_work, daemon=True).start()

    def _update_program_work(self):
        try:
            base = get_repo_raw_base()
            files = ["gtk_launcher.py", "download_manager.py",
                     "catalog.json", "README.md"]
            for fn in files:
                url = f"{base}/{fn}"
                req = urllib.request.Request(url, headers={"User-Agent": "PP-Launcher"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = r.read()
                dest = os.path.join(APP_DIR, fn)
                tmp = dest + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, dest)
            GLib.idle_add(self._after_program_update)
        except Exception as e:
            GLib.idle_add(self._show_info, "Error al actualizar el programa",
                          f"No se pudo actualizar:\n{str(e)}")

    def _after_program_update(self):
        self._show_info("Programa actualizado",
                        "Se descargó la última versión. Reinicia el launcher "
                        "para aplicar los cambios del código.")
        return False

    def build_nav_bar(self):
        for child in list(self.nav_bar):
            self.nav_bar.remove(child)
        self.nav_items = []

        btn_store = self._nav_button("Tienda", len(self.catalog))
        btn_store.connect("clicked", lambda b: self._switch_view("tienda"))
        self.nav_bar.append(btn_store)
        self.nav_items.append(("tienda", btn_store))

        self.nav_bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        pref_btn = self._nav_button("Preferencias", None)
        pref_btn.connect("clicked", lambda b: self.show_preferences())
        self.nav_bar.append(pref_btn)

        self.nav_bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        zoom_box.add_css_class("zoom-box")
        zout = Gtk.Button(label="\u2212")
        zout.add_css_class("nav-tab")
        zout.set_has_frame(False)
        zout.set_tooltip_text("Reducir tamaño")
        zout.connect("clicked", lambda b: self._change_zoom(0.85))
        zoom_box.append(zout)
        self.zoom_lbl = Gtk.Label(label=f"{int(self.zoom * 100)}%")
        self.zoom_lbl.add_css_class("dim-label")
        self.zoom_lbl.set_xalign(0.5)
        self.zoom_lbl.set_size_request(44, -1)
        zoom_box.append(self.zoom_lbl)
        zin = Gtk.Button(label="\u002b")
        zin.add_css_class("nav-tab")
        zin.set_has_frame(False)
        zin.set_tooltip_text("Aumentar tamaño")
        zin.connect("clicked", lambda b: self._change_zoom(1.0 / 0.85))
        zoom_box.append(zin)
        self.nav_bar.append(zoom_box)

        self._update_nav_active()

    def _change_zoom(self, factor):
        self.zoom = max(0.5, min(2.0, self.zoom * factor))
        self.zoom_lbl.set_text(f"{int(self.zoom * 100)}%")
        self.settings["zoom"] = self.zoom
        save_settings(self.settings)
        self._refresh_current_view()

    def _nav_button(self, label, count=None):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl = Gtk.Label(label=label)
        lbl.set_xalign(0)
        hbox.append(lbl)
        if count is not None:
            cnt = Gtk.Label(label=str(count))
            cnt.add_css_class("dim-label")
            cnt.add_css_class("info-pill")
            hbox.append(cnt)
        btn = Gtk.Button(child=hbox)
        btn.set_has_frame(False)
        btn.add_css_class("nav-tab")
        return btn

    def _switch_view(self, view):
        self.current_view = view
        self.search_entry.set_text("")
        self._update_nav_active()
        self.render_view()

    def _update_nav_active(self):
        for name, btn in self.nav_items:
            btn.remove_css_class("nav-tab-active")
            if name == self.current_view:
                btn.add_css_class("nav-tab-active")

    def on_search_changed(self, entry):
        self.search_term = entry.get_text().strip().lower()
        self.render_view()

    def render_view(self):
        self.stack.set_visible_child_name("grid")
        self._refresh_current_view()

    def _refresh_current_view(self):
        for child in list(self.flow_box):
            self.flow_box.remove(child)
        self._render_store()

    def _sorted_items(self, items):
        order = self.settings.get("sort_order", "name")
        if order == "category":
            return sorted(items, key=lambda i: (i.get("category", ""), i.get("name", "").lower()))
        if order == "random":
            import random
            lst = list(items)
            random.shuffle(lst)
            return lst
        return sorted(items, key=lambda i: i.get("name", "").lower())

    def _render_store(self):
        items = self._sorted_items(self.catalog)

        if self.search_term:
            items = [i for i in items if self.search_term in i.get("name", "").lower()
                     or self.search_term in i.get("description", "").lower()]

        if not items:
            empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            empty.add_css_class("empty-state")
            empty.set_valign(Gtk.Align.CENTER)
            empty.set_halign(Gtk.Align.CENTER)
            empty.set_margin_top(60)
            ic = Gtk.Image.new_from_icon_name("edit-find-symbolic")
            ic.set_pixel_size(56)
            ic.add_css_class("empty-icon")
            empty.append(ic)
            t = Gtk.Label(label="Sin resultados")
            t.add_css_class("title-3")
            empty.append(t)
            d = Gtk.Label(label="Intenta con otro término")
            d.add_css_class("dim-label")
            empty.append(d)
            self.flow_box.append(empty)
            self.status_lbl.set_text("0 juegos")
            return

        for item in items:
            self.flow_box.append(self._make_game_card(
                item,
                int(self.store_w * self.zoom), int(self.store_h * self.zoom)))

        self.status_lbl.set_text(f"{len(items)} juegos")
        self._update_grid_columns()

    def _update_grid_columns(self):
        fb = getattr(self, "flow_box", None)
        if not fb:
            return
        avail = int(self.grid_scroll.get_hadjustment().get_page_size())
        if avail <= 1:
            avail = self.grid_scroll.get_width()
        if avail <= 1:
            return
        spacing = int(self.settings.get("grid_spacing", 12))
        card_w = int(self.store_w * self.zoom)
        usable = avail - 24
        cols = max(1, int((usable + spacing) / (card_w + spacing)))
        fb.set_min_children_per_line(cols)
        fb.set_max_children_per_line(cols)

    def _make_game_card(self, item, cover_w=160, cover_h=240):
        c1, c2, emoji = get_cover(item.get("name", ""))

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.add_css_class("game-cell")
        card.set_size_request(cover_w, -1)
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.START)
        card.set_hexpand(False)

        cover_overlay = Gtk.Overlay()
        cover_overlay.set_size_request(cover_w, cover_h)
        cover_overlay.set_halign(Gtk.Align.CENTER)
        cover_overlay.set_valign(Gtk.Align.START)
        cover_overlay.set_overflow(Gtk.Overflow.HIDDEN)
        cover_overlay.add_css_class("cover-box")

        cover_path = get_cached_cover(item.get("name", ""))
        pb = load_scaled_pixbuf(cover_path, cover_w, cover_h) if cover_path else None
        if pb:
            visual = Gtk.Picture()
            visual.set_pixbuf(pb)
            visual.set_content_fit(Gtk.ContentFit.COVER)
            visual.set_can_shrink(True)
            visual.set_halign(Gtk.Align.FILL)
            visual.set_valign(Gtk.Align.FILL)
            visual.set_size_request(cover_w, cover_h)
        else:
            visual = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            visual.set_size_request(cover_w, cover_h)
            visual.add_css_class(make_color_css(c1))
            emoji_lbl = Gtk.Label(label=emoji)
            emoji_lbl.set_markup(f'<span size="xx-large">{emoji}</span>')
            emoji_lbl.set_valign(Gtk.Align.CENTER)
            emoji_lbl.set_halign(Gtk.Align.CENTER)
            visual.append(emoji_lbl)
        cover_overlay.set_child(visual)

        installed = item.get("id") and self.dl_manager.is_installed(item.get("id"))
        if installed:
            badge = Gtk.Label(label="INSTALADO")
            badge.add_css_class("badge-installed")
            badge.set_halign(Gtk.Align.END)
            badge.set_valign(Gtk.Align.START)
            badge.set_margin_top(8)
            badge.set_margin_end(8)
            cover_overlay.add_overlay(badge)

        foot = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        foot.set_halign(Gtk.Align.FILL)
        foot.set_valign(Gtk.Align.END)
        foot.add_css_class("game-foot")
        foot.set_margin_start(10)
        foot.set_margin_end(10)
        foot.set_margin_bottom(10)

        if self.settings.get("show_title", True):
            name_lbl = Gtk.Label(label=item.get("name", ""))
            name_lbl.set_xalign(0)
            name_lbl.set_wrap(True)
            name_lbl.set_lines(2)
            name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            name_lbl.add_css_class("game-foot-title")
            foot.append(name_lbl)

        if self.settings.get("show_category", True):
            sub = item.get("subcategory", item.get("category", ""))
            cat = item.get("category", "")
            sub_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            sub_chip = Gtk.Label(label=sub)
            sub_chip.add_css_class("chip")
            sub_chip.add_css_class("chip-inv")
            sub_row.append(sub_chip)
            if cat and cat != sub:
                cat_lbl = Gtk.Label(label=cat)
                cat_lbl.set_xalign(0)
                cat_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                cat_lbl.add_css_class("game-foot-sub")
                sub_row.append(cat_lbl)
            foot.append(sub_row)

        cover_overlay.add_overlay(foot)

        action_overlay = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        action_overlay.set_halign(Gtk.Align.END)
        action_overlay.set_valign(Gtk.Align.END)
        action_overlay.add_css_class("game-overlay")
        play_btn = Gtk.Button(icon_name="media-playback-start-symbolic")
        play_btn.add_css_class("game-play")
        play_btn.set_has_frame(False)
        play_btn.set_halign(Gtk.Align.END)
        play_btn.set_valign(Gtk.Align.END)
        play_btn.set_margin_end(10)
        play_btn.set_margin_bottom(10)
        play_btn.set_tooltip_text("Ver detalles")
        play_btn.connect("clicked", lambda b: self.show_detail(item))
        action_overlay.append(play_btn)
        cover_overlay.add_overlay(action_overlay)

        card.append(cover_overlay)

        def on_open(*a):
            self.show_detail(item)

        card_event = Gtk.GestureClick()
        card_event.connect("released", lambda g, n, x, y: on_open())
        card.add_controller(card_event)
        return card

    def show_detail(self, item):
        self.stack.set_visible_child_name("detail")
        for child in list(self.detail_box):
            self.detail_box.remove(child)

        c1, c2, emoji = get_cover(item.get("name", ""))

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        nav_box.set_margin_start(12)
        nav_box.set_margin_top(8)
        nav_box.set_margin_bottom(4)
        back_btn = Gtk.Button(icon_name="go-previous-symbolic")
        back_btn.set_has_frame(False)
        back_btn.connect("clicked", lambda b: self.render_view())
        nav_box.append(back_btn)

        back_lbl = Gtk.Label(label="Volver")
        back_lbl.add_css_class("dim-label")
        nav_box.append(back_lbl)
        self.detail_box.append(nav_box)

        top_row = Gtk.Overlay()
        top_row.add_css_class("hero")
        top_row.set_margin_start(14)
        top_row.set_margin_end(14)
        top_row.set_margin_top(12)
        top_row.set_margin_bottom(14)
        self.detail_box.append(top_row)

        cover_path = get_cached_cover(item.get("name", ""))
        pb = load_scaled_pixbuf(cover_path, 170, 255) if cover_path else None
        if pb:
            bg = Gtk.Picture()
            bg.set_pixbuf(pb)
            bg.set_content_fit(Gtk.ContentFit.COVER)
            bg.set_can_shrink(True)
            bg.add_css_class("hero-bg")
            top_row.set_child(bg)
            scrim = Gtk.Box()
            scrim.set_halign(Gtk.Align.FILL)
            scrim.set_valign(Gtk.Align.FILL)
            scrim.add_css_class("hero-scrim")
            top_row.add_overlay(scrim)

        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        inner.set_halign(Gtk.Align.FILL)
        inner.set_valign(Gtk.Align.FILL)
        inner.set_margin_start(20)
        inner.set_margin_end(20)
        inner.set_margin_top(18)
        inner.set_margin_bottom(18)
        top_row.add_overlay(inner)

        if pb:
            picture = Gtk.Picture()
            picture.set_pixbuf(pb)
            picture.set_size_request(170, 255)
            picture.set_content_fit(Gtk.ContentFit.COVER)
            picture.set_can_shrink(True)
            picture.set_valign(Gtk.Align.START)
            picture.set_halign(Gtk.Align.START)
            picture.add_css_class("detail-cover")
            inner.append(picture)
        else:
            css_name = make_color_css(c1)
            cover = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            cover.set_size_request(170, 255)
            cover.set_valign(Gtk.Align.START)
            cover.set_halign(Gtk.Align.START)
            cover.add_css_class(css_name)
            cover.add_css_class("detail-cover")
            emoji_lbl = Gtk.Label(label=emoji)
            emoji_lbl.set_markup(f'<span size="xx-large">{emoji}</span>')
            emoji_lbl.set_valign(Gtk.Align.CENTER)
            emoji_lbl.set_halign(Gtk.Align.CENTER)
            cover.append(emoji_lbl)
            inner.append(cover)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        info_box.set_vexpand(True)
        info_box.set_hexpand(True)
        inner.append(info_box)

        title = Gtk.Label(label=item.get("name", ""))
        title.set_xalign(0)
        title.add_css_class("detail-title")
        info_box.append(title)

        meta_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cat_chip = Gtk.Label(label=item.get("category", ""))
        cat_chip.add_css_class("chip")
        meta_row.append(cat_chip)
        sub = item.get("subcategory", "")
        if sub and sub != item.get("category", ""):
            sub_chip = Gtk.Label(label=sub)
            sub_chip.add_css_class("chip")
            sub_chip.add_css_class("accent")
            meta_row.append(sub_chip)
        info_box.append(meta_row)

        actions = Gtk.FlowBox()
        actions.set_selection_mode(Gtk.SelectionMode.NONE)
        actions.set_max_children_per_line(6)
        actions.set_column_spacing(8)
        actions.set_row_spacing(8)
        actions.set_homogeneous(False)
        info_box.append(actions)

        def add_action(w):
            if isinstance(w, Gtk.Button):
                w.add_css_class("detail-action")
            actions.append(w)

        if item.get("url"):
            url = item["url"]
            game_id = item.get("id", "")
            dl_status = self.dl_manager.get_status(game_id) if game_id else None
            installed = self.dl_manager.is_installed(game_id) if game_id else False

            if installed:
                play_btn = Gtk.Button(label="\u25b6  Jugar")
                play_btn.add_css_class("suggested-action")
                install_path = self.dl_manager.get_install_path(game_id)
                if install_path:
                    exe = find_exe_in_dir(install_path) if os.path.isdir(install_path) else None
                    target = exe or install_path
                    play_btn.connect("clicked", lambda b, t=target: (
                        self._launch_exe(t) if os.path.isfile(t) else subprocess.Popen(
                            ["xdg-open", t], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
                add_action(play_btn)

                del_btn = Gtk.Button(label="  Desinstalar")
                del_btn.add_css_class("destructive-action")
                del_btn.connect("clicked", lambda b, gid=game_id: self._uninstall_game(gid))
                add_action(del_btn)

            elif dl_status and dl_status["status"] in ("downloading", "extracting", "extracting_link"):
                prog_bar = Gtk.ProgressBar()
                prog_bar.set_fraction(dl_status.get("progress", 0) / 100.0)
                prog_bar.set_show_text(True)
                prog_bar.add_css_class("dl-bar")
                prog_bar.set_size_request(200, -1)
                add_action(prog_bar)
                dl_info = Gtk.Label(label="Descargando...")
                dl_info.set_xalign(0)
                dl_info.add_css_class("dim-label")
                add_action(dl_info)

                cancel_btn = Gtk.Button(label="Cancelar descarga")
                cancel_btn.add_css_class("destructive-action")
                cancel_btn.connect("clicked", lambda b, gid=game_id: self.dl_manager.cancel(gid))
                add_action(cancel_btn)

            elif dl_status and dl_status["status"] == "needs_browser":
                warn_lbl = Gtk.Label(label="Se necesita descargar manualmente desde el navegador.")
                warn_lbl.set_xalign(0)
                warn_lbl.set_wrap(True)
                warn_lbl.add_css_class("dim-label")
                add_action(warn_lbl)

                dl_btn = Gtk.Button(label="  Descargar desde navegador")
                dl_btn.add_css_class("suggested-action")
                dl_btn.connect("clicked", lambda b, it=item: self.start_download(
                    it.get("id", ""), it.get("name", ""), it.get("url", "")))
                add_action(dl_btn)

            else:
                dl_btn = Gtk.Button(label="  Descargar")
                dl_btn.add_css_class("suggested-action")
                dl_btn.connect("clicked", lambda b, it=item: self.start_download(
                    it.get("id", ""), it.get("name", ""), it.get("url", "")))
                add_action(dl_btn)

        if item.get("command"):
            cmd = item["command"]
            cmd_short = cmd[:60] + "..." if len(cmd) > 60 else cmd
            exec_btn = Gtk.Button(label="\u25b6  Ejecutar")
            exec_btn.add_css_class("suggested-action")
            exec_btn.connect("clicked", lambda b, c=cmd: self.run_command(c))
            add_action(exec_btn)
            cmd_lbl = Gtk.Label(label=f"Comando: {cmd_short}")
            cmd_lbl.set_xalign(0)
            cmd_lbl.set_selectable(True)
            cmd_lbl.add_css_class("dim-label")
            add_action(cmd_lbl)

        if not item.get("url") and not item.get("command"):
            no_act = Gtk.Label(label="Sin acciones disponibles")
            no_act.set_xalign(0)
            no_act.add_css_class("dim-label")
            add_action(no_act)

        game_name = item.get("name", "")
        cover_btn = Gtk.Button(label="  Elegir carátula")
        cover_btn.add_css_class("suggested-action")
        cover_btn.connect("clicked", lambda b, it=item: self.show_cover_picker(it))
        add_action(cover_btn)

        yt_btn = Gtk.Button(label="  Ver gameplay en YouTube")
        yt_btn.add_css_class("suggested-action")
        yt_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(game_name + ' gameplay')}"
        yt_btn.connect("clicked", lambda b, u=yt_url: subprocess.Popen(
            ["xdg-open", u], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        add_action(yt_btn)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_bottom(20)
        self.detail_box.append(content)

        def section_title(text):
            lbl = Gtk.Label(label=text)
            lbl.set_xalign(0)
            lbl.add_css_class("section-title")
            return lbl

        content.append(section_title("Descripción"))
        desc = Gtk.Label(label=item.get("description", "Sin descripción"))
        desc.set_xalign(0)
        desc.set_wrap(True)
        desc.set_selectable(True)
        desc.add_css_class("desc")
        content.append(desc)

        tags = item.get("tags", [])
        if tags:
            content.append(section_title("Etiquetas"))
            tags_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            for t in tags:
                chip = Gtk.Label(label=t.upper())
                chip.add_css_class("chip")
                tags_box.append(chip)
            content.append(tags_box)

        info_rows = []
        if item.get("url"):
            info_rows = [("Enlace", item.get("url", ""))]
        if info_rows:
            content.append(section_title("Información"))
            info_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            info_card.add_css_class("detail-card")
            for k, v in info_rows:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                key = Gtk.Label(label=k)
                key.set_xalign(0)
                key.set_size_request(90, -1)
                key.add_css_class("kv-key")
                row.append(key)
                val = Gtk.Label(label=v)
                val.set_xalign(0)
                val.set_hexpand(True)
                val.set_selectable(True)
                val.set_ellipsize(Pango.EllipsizeMode.END)
                val.add_css_class("kv")
                row.append(val)
                info_card.append(row)
            content.append(info_card)

    def show_cover_picker(self, item):
        api_key = self.settings.get("sgdb_api_key", "")
        if not api_key:
            alert = Gtk.AlertDialog(
                message="Necesitas una API Key de SteamGridDB en Preferencias para elegir carátulas.")
            alert.show(self.win)
            return

        game_name = item.get("name", "")

        win = Gtk.Window(title="Elegir carátula", transient_for=self.win, modal=True)
        win.set_default_size(720, 560)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        win.set_child(vbox)

        # --- Buscador + selector de juego ---
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        entry = Gtk.Entry()
        entry.set_text(game_name)
        entry.set_hexpand(True)
        entry.set_placeholder_text("Buscar juego en SteamGridDB...")
        top.append(entry)
        search_btn = Gtk.Button(label="Buscar")
        top.append(search_btn)
        vbox.append(top)

        game_combo = Gtk.DropDown()
        game_combo.set_hexpand(True)
        vbox.append(game_combo)

        status = Gtk.Label(label="")
        status.set_xalign(0)
        status.add_css_class("dim-label")
        vbox.append(status)

        # --- Cuadrícula de carátulas ---
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        flow.set_column_spacing(8)
        flow.set_row_spacing(8)
        flow.set_max_children_per_line(4)
        flow.set_homogeneous(True)
        flow.set_margin_top(4)
        flow.set_margin_bottom(4)
        scroll.set_child(flow)
        vbox.append(scroll)

        # --- Botones ---
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bottom.set_halign(Gtk.Align.END)
        reset_btn = Gtk.Button(label="Restaurar (gradiente)")
        reset_btn.connect("clicked", lambda b: self._reset_cover(game_name, win, item))
        bottom.append(reset_btn)
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda b: win.close())
        bottom.append(cancel_btn)
        use_btn = Gtk.Button(label="Usar esta carátula")
        use_btn.add_css_class("suggested-action")
        bottom.append(use_btn)
        vbox.append(bottom)

        picker_game_ids = []

        def clear_flow():
            for child in list(flow):
                flow.remove(child)

        def show_message(text):
            clear_flow()
            lbl = Gtk.Label(label=text)
            lbl.set_valign(Gtk.Align.CENTER)
            lbl.set_halign(Gtk.Align.CENTER)
            lbl.set_vexpand(True)
            lbl.add_css_class("dim-label")
            flow.append(lbl)

        def add_thumb(grid):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_size_request(150, 225)
            box.set_overflow(Gtk.Overflow.HIDDEN)
            pic = Gtk.Picture()
            pic.set_content_fit(Gtk.ContentFit.COVER)
            pic.set_size_request(150, 225)
            pic.set_hexpand(False)
            pic.set_vexpand(False)
            box.append(pic)
            box._grid = grid
            flow.append(box)

            thumb = grid.get("thumb") or grid.get("url")
            if not thumb:
                return

            def do_load():
                try:
                    req = urllib.request.Request(thumb, headers={
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                        "Referer": "https://www.steamgriddb.com/"
                    })
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        raw = resp.read()
                    loader = GdkPixbuf.PixbufLoader()
                    loader.write(raw)
                    loader.close()
                    pb = loader.get_pixbuf()
                    if pb:
                        # Escalar a un tamaño fijo para que el FlowBox
                        # (homogeneous) no se redimensione al ir cargando.
                        w, h = pb.get_width(), pb.get_height()
                        tw, th = 150, 225
                        scale = min(tw / w, th / h) if (w and h) else 1
                        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                        pb = pb.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
                        def set_img():
                            pic.set_pixbuf(pb)
                            return False
                        GLib.idle_add(set_img)
                except Exception:
                    pass

            threading.Thread(target=do_load, daemon=True).start()

        def load_covers_for(game_id):
            clear_flow()
            status.set_text("Cargando carátulas...")
            def do_load():
                grids = fetch_sgdb_grids(game_id, api_key)
                def populate():
                    if not grids:
                        show_message("No se encontraron carátulas para este juego.")
                        status.set_text("")
                        return
                    for g in grids:
                        add_thumb(g)
                    status.set_text(f"{len(grids)} carátulas encontradas")
                GLib.idle_add(populate)
            threading.Thread(target=do_load, daemon=True).start()

        def populate_games(results):
            picker_game_ids.clear()
            names = []
            for r in results:
                picker_game_ids.append(r["id"])
                names.append(r["name"])
            if not names:
                game_combo.set_model(Gtk.StringList.new(["(sin resultados)"]))
                game_combo.set_sensitive(False)
                clear_flow()
                show_message("Sin resultados. Prueba otro término.")
                status.set_text("")
                return
            game_combo.set_model(Gtk.StringList.new(names))
            game_combo.set_sensitive(True)
            game_combo.set_selected(0)
            load_covers_for(results[0]["id"])

        def on_game_changed(combo, *a):
            idx = combo.get_selected()
            if 0 <= idx < len(picker_game_ids):
                load_covers_for(picker_game_ids[idx])

        game_combo.connect("notify::selected", on_game_changed)

        def do_search(term):
            status.set_text("Buscando...")
            def run():
                results = search_sgdb_results(term, api_key)
                GLib.idle_add(populate_games, results)
            threading.Thread(target=run, daemon=True).start()

        search_btn.connect("clicked", lambda b: do_search(entry.get_text().strip()))
        entry.connect("activate", lambda e: do_search(entry.get_text().strip()))

        def on_use(b):
            sel = flow.get_selected_children()
            if not sel:
                return
            grid = sel[0].get_child()._grid
            url = grid.get("url") or grid.get("thumb")
            if not url:
                return
            status.set_text("Guardando carátula...")
            def run():
                path = save_cover_from_url(game_name, url, api_key)
                def done():
                    if path:
                        self.show_detail(item)
                    win.close()
                GLib.idle_add(done)
            threading.Thread(target=run, daemon=True).start()

        use_btn.connect("clicked", on_use)

        # Búsqueda inicial
        do_search(game_name)

        win.present()

    def _reset_cover(self, game_name, picker_win, item):
        path = os.path.join(COVERS_DIR, _safe_cover_name(game_name) + ".jpg")
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass
        picker_win.close()
        self.show_detail(item)

    def run_command(self, cmd):
        term = find_terminal()
        full = f'{cmd}; echo; read -p "Presiona Enter para cerrar..."'
        try:
            if term:
                subprocess.Popen([term, "-e", f"bash -c {shlex.quote(full)}"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["bash", "-c", cmd],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _batch_fetch_covers(self, status_lbl=None):
        api_key = self.settings.get("sgdb_api_key", "")
        if not api_key:
            return

        all_names = [i.get("name", "") for i in self.catalog]
        to_fetch = [n for n in all_names if n and not get_cached_cover(n)]

        if not to_fetch:
            if status_lbl:
                GLib.idle_add(status_lbl.set_text, "Todas las carátulas ya están descargadas")
            return

        total = len(to_fetch)

        def do_batch():
            count = 0
            for name in to_fetch:
                count += 1
                if status_lbl:
                    GLib.idle_add(status_lbl.set_text, f"Descargando carátulas... {count}/{total}")
                download_cover(name, api_key)
                time.sleep(0.1)
            # Reintentar las que fallaron (errores transitorios / limite de SGDB)
            missing = [n for n in to_fetch if not get_cached_cover(n)]
            for _ in range(2):
                if not missing:
                    break
                retry = []
                for name in missing:
                    download_cover(name, api_key)
                    time.sleep(0.2)
                    if not get_cached_cover(name):
                        retry.append(name)
                missing = retry
            ok = sum(1 for n in to_fetch if get_cached_cover(n))
            if status_lbl:
                GLib.idle_add(status_lbl.set_text, f"Carátulas: {ok}/{total}")
            GLib.idle_add(self.render_view)

        threading.Thread(target=do_batch, daemon=True).start()

    def _show_about(self):
        win = Gtk.Window(title="Acerca de", transient_for=self.win, modal=True)
        win.set_default_size(380, 320)
        win.set_resizable(False)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        win.set_child(vbox)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("about-box")
        card.set_halign(Gtk.Align.FILL)

        logo = Gtk.Label(label="\U0001F3AE")
        logo.add_css_class("about-logo")
        logo.set_xalign(0.5)
        card.append(logo)

        title = Gtk.Label(label="PP Launcher")
        title.add_css_class("about-title")
        title.set_xalign(0.5)
        card.append(title)

        sub = Gtk.Label(label="v8.1  ·  Lanzador de juegos estilo Lutris")
        sub.add_css_class("about-sub")
        sub.set_xalign(0.5)
        card.append(sub)

        link = Gtk.Label()
        link.set_markup('<a href="https://github.com/a101mdtbb/pp">github.com/a101mdtbb/pp</a>')
        link.set_xalign(0.5)
        card.append(link)

        vbox.append(card)

        close_btn = Gtk.Button(label="Cerrar")
        close_btn.add_css_class("suggested-action")
        close_btn.set_halign(Gtk.Align.CENTER)
        close_btn.set_margin_top(14)
        close_btn.set_size_request(160, -1)
        close_btn.connect("clicked", lambda b: win.close())
        vbox.append(close_btn)

        win.present()

    def show_preferences(self):
        win = Gtk.Window(title="Preferencias \u2014 PP Launcher", transient_for=self.win, modal=True)
        win.set_default_size(750, 520)

        snapshot = dict(self.settings)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        win.set_child(root)

        main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        main_hbox.set_vexpand(True)
        root.append(main_hbox)

        nav = Gtk.StackSidebar()
        nav.set_size_request(180, -1)
        nav.add_css_class("sidebar")

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        nav.set_stack(stack)
        main_hbox.append(nav)
        main_hbox.append(stack)

        self._build_interface_page(stack, win)
        self._build_appearance_page(stack)
        self._build_system_page(stack)

        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_bar.add_css_class("toolbar")
        action_bar.set_margin_start(18)
        action_bar.set_margin_end(18)
        action_bar.set_margin_top(10)
        action_bar.set_margin_bottom(12)

        action_spacer = Gtk.Box()
        action_spacer.set_hexpand(True)
        action_bar.append(action_spacer)

        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.set_size_request(120, -1)

        def on_cancel(_b):
            self.settings.clear()
            self.settings.update(snapshot)
            save_settings(self.settings)
            self._apply_appearance()
            self._apply_theme()
            self._refresh_current_view()
            win.close()

        cancel_btn.connect("clicked", on_cancel)
        action_bar.append(cancel_btn)

        save_btn = Gtk.Button(label="Guardar y cerrar")
        save_btn.add_css_class("suggested-action")
        save_btn.set_size_request(150, -1)
        save_btn.connect("clicked", lambda b: (save_settings(self.settings), win.close()))
        action_bar.append(save_btn)

        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        root.append(action_bar)

        win.present()

    def _pref_group(self, title, *widgets):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        t = Gtk.Label(label=title)
        t.add_css_class("pref-group-title")
        outer.append(t)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        card.add_css_class("pref-group")
        for w in widgets:
            if isinstance(w, Gtk.Widget):
                w.add_css_class("pref-row")
                card.append(w)
        outer.append(card)
        return outer

    def _build_interface_page(self, stack, pref_win):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_start(18)
        page.set_margin_end(18)
        page.set_margin_top(12)
        page.set_margin_bottom(12)

        lbl = Gtk.Label(label="Interfaz")
        lbl.set_xalign(0)
        lbl.add_css_class("title-2")
        page.append(lbl)

        minimize_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        minimize_lbl = Gtk.Label(label="Minimizar al lanzar un juego")
        minimize_lbl.set_hexpand(True)
        minimize_lbl.set_xalign(0)
        minimize_row.append(minimize_lbl)
        minimize_sw = Gtk.Switch()
        minimize_sw.set_active(self.settings.get("minimize_on_launch", True))
        minimize_sw.connect("notify::active", lambda s, p: self._set_setting("minimize_on_launch", s.get_active()))
        minimize_row.append(minimize_sw)

        badge_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        badge_lbl = Gtk.Label(label="Mostrar insignias en tarjetas")
        badge_lbl.set_hexpand(True)
        badge_lbl.set_xalign(0)
        badge_row.append(badge_lbl)
        badge_sw = Gtk.Switch()
        badge_sw.set_active(self.settings.get("show_badges", True))
        badge_sw.connect("notify::active", lambda s, p: self._set_setting("show_badges", s.get_active()))
        badge_row.append(badge_sw)

        page.append(self._pref_group("Comportamiento", minimize_row, badge_row))

        theme_lbl = Gtk.Label(label="Tema GTK")
        theme_lbl.set_xalign(0)
        theme_lbl.add_css_class("caption")
        theme_lbl.add_css_class("dim-label")

        available_themes = detect_gtk_themes()
        theme_combo = Gtk.DropDown()
        theme_combo.set_model(Gtk.StringList.new(available_themes))
        current_gtk = self.settings.get("gtk_theme", "Adwaita")
        if current_gtk in available_themes:
            theme_combo.set_selected(available_themes.index(current_gtk))

        theme_info = Gtk.Label(label="Actual: " + current_gtk)
        theme_info.set_xalign(0)
        theme_info.add_css_class("dim-label")

        def on_theme_change(combo, *args):
            idx = combo.get_selected()
            if idx < len(available_themes):
                name = available_themes[idx]
                self._set_setting("gtk_theme", name)
                self._apply_theme()
                theme_info.set_text("Actual: " + name)

        theme_combo.connect("notify::selected", on_theme_change)
        page.append(self._pref_group("Tema GTK", theme_lbl, theme_combo, theme_info))

        sgdb_lbl = Gtk.Label(label="SteamGridDB - Carátulas")
        sgdb_lbl.set_xalign(0)
        sgdb_lbl.add_css_class("title-2")

        key_lbl = Gtk.Label(label="API Key (steamgriddb.com/profile/preferences/api)")
        key_lbl.set_xalign(0)
        key_lbl.add_css_class("caption")
        key_lbl.add_css_class("dim-label")

        key_entry = Gtk.Entry()
        key_entry.set_text(self.settings.get("sgdb_api_key", ""))
        key_entry.set_visibility(False)
        key_entry.set_hexpand(True)
        key_entry.set_placeholder_text("Tu API key de SteamGridDB")
        key_entry.connect("changed", lambda e: self._set_setting("sgdb_api_key", e.get_text()))

        auto_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        auto_lbl = Gtk.Label(label="Descargar carátulas automáticamente")
        auto_lbl.set_hexpand(True)
        auto_lbl.set_xalign(0)
        auto_row.append(auto_lbl)
        auto_sw = Gtk.Switch()
        auto_sw.set_active(self.settings.get("auto_fetch_covers", True))
        auto_sw.connect("notify::active", lambda s, p: self._set_setting("auto_fetch_covers", s.get_active()))
        auto_row.append(auto_sw)

        page.append(self._pref_group("Carátulas", sgdb_lbl, key_lbl, key_entry, auto_row))

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        page.append(spacer)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(page)
        stack.add_titled(scroll, "interface", "Interfaz")

    def _ap_switch_row(self, label, key):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl = Gtk.Label(label=label)
        lbl.set_hexpand(True)
        lbl.set_xalign(0)
        row.append(lbl)
        sw = Gtk.Switch()
        sw.set_active(self.settings.get(key, True))
        sw.connect("notify::active", lambda s, p: self._set_setting(key, s.get_active()))
        row.append(sw)
        return row

    def _ap_slider_row(self, label, key, lo, hi, step, fmt):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl = Gtk.Label(label=label)
        lbl.set_hexpand(True)
        lbl.set_xalign(0)
        head.append(lbl)
        val_lbl = Gtk.Label()
        val_lbl.set_xalign(1)
        val_lbl.add_css_class("dim-label")
        head.append(val_lbl)
        box.append(head)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, step)
        scale.set_value(float(self.settings.get(key, lo)))
        scale.set_draw_value(False)
        scale.set_hexpand(True)

        def on_change(s):
            v = s.get_value()
            self._set_setting(key, v)
            val_lbl.set_text(fmt(v))

        scale.connect("value-changed", on_change)
        val_lbl.set_text(fmt(scale.get_value()))
        box.append(scale)
        return box

    def _ap_choice_row(self, label, key, options):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl = Gtk.Label(label=label)
        lbl.set_xalign(0)
        lbl.add_css_class("caption")
        lbl.add_css_class("dim-label")
        box.append(lbl)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cur = self.settings.get(key, options[0][1])
        first = None
        for text, val in options:
            btn = Gtk.ToggleButton(label=text)
            if first is None:
                first = btn
            else:
                btn.set_group(first)
            if cur == val:
                btn.set_active(True)
            btn.connect("toggled", lambda b, v=val: self._set_setting(key, v))
            row.append(btn)
        box.append(row)
        return box

    def _build_appearance_page(self, stack):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_start(18)
        page.set_margin_end(18)
        page.set_margin_top(12)
        page.set_margin_bottom(12)

        title = Gtk.Label(label="Apariencia")
        title.set_xalign(0)
        title.add_css_class("title-2")
        page.append(title)

        from colorsys import hls_to_rgb

        def hue_to_accent(hue):
            r, g, b = hls_to_rgb(hue / 360.0, 0.5, 0.62)
            return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

        accent_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        ahead = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        albl = Gtk.Label(label="Color de acento")
        albl.set_hexpand(True)
        albl.set_xalign(0)
        ahead.append(albl)
        asw = Gtk.ColorDialogButton()
        cd = Gtk.ColorDialog()
        asw.set_dialog(cd)
        def hex_to_rgba(h):
            h = h.lstrip("#")
            return Gdk.RGBA(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255,
                            int(h[4:6], 16) / 255, 1)
        asw.set_rgba(hex_to_rgba(self.settings.get("accent_color", "#3584e4")))

        def on_accent(btn):
            rgba = btn.get_rgba()
            hexv = "#%02x%02x%02x" % (int(rgba.red * 255), int(rgba.green * 255),
                                      int(rgba.blue * 255))
            self._set_setting("accent_color", hexv)
        asw.connect("notify::rgba", on_accent)
        ahead.append(asw)
        accent_box.append(ahead)

        page.append(self._pref_group("Color", accent_box,
            self._ap_slider_row("Radio de las carátulas", "cover_radius", 0, 24, 1,
                                lambda v: f"{int(v)} px"),
            self._ap_slider_row("Espaciado de la cuadrícula", "grid_spacing", 0, 28, 1,
                                lambda v: f"{int(v)} px"),
            self._ap_slider_row("Tamaño de fuente", "font_scale", 0.8, 1.5, 0.05,
                                lambda v: f"{int(v * 100)}%")))

        page.append(self._pref_group("Visibilidad",
            self._ap_switch_row("Mostrar nombre del juego", "show_title"),
            self._ap_switch_row("Mostrar categoría", "show_category"),
            self._ap_switch_row("Mostrar borde en carátulas", "show_cover_border"),
            self._ap_switch_row("Animaciones", "animations")))

        page.append(self._pref_group("Orden",
            self._ap_choice_row("Ordenar juegos por", "sort_order",
                [("Nombre", "name"), ("Categoría", "category"), ("Aleatorio", "random")])))

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        page.append(spacer)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(page)
        stack.add_titled(scroll, "appearance", "Apariencia")

    def _set_setting_silent(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)

    def _build_system_page(self, stack):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_start(18)
        page.set_margin_end(18)
        page.set_margin_top(12)
        page.set_margin_bottom(12)

        lbl = Gtk.Label(label="Sistema")
        lbl.set_xalign(0)
        lbl.add_css_class("title-2")
        page.append(lbl)

        rows = []
        for label, value in [
            ("Plataforma", sys.platform),
            ("Python", sys.version.split()[0]),
            ("GTK", "4.0"),
            ("Settings file", SETTINGS_FILE),
            ("Catálogo", f"{len(self.catalog)} juegos"),
        ]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            lbl_name = Gtk.Label(label=label)
            lbl_name.set_xalign(0)
            lbl_name.set_size_request(140, -1)
            lbl_name.add_css_class("dim-label")
            row.append(lbl_name)
            lbl_val = Gtk.Label(label=str(value))
            lbl_val.set_xalign(0)
            lbl_val.set_selectable(True)
            lbl_val.set_ellipsize(Pango.EllipsizeMode.END)
            row.append(lbl_val)
            rows.append(row)

        page.append(self._pref_group("Información del sistema", *rows))

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        page.append(spacer)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(page)
        stack.add_titled(scroll, "system", "Sistema")


def main():
    app = PPLauncher()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
