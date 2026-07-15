#!/usr/bin/env python3
"""PP Launcher - Download Manager
Extracts direct links and downloads games from various hosting services."""
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

DOWNLOADS_DIR = os.path.expanduser("~/PP-Games")
INSTALLED_FILE = os.path.expanduser("~/.pp-launcher/installed.json")
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pp-launcher-downloads")


def _get_opener(extra_headers=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        headers.update(extra_headers)
    return urllib.request.build_opener(urllib.request.HTTPRedirectHandler, urllib.request.HTTPCookieProcessor())


def _fetch(url, extra_headers=None, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    if extra_headers:
        for k, v in extra_headers.items():
            req.add_header(k, v)
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp


def _html(url, extra_headers=None):
    with _fetch(url, extra_headers) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _detect_host(url):
    host = urllib.parse.urlparse(url).hostname or ""
    host = host.lower().replace("www.", "")
    if "buzzheavier" in host or "bzzhr" in host or "fuckingfast" in host:
        return "buzzheavier"
    elif "gofile" in host:
        return "gofile"
    elif "mediafire" in host:
        return "mediafire"
    elif "pixeldrain" in host:
        return "pixeldrain"
    elif "archive.org" in host:
        return "archive"
    elif "drive.google" in host:
        return "gdrive"
    elif "github" in host:
        return "github"
    elif "madiashare" in host:
        return "madiashare"
    elif "megadb" in host:
        return "megadb"
    elif "itch.io" in host or "itch." in host:
        return "itchio"
    elif "mcpelife" in host:
        return "mcpelife"
    return "unknown"


def extract_pixeldrain(url):
    m = re.search(r'pixeldrain\.com/u/([a-zA-Z0-9]+)', url)
    if not m:
        m = re.search(r'pixeldrain\.com/api/file/([a-zA-Z0-9]+)', url)
    if m:
        fid = m.group(1)
        info = json.loads(_html(f"https://pixeldrain.com/api/file/{fid}/info"))
        return {
            "url": f"https://pixeldrain.com/api/file/{fid}?download",
            "filename": info.get("name", f"{fid}.bin"),
            "size": info.get("size", 0),
        }
    return None


def extract_mediafire(url):
    html = _html(url)
    m = re.search(r'href="(https?://download\d+\.mediafire\.com/[^"]+)"', html)
    if m:
        dl_url = m.group(1)
        fname = None
        fname_m = re.search(r'/file/[^/]+/([^/]+)/file', url)
        if fname_m:
            fname = urllib.parse.unquote(fname_m.group(1))
        if not fname:
            path_part = urllib.parse.urlparse(dl_url).path
            last_segment = urllib.parse.unquote(os.path.basename(path_part))
            if "." in last_segment and not last_segment.startswith("http"):
                fname = last_segment
        if not fname:
            fname_m = re.search(r'"([A-Za-z0-9_\-\.]+\.(?:zip|rar|7z|tar|gz|exe|iso))"', html, re.I)
            if fname_m:
                fname = fname_m.group(1)
        return {"url": dl_url, "filename": fname, "size": 0}
    return None


def extract_gdrive(url):
    m = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if m:
        fid = m.group(1)
        direct = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
        try:
            req = urllib.request.Request(direct, method="HEAD", headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                cd = resp.headers.get("Content-Disposition", "")
                fname_m = re.search(r'filename="?([^";]+)', cd)
                size = int(resp.headers.get("Content-Length", 0) or 0)
                return {"url": direct, "filename": fname_m.group(1) if fname_m else None, "size": size}
        except Exception:
            pass
        return {"url": direct, "filename": None, "size": 0}
    return None


def extract_github(url):
    m = re.search(r'github\.com/([^/]+)/([^/]+)/releases/(?:download/([^/]+)/(.+)|.+/download/([^/]+)/(.+))', url)
    if m:
        return {"url": url, "filename": m.group(4) or m.group(6), "size": 0}

    m = re.search(r'github\.com/([^/]+)/([^/]+)', url)
    if m:
        owner, repo = m.group(1), m.group(2)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        data = json.loads(_html(api_url, {"Accept": "application/vnd.github+json"}))
        assets = data.get("assets", [])
        if assets:
            best = max(assets, key=lambda a: a.get("size", 0))
            return {"url": best["browser_download_url"], "filename": best["name"], "size": best.get("size", 0)}
    return None


def extract_archive(url):
    filename = os.path.basename(urllib.parse.urlparse(url).path)
    return {"url": url, "filename": filename or None, "size": 0}


def extract_gofile(url):
    m = re.search(r'gofile\.io/d/([a-zA-Z0-9]+)', url)
    if not m:
        return None
    content_id = m.group(1)
    try:
        acc_req = urllib.request.Request("https://api.gofile.io/accounts", method="POST", headers={
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(acc_req, timeout=15) as resp:
            acc_data = json.loads(resp.read())
        token = acc_data["data"]["token"]

        content_url = f"https://api.gofile.io/contents/{content_id}?token={token}"
        req = urllib.request.Request(content_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_data = json.loads(resp.read())

        if content_data.get("status") == "ok":
            files = content_data.get("data", {}).get("files", {})
            if files:
                first_file = list(files.values())[0]
                return {
                    "url": first_file.get("link", ""),
                    "filename": first_file.get("name"),
                    "size": first_file.get("size", 0),
                }
    except Exception:
        pass

    return None


def extract_buzzheavier(url):
    m = re.search(r'bzzhr\.to/d/([a-zA-Z0-9]+)', url)
    if m:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Referer": url,
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                cd = resp.headers.get("Content-Disposition", "")
                fname_m = re.search(r'filename="?([^";]+)', cd)
                size = int(resp.headers.get("Content-Length", 0) or 0)
                return {"url": resp.url, "filename": fname_m.group(1) if fname_m else None, "size": size}
        except Exception:
            return {"url": url, "filename": None, "size": 0}

    m = re.search(r'buzzheavier\.com/([a-zA-Z0-9]+)', url)
    if not m:
        m = re.search(r'bzzhr\.co/([a-zA-Z0-9]+)', url)
    if not m:
        return None
    file_id = m.group(1)

    try:
        html = _html(f"https://buzzheavier.com/{file_id}")
        token_m = re.search(r'download\?t=([^"\'&\\#]+)', html)
        if token_m:
            token = token_m.group(1)
            dl_url = f"https://buzzheavier.com/{file_id}/download?t={token}&alt=true"
            req = urllib.request.Request(dl_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "hx-request": "true",
                "hx-current-url": f"https://buzzheavier.com/{file_id}",
                "referer": f"https://buzzheavier.com/{file_id}",
            })
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    pass
            except urllib.error.HTTPError as e:
                hx_redirect = e.headers.get("Hx-Redirect") or e.headers.get("Location")
                if hx_redirect:
                    return {"url": hx_redirect, "filename": None, "size": 0}
    except Exception:
        pass

    return None


def extract_megadb(url):
    try:
        html = _html(url)
        m = re.search(r'href="(https?://[^"]*download[^"]*)"', html, re.I)
        if m:
            return {"url": m.group(1), "filename": None, "size": 0}

        m = re.search(r'data-url="([^"]+)"', html)
        if m:
            return {"url": m.group(1), "filename": None, "size": 0}

        m = re.search(r'"(https?://[^"]+\.(?:zip|rar|7z|tar|gz))"', html, re.I)
        if m:
            return {"url": m.group(1), "filename": None, "size": 0}
    except Exception:
        pass
    return None


def extract_madiashare(url):
    try:
        html = _html(url)
        m = re.search(r'action="(https?://[^"]*descargar[^"]*)"', html, re.I)
        if m:
            post_url = m.group(1)
            inputs = re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', html)
            if inputs:
                data = urllib.parse.urlencode(dict(inputs)).encode()
                req = urllib.request.Request(post_url, data=data, headers={
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/x-www-form-urlencoded",
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    cd = resp.headers.get("Content-Disposition", "")
                    fname_m = re.search(r'filename="?([^";]+)', cd)
                    size = int(resp.headers.get("Content-Length", 0) or 0)
                    return {"url": resp.url, "filename": fname_m.group(1) if fname_m else None, "size": size}
    except Exception:
        pass
    return None


def extract_itchio(url):
    try:
        html = _html(url)
        download_links = re.findall(r'href="(https?://[^"]*uploads\.itch[^"]*)"', html)
        if download_links:
            return {"url": download_links[0], "filename": None, "size": 0}

        upload_divs = re.findall(r'data-upload="(\d+)"[^>]*data-href="([^"]+)"', html)
        if upload_divs:
            return {"url": upload_divs[0][1], "filename": None, "size": 0}
    except Exception:
        pass
    return None


def extract_mcpelife(url):
    try:
        html = _html(url)
        m = re.search(r'href="(https?://[^"]*download[^"]*\.(?:apk|zip|rar|7z))"', html, re.I)
        if m:
            return {"url": m.group(1), "filename": None, "size": 0}

        m = re.search(r'href="(https?://mcpelife\.com/[^"]*download[^"]*)"', html, re.I)
        if m:
            inner_html = _html(m.group(1))
            m2 = re.search(r'href="(https?://[^"]+\.(?:apk|zip|rar|7z))"', inner_html, re.I)
            if m2:
                return {"url": m2.group(1), "filename": None, "size": 0}
    except Exception:
        pass
    return None


EXTRACTORS = {
    "pixeldrain": extract_pixeldrain,
    "mediafire": extract_mediafire,
    "gdrive": extract_gdrive,
    "github": extract_github,
    "archive": extract_archive,
    "gofile": extract_gofile,
    "buzzheavier": extract_buzzheavier,
    "megadb": extract_megadb,
    "madiashare": extract_madiashare,
    "itchio": extract_itchio,
    "mcpelife": extract_mcpelife,
}


def extract_direct_link(url):
    host = _detect_host(url)
    extractor = EXTRACTORS.get(host)
    if extractor:
        try:
            result = extractor(url)
            if result and result.get("url"):
                result["host"] = host
                return result
        except Exception:
            pass
    return {"url": url, "filename": None, "size": 0, "host": host, "needs_browser": True}


class DownloadManager:
    def __init__(self):
        self.active_downloads = {}
        self._meta = {}
        self._lock = threading.Lock()
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)

    def get_installed(self):
        try:
            with open(INSTALLED_FILE) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_installed(self, data):
        os.makedirs(os.path.dirname(INSTALLED_FILE), exist_ok=True)
        with open(INSTALLED_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def is_installed(self, game_id):
        return game_id in self.get_installed()

    def mark_installed(self, game_id, game_name, install_path):
        installed = self.get_installed()
        installed[game_id] = {
            "name": game_name,
            "path": install_path,
            "installed_at": time.time(),
        }
        self._save_installed(installed)

    def mark_uninstalled(self, game_id):
        installed = self.get_installed()
        if game_id in installed:
            del installed[game_id]
            self._save_installed(installed)

    def get_install_path(self, game_id):
        installed = self.get_installed()
        if game_id in installed:
            return installed[game_id].get("path")
        return None

    def download(self, game_id, game_name, url, progress_callback=None, done_callback=None):
        with self._lock:
            st = self.active_downloads.get(game_id, {})
            if st.get("status") in ("extracting_link", "downloading", "extracting", "paused"):
                return False
            self.active_downloads[game_id] = {"status": "extracting_link", "progress": 0}
        self._meta[game_id] = {
            "game_name": game_name,
            "url": url,
            "progress_callback": progress_callback,
            "done_callback": done_callback,
        }
        threading.Thread(target=self._worker, args=(game_id, False), daemon=True).start()
        return True

    def _worker(self, game_id, resume):
        meta = self._meta.get(game_id, {})
        game_name = meta.get("game_name", game_id)
        url = meta.get("url", "")
        progress_callback = meta.get("progress_callback")
        done_callback = meta.get("done_callback")
        try:
            if resume and meta.get("direct_url"):
                direct_url = meta["direct_url"]
                filename = meta["filename"]
                dest = meta["dest"]
                game_dir = meta["game_dir"]
            else:
                link_info = extract_direct_link(url)
                direct_url = link_info.get("url", url)
                filename = link_info.get("filename")
                host = link_info.get("host", "unknown")

                if link_info.get("needs_browser"):
                    with self._lock:
                        self.active_downloads[game_id] = {
                            "status": "needs_browser",
                            "progress": 0,
                            "url": url,
                            "host": host,
                        }
                    if progress_callback:
                        progress_callback(game_id, "needs_browser", 0, url)
                    return

                if not filename:
                    filename = _guess_filename(direct_url, game_name)
                filename = _sanitize_filename(filename)

                game_dir = os.path.join(DOWNLOADS_DIR, _sanitize_filename(game_name))
                os.makedirs(game_dir, exist_ok=True)
                dest = os.path.join(game_dir, filename)

                if os.path.exists(dest):
                    try:
                        os.remove(dest)
                    except Exception:
                        pass
                meta.update({"direct_url": direct_url, "filename": filename,
                             "dest": dest, "game_dir": game_dir})

            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Referer": url,
            }
            downloaded = 0
            file_mode = "wb"
            if resume and os.path.exists(dest):
                downloaded = os.path.getsize(dest)
                headers["Range"] = f"bytes={downloaded}-"
                file_mode = "ab"

            req = urllib.request.Request(direct_url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=600)

            if resp.status == 200 and file_mode == "ab":
                downloaded = 0
                file_mode = "wb"
            remaining = int(resp.headers.get("Content-Length", 0) or 0)
            total = meta.get("total") or (downloaded + remaining)
            meta["total"] = total

            with self._lock:
                self.active_downloads[game_id] = {"status": "downloading", "progress": 0, "filename": filename}

            start_time = time.time()
            start_bytes = downloaded
            chunk_size = 256 * 1024
            paused = False

            try:
                with open(dest, file_mode) as f:
                    while True:
                        with self._lock:
                            state = self.active_downloads.get(game_id, {}).get("status")
                        if state == "cancelled":
                            break
                        if state == "pausing":
                            paused = True
                            break
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        pct = int(downloaded * 100 / total) if total > 0 else 0
                        elapsed = time.time() - start_time
                        speed = (downloaded - start_bytes) / elapsed if elapsed > 0 else 0
                        eta = (total - downloaded) / speed if (total > 0 and speed > 0) else 0

                        with self._lock:
                            if self.active_downloads.get(game_id, {}).get("status") in ("cancelled", "pausing"):
                                continue
                            self.active_downloads[game_id] = {
                                "status": "downloading",
                                "progress": pct,
                                "downloaded": downloaded,
                                "total": total,
                                "speed": speed,
                                "eta": eta,
                                "filename": filename,
                            }

                        if progress_callback:
                            progress_callback(game_id, "downloading", pct, "")
            finally:
                resp.close()

            if paused:
                pct = int(downloaded * 100 / total) if total > 0 else 0
                with self._lock:
                    self.active_downloads[game_id] = {
                        "status": "paused", "progress": pct,
                        "downloaded": downloaded, "total": total,
                        "filename": filename,
                    }
                if progress_callback:
                    progress_callback(game_id, "paused", pct, "")
                return

            with self._lock:
                if self.active_downloads.get(game_id, {}).get("status") == "cancelled":
                    try:
                        if os.path.exists(dest):
                            os.remove(dest)
                    except Exception:
                        pass
                    try:
                        if os.path.isdir(game_dir) and not os.listdir(game_dir):
                            os.rmdir(game_dir)
                    except Exception:
                        pass
                    return

            # Validar que el archivo sea un juego real y no una página de error.
            if not _is_valid_download(dest):
                try:
                    if os.path.exists(dest):
                        os.remove(dest)
                    if os.path.isdir(game_dir) and not os.listdir(game_dir):
                        os.rmdir(game_dir)
                except Exception:
                    pass
                raise ValueError(
                    "Archivo descargado no válido (probablemente una página de error).")

            with self._lock:
                self.active_downloads[game_id] = {"status": "extracting", "progress": 100}

            if progress_callback:
                progress_callback(game_id, "extracting", 100, filename)

            extracted_path = _extract_archive(dest, game_dir, game_name)

            with self._lock:
                self.active_downloads[game_id] = {"status": "complete", "progress": 100}

            if progress_callback:
                progress_callback(game_id, "complete", 100, "")

            if done_callback:
                done_callback(game_id, game_name, extracted_path or game_dir)

        except Exception as e:
            with self._lock:
                self.active_downloads[game_id] = {"status": "error", "progress": 0, "error": str(e)}
            if progress_callback:
                progress_callback(game_id, "error", 0, str(e))

    def pause(self, game_id):
        with self._lock:
            st = self.active_downloads.get(game_id)
            if st and st.get("status") == "downloading":
                self.active_downloads[game_id]["status"] = "pausing"
                return True
        return False

    def resume(self, game_id):
        with self._lock:
            st = self.active_downloads.get(game_id)
            if not (st and st.get("status") == "paused"):
                return False
            self.active_downloads[game_id]["status"] = "downloading"
        threading.Thread(target=self._worker, args=(game_id, True), daemon=True).start()
        return True

    def cancel(self, game_id):
        with self._lock:
            if game_id in self.active_downloads:
                self.active_downloads[game_id]["status"] = "cancelled"
                return True
        return False

    def get_status(self, game_id):
        with self._lock:
            return self.active_downloads.get(game_id)

    def get_all_status(self):
        with self._lock:
            return dict(self.active_downloads)


def _guess_filename(url, game_name):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    fname = os.path.basename(path)
    if fname and "." in fname:
        return urllib.parse.unquote(fname)
    return _sanitize_filename(game_name) + ".bin"


def _sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name).strip()
    name = name.strip('.')
    return name[:200] if name else "download"


def _is_valid_download(filepath):
    """Comprueba que un archivo descargado sea un juego/instalador real y no
    una página de error (HTML) ni un archivo corrupto/truncado."""
    try:
        size = os.path.getsize(filepath)
    except Exception:
        return False
    if size < 1024:
        return False
    with open(filepath, "rb") as f:
        head = f.read(32)
    good_sigs = (
        b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08",   # zip
        b"MZ",                                          # exe / dll
        b"Rar!\x1a\x07",                                # rar
        b"7z\xbc\xaf\x27\x1c",                          # 7z
        b"\x1f\x8b",                                    # gzip
        b"BZh",                                         # bzip2
        b"CD001",                                       # iso 9660
        b"ustar",                                       # tar
        b"MSCF",                                        # cab
        b"OggS",                                        # ogg
        b"%PDF",                                        # pdf
        b"\x89PNG", b"\xff\xd8\xff", b"GIF8",           # imágenes
        b"fLaC", b"ID3", b"\x00\x00\x01\xba",           # multimedia
    )
    if any(head.startswith(sig) for sig in good_sigs):
        return True
    low = head.lstrip().lower()
    if low.startswith(b"<!doctype") or low.startswith(b"<html") or low.startswith(b"<"):
        return False
    # Binario y grande pero de formato no listado: se asume válido.
    return True


def _extract_archive(filepath, dest_dir, game_name):
    ext = filepath.lower()

    if ext.endswith('.zip'):
        import zipfile
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                zf.extractall(dest_dir)
            return dest_dir
        except Exception:
            pass

    elif ext.endswith('.rar'):
        try:
            result = subprocess.run(
                ["unrar", "x", "-o+", "-y", filepath, dest_dir + "/"],
                capture_output=True, timeout=600
            )
            if result.returncode == 0:
                return dest_dir
        except FileNotFoundError:
            pass
        try:
            result = subprocess.run(
                ["7z", "x", f"-o{dest_dir}", "-y", filepath],
                capture_output=True, timeout=600
            )
            if result.returncode == 0:
                return dest_dir
        except FileNotFoundError:
            pass

    elif ext.endswith('.7z'):
        try:
            result = subprocess.run(
                ["7z", "x", f"-o{dest_dir}", "-y", filepath],
                capture_output=True, timeout=600
            )
            if result.returncode == 0:
                return dest_dir
        except FileNotFoundError:
            pass

    elif ext.endswith('.tar.gz') or ext.endswith('.tgz'):
        import tarfile
        try:
            with tarfile.open(filepath, 'r:gz') as tf:
                tf.extractall(dest_dir)
            return dest_dir
        except Exception:
            pass

    elif ext.endswith('.tar'):
        import tarfile
        try:
            with tarfile.open(filepath, 'r') as tf:
                tf.extractall(dest_dir)
            return dest_dir
        except Exception:
            pass

    elif ext.endswith('.iso'):
        return filepath

    return filepath


def find_exe_in_dir(directory):
    exe_extensions = ('.exe', '.bat', '.cmd', '.sh')
    candidates = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(exe_extensions):
                path = os.path.join(root, f)
                candidates.append(path)
        depth = root.replace(directory, '').count(os.sep)
        if depth >= 3:
            dirs.clear()

    if not candidates:
        return None

    for exe in candidates:
        name_lower = os.path.basename(exe).lower()
        if any(k in name_lower for k in ["launch", "start", "play", "game", "main"]):
            return exe

    return candidates[0] if candidates else None
