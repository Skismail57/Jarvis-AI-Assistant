import os
import re
import sys
import shutil
import time
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple


class PCController:
    def __init__(self):
        self.is_windows = sys.platform.startswith("win")
        self.is_mac = sys.platform == "darwin"
        self.is_linux = sys.platform.startswith("linux")
        self._clipboard_stack: List[str] = []

    def _run(self, cmd: str, shell: bool = True, capture: bool = True, timeout: int = 30) -> Tuple[int, str, str]:
        try:
            r = subprocess.run(cmd, shell=shell, capture_output=capture, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except Exception as e:
            return -1, "", str(e)

    # ---------------- App control ----------------
    def open_app(self, name: str) -> Dict[str, Any]:
        name_l = name.lower().strip()
        mapping = {
            "chrome": ("start chrome" if self.is_windows else "open -a 'Google Chrome'" if self.is_mac else "google-chrome"),
            "edge": ("start msedge" if self.is_windows else "open -a 'Microsoft Edge'" if self.is_mac else "microsoft-edge"),
            "firefox": ("start firefox" if self.is_windows else "open -a Firefox" if self.is_mac else "firefox"),
            "notepad": ("notepad" if self.is_windows else "open -a TextEdit" if self.is_mac else "gedit"),
            "calculator": ("calc" if self.is_windows else "open -a Calculator" if self.is_mac else "gnome-calculator"),
            "explorer": ("explorer" if self.is_windows else "open /" if self.is_mac else "nautilus"),
            "file manager": ("explorer" if self.is_windows else "open /" if self.is_mac else "nautilus"),
            "command prompt": ("cmd" if self.is_windows else "open -a Terminal" if self.is_mac else "gnome-terminal"),
            "terminal": ("cmd" if self.is_windows else "open -a Terminal" if self.is_mac else "gnome-terminal"),
            "powershell": ("powershell" if self.is_windows else "open -a Terminal" if self.is_mac else "gnome-terminal"),
            "word": ("start winword" if self.is_windows else "open -a 'Microsoft Word'" if self.is_mac else "libreoffice --writer"),
            "excel": ("start excel" if self.is_windows else "open -a 'Microsoft Excel'" if self.is_mac else "libreoffice --calc"),
            "powerpoint": ("start powerpnt" if self.is_windows else "open -a 'Microsoft PowerPoint'" if self.is_mac else "libreoffice --impress"),
            "outlook": ("start outlook" if self.is_windows else "open -a 'Microsoft Outlook'" if self.is_mac else "thunderbird"),
            "spotify": ("start spotify" if self.is_windows else "open -a Spotify" if self.is_mac else "spotify"),
            "discord": ("start discord" if self.is_windows else "open -a Discord" if self.is_mac else "discord"),
            "slack": ("start slack" if self.is_windows else "open -a Slack" if self.is_mac else "slack"),
            "code": ("code" if self.is_windows else "open -a 'Visual Studio Code'" if self.is_mac else "code"),
            "vs code": ("code" if self.is_windows else "open -a 'Visual Studio Code'" if self.is_mac else "code"),
            "vscode": ("code" if self.is_windows else "open -a 'Visual Studio Code'" if self.is_mac else "code"),
            "settings": ("start ms-settings:" if self.is_windows else "open 'x-apple.systempreferences:'" if self.is_mac else "gnome-control-center"),
            "paint": ("mspaint" if self.is_windows else "open -a Preview" if self.is_mac else "gimp"),
            "store": ("start ms-windows-store:" if self.is_windows else "open -a App Store" if self.is_mac else "snap-store"),
            "camera": ("start microsoft.windows.camera:" if self.is_windows else "open -a Photo Booth" if self.is_mac else "cheese"),
            "task manager": ("taskmgr" if self.is_windows else "open -a 'Activity Monitor'" if self.is_mac else "gnome-system-monitor"),
            "control panel": ("control" if self.is_windows else "open -a 'System Settings'" if self.is_mac else "gnome-control-center"),
        }
        cmd = mapping.get(name_l)
        if cmd:
            code, _, err = self._run(cmd, capture=False, timeout=10)
            return {"action": "open_app", "app": name, "success": code == 0, "error": err}
        try:
            if self.is_windows:
                code, _, err = self._run(f"start {name}", capture=False, timeout=10)
                return {"action": "open_app", "app": name, "success": code == 0, "error": err}
            if self.is_mac:
                code, _, err = self._run(f"open -a '{name}'", capture=False, timeout=10)
                return {"action": "open_app", "app": name, "success": code == 0, "error": err}
            code, _, err = self._run(name, capture=False, timeout=10)
            return {"action": "open_app", "app": name, "success": code == 0, "error": err}
        except Exception as e:
            return {"action": "open_app", "app": name, "success": False, "error": str(e)}

    def close_app(self, name: str) -> Dict[str, Any]:
        name_l = name.lower().strip()
        mapping = {
            "chrome": "chrome.exe" if self.is_windows else "Chrome" if self.is_mac else "chrome",
            "edge": "msedge.exe" if self.is_windows else "Microsoft Edge" if self.is_mac else "microsoft-edge",
            "firefox": "firefox.exe" if self.is_windows else "Firefox" if self.is_mac else "firefox",
            "notepad": "notepad.exe" if self.is_windows else "TextEdit" if self.is_mac else "gedit",
            "calculator": "calc.exe" if self.is_windows else "Calculator" if self.is_mac else "gnome-calculator",
            "explorer": "explorer.exe" if self.is_windows else "Finder" if self.is_mac else "nautilus",
            "file manager": "explorer.exe" if self.is_windows else "Finder" if self.is_mac else "nautilus",
            "word": "WINWORD.EXE" if self.is_windows else "Microsoft Word" if self.is_mac else "soffice",
            "excel": "EXCEL.EXE" if self.is_windows else "Microsoft Excel" if self.is_mac else "soffice",
            "powerpoint": "POWERPNT.EXE" if self.is_windows else "Microsoft PowerPoint" if self.is_mac else "soffice",
            "vs code": "Code.exe" if self.is_windows else "Visual Studio Code" if self.is_mac else "code",
            "vscode": "Code.exe" if self.is_windows else "Visual Studio Code" if self.is_mac else "code",
            "code": "Code.exe" if self.is_windows else "Visual Studio Code" if self.is_mac else "code",
        }
        target = mapping.get(name_l, name if not self.is_windows else name + (".exe" if not name.endswith(".exe") else ""))
        try:
            if self.is_windows:
                code, out, err = self._run(f"taskkill /F /IM {target} /T 2>&1")
                success = (code == 0) or ("no tasks" in (out + err).lower())
                return {"action": "close_app", "app": name, "success": success, "error": err if not success else ""}
            if self.is_mac:
                code, _, err = self._run(f"pkill -f '{target}' || killall '{target}' 2>/dev/null; echo done")
                return {"action": "close_app", "app": name, "success": True, "error": err}
            code, _, err = self._run(f"pkill -f '{target}' 2>/dev/null || true")
            return {"action": "close_app", "app": name, "success": True, "error": err}
        except Exception as e:
            return {"action": "close_app", "app": name, "success": False, "error": str(e)}

    def list_running_processes(self, limit: int = 50) -> List[Dict[str, Any]]:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
            try:
                info = p.info
                mem_mb = round((info.get("memory_info").rss / (1024 * 1024)), 1) if info.get("memory_info") else 0.0
                procs.append({
                    "pid": info["pid"],
                    "name": info.get("name", ""),
                    "cpu_percent": info.get("cpu_percent", 0.0),
                    "mem_mb": mem_mb
                })
            except Exception:
                continue
        procs.sort(key=lambda x: x["mem_mb"], reverse=True)
        return procs[:limit]

    # ---------------- Web / URL ----------------
    def open_url(self, url: str) -> Dict[str, Any]:
        if not re.match(r"^https?://", url):
            url = "https://" + url
        try:
            webbrowser.open(url, new=2)
            return {"action": "open_url", "url": url, "success": True}
        except Exception as e:
            return {"action": "open_url", "url": url, "success": False, "error": str(e)}

    def google_search(self, query: str) -> Dict[str, Any]:
        url = f"https://www.google.com/search?q={_urlq(query)}"
        webbrowser.open(url, new=2)
        return {"action": "google_search", "query": query, "url": url, "success": True}

    def youtube_search(self, query: str) -> Dict[str, Any]:
        url = f"https://www.youtube.com/results?search_query={_urlq(query)}"
        webbrowser.open(url, new=2)
        return {"action": "youtube_search", "query": query, "url": url, "success": True}

    def maps_search(self, query: str) -> Dict[str, Any]:
        url = f"https://www.google.com/maps/search/{_urlq(query)}"
        webbrowser.open(url, new=2)
        return {"action": "maps_search", "query": query, "url": url, "success": True}

    def directions(self, origin: str, destination: str) -> Dict[str, Any]:
        url = f"https://www.google.com/maps/dir/{_urlq(origin)}/{_urlq(destination)}"
        webbrowser.open(url, new=2)
        return {"action": "directions", "origin": origin, "destination": destination, "url": url, "success": True}

    # ---------------- File & folder operations ----------------
    def _resolve(self, path: str) -> Path:
        return Path(os.path.expandvars(os.path.expanduser(path))).resolve()

    def list_folder(self, path: str = ".") -> Dict[str, Any]:
        p = self._resolve(path)
        if not p.exists():
            return {"action": "list_folder", "path": str(p), "success": False, "error": "Path not found"}
        if not p.is_dir():
            return {"action": "list_folder", "path": str(p), "success": False, "error": "Not a folder"}
        items = []
        for child in sorted(p.iterdir()):
            try:
                items.append({
                    "name": child.name,
                    "type": "folder" if child.is_dir() else "file",
                    "size": child.stat().st_size if child.is_file() else 0,
                    "modified": time.ctime(child.stat().st_mtime),
                })
            except Exception:
                continue
        return {"action": "list_folder", "path": str(p), "success": True, "items": items, "count": len(items)}

    def open_folder(self, path: str = ".") -> Dict[str, Any]:
        p = self._resolve(path)
        if not p.exists():
            return {"action": "open_folder", "path": str(p), "success": False, "error": "Path not found"}
        try:
            if self.is_windows:
                os.startfile(str(p))
            elif self.is_mac:
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
            return {"action": "open_folder", "path": str(p), "success": True}
        except Exception as e:
            return {"action": "open_folder", "path": str(p), "success": False, "error": str(e)}

    def open_file(self, path: str) -> Dict[str, Any]:
        return self.open_folder(path)

    def create_folder(self, path: str) -> Dict[str, Any]:
        p = self._resolve(path)
        try:
            p.mkdir(parents=True, exist_ok=True)
            return {"action": "create_folder", "path": str(p), "success": True}
        except Exception as e:
            return {"action": "create_folder", "path": str(p), "success": False, "error": str(e)}

    def delete(self, path: str, skip_confirm: bool = True) -> Dict[str, Any]:
        p = self._resolve(path)
        if not p.exists():
            return {"action": "delete", "path": str(p), "success": False, "error": "Path not found"}
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return {"action": "delete", "path": str(p), "success": True}
        except Exception as e:
            return {"action": "delete", "path": str(p), "success": False, "error": str(e)}

    def copy(self, src: str, dst: str) -> Dict[str, Any]:
        s, d = self._resolve(src), self._resolve(dst)
        if not s.exists():
            return {"action": "copy", "src": str(s), "dst": str(d), "success": False, "error": "Source not found"}
        try:
            if s.is_dir():
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)
            return {"action": "copy", "src": str(s), "dst": str(d), "success": True}
        except Exception as e:
            return {"action": "copy", "src": str(s), "dst": str(d), "success": False, "error": str(e)}

    def move(self, src: str, dst: str) -> Dict[str, Any]:
        s, d = self._resolve(src), self._resolve(dst)
        if not s.exists():
            return {"action": "move", "src": str(s), "dst": str(d), "success": False, "error": "Source not found"}
        try:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(s), str(d))
            return {"action": "move", "src": str(s), "dst": str(d), "success": True}
        except Exception as e:
            return {"action": "move", "src": str(s), "dst": str(d), "success": False, "error": str(e)}

    def cut(self, src: str) -> Dict[str, Any]:
        s = self._resolve(src)
        if not s.exists():
            return {"action": "cut", "src": str(s), "success": False, "error": "Source not found"}
        self._clipboard_stack.append(str(s))
        return {"action": "cut", "src": str(s), "success": True, "clipboard": self._clipboard_stack}

    def paste(self, dst: str = ".") -> Dict[str, Any]:
        d = self._resolve(dst)
        if not self._clipboard_stack:
            return {"action": "paste", "dst": str(d), "success": False, "error": "Clipboard empty, please cut/copy first"}
        results = []
        for src in list(self._clipboard_stack):
            s = Path(src)
            target = d / s.name
            try:
                if s.is_dir():
                    shutil.move(str(s), str(target)) if self._clipboard_mode == "cut" else shutil.copytree(s, target, dirs_exist_ok=True)
                else:
                    d.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(s), str(target)) if self._clipboard_mode == "cut" else shutil.copy2(s, target)
                results.append({"src": str(s), "dst": str(target), "success": True})
            except Exception as e:
                results.append({"src": str(s), "dst": str(target), "success": False, "error": str(e)})
        self._clipboard_stack.clear()
        return {"action": "paste", "dst": str(d), "success": True, "results": results}

    def copy_to_clipboard(self, src: str) -> Dict[str, Any]:
        s = self._resolve(src)
        if not s.exists():
            return {"action": "copy_to_clipboard", "src": str(s), "success": False, "error": "Source not found"}
        self._clipboard_stack.append(str(s))
        self._clipboard_mode = "copy"
        return {"action": "copy_to_clipboard", "src": str(s), "success": True, "clipboard": self._clipboard_stack}

    def rename(self, path: str, new_name: str) -> Dict[str, Any]:
        p = self._resolve(path)
        if not p.exists():
            return {"action": "rename", "path": str(p), "to": new_name, "success": False, "error": "Source not found"}
        target = p.parent / new_name
        try:
            p.rename(target)
            return {"action": "rename", "from": str(p), "to": str(target), "success": True}
        except Exception as e:
            return {"action": "rename", "from": str(p), "to": str(target), "success": False, "error": str(e)}

    def search_files(self, name_pattern: str, root: str = ".") -> Dict[str, Any]:
        r = self._resolve(root)
        results: List[str] = []
        pat = re.compile(name_pattern, re.IGNORECASE)
        for p in r.rglob("*"):
            try:
                if pat.search(p.name):
                    results.append(str(p))
                    if len(results) > 200:
                        break
            except Exception:
                continue
        return {"action": "search_files", "pattern": name_pattern, "root": str(r), "success": True, "matches": results, "count": len(results)}

    # ---------------- Screen / display ----------------
    def take_screenshot(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        try:
            import pyautogui
            ss = pyautogui.screenshot()
            if save_path is None:
                from datetime import datetime
                folder = self._resolve("~/Pictures/Jarvis Screenshots")
                folder.mkdir(parents=True, exist_ok=True)
                save_path = str(folder / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            else:
                save_path = str(self._resolve(save_path))
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            ss.save(save_path)
            return {"action": "screenshot", "path": save_path, "success": True}
        except Exception as e:
            return {"action": "screenshot", "success": False, "error": str(e)}

    def set_brightness(self, level: int) -> Dict[str, Any]:
        level = max(0, min(100, int(level)))
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(level)
            return {"action": "set_brightness", "level": level, "success": True}
        except Exception:
            try:
                if self.is_windows:
                    import ctypes
                    def gamma(level):
                        g = int((level / 100) * 65535)
                        ramp = ([i * g // 255 for i in range(256)] * 3)
                        ramp = (ctypes.c_ushort * (256 * 3))(*ramp)
                        hdc = ctypes.windll.user32.GetDC(0)
                        ctypes.windll.gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp))
                        ctypes.windll.user32.ReleaseDC(0, hdc)
                    gamma(level)
                    return {"action": "set_brightness", "level": level, "success": True, "note": "Used gamma ramp approximation"}
            except Exception as e:
                return {"action": "set_brightness", "level": level, "success": False, "error": str(e)}
        return {"action": "set_brightness", "level": level, "success": False, "error": "unsupported"}

    def get_brightness(self) -> Dict[str, Any]:
        try:
            import screen_brightness_control as sbc
            val = sbc.get_brightness(display=0)
            if isinstance(val, list):
                val = val[0]
            return {"action": "get_brightness", "level": int(val), "success": True}
        except Exception as e:
            return {"action": "get_brightness", "success": False, "error": str(e)}

    def set_volume(self, level: int) -> Dict[str, Any]:
        level = max(0, min(100, int(level)))
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return {"action": "set_volume", "level": level, "success": True}
        except Exception:
            try:
                if self.is_windows:
                    import ctypes
                    NL_VOLUME, SL_VOLUME = 0x5000, 0x302E2
                    ctypes.windll.user32.SendMessageW(0xFFFF, 0x319, 0, NL_VOLUME | SL_VOLUME | level)
                    return {"action": "set_volume", "level": level, "success": True}
                if self.is_linux:
                    subprocess.run(["amixer", "-q", "sset", "Master", f"{level}%"])
                    return {"action": "set_volume", "level": level, "success": True}
            except Exception as e:
                return {"action": "set_volume", "level": level, "success": False, "error": str(e)}
        return {"action": "set_volume", "level": level, "success": False}

    def get_volume(self) -> Dict[str, Any]:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            level = int(round(volume.GetMasterVolumeLevelScalar() * 100))
            return {"action": "get_volume", "level": level, "success": True}
        except Exception:
            return {"action": "get_volume", "success": False}

    def lock_screen(self) -> Dict[str, Any]:
        try:
            if self.is_windows:
                self._run("rundll32.exe user32.dll,LockWorkStation", capture=False, timeout=10)
            elif self.is_mac:
                self._run("pmset displaysleepnow", capture=False, timeout=10)
            else:
                self._run("xdg-screensaver lock", capture=False, timeout=10)
            return {"action": "lock_screen", "success": True}
        except Exception as e:
            return {"action": "lock_screen", "success": False, "error": str(e)}

    def shutdown(self, seconds: int = 60) -> Dict[str, Any]:
        try:
            if self.is_windows:
                self._run(f"shutdown /s /t {seconds}", capture=False, timeout=10)
            else:
                self._run(f"shutdown -h {seconds if seconds else 'now'}", capture=False, timeout=10)
            return {"action": "shutdown", "in_seconds": seconds, "success": True}
        except Exception as e:
            return {"action": "shutdown", "success": False, "error": str(e)}

    def cancel_shutdown(self) -> Dict[str, Any]:
        try:
            if self.is_windows:
                self._run("shutdown /a", capture=False, timeout=10)
            else:
                self._run("shutdown -c", capture=False, timeout=10)
            return {"action": "cancel_shutdown", "success": True}
        except Exception as e:
            return {"action": "cancel_shutdown", "success": False, "error": str(e)}

    def restart(self, seconds: int = 10) -> Dict[str, Any]:
        try:
            if self.is_windows:
                self._run(f"shutdown /r /t {seconds}", capture=False, timeout=10)
            else:
                self._run(f"shutdown -r {seconds if seconds else 'now'}", capture=False, timeout=10)
            return {"action": "restart", "in_seconds": seconds, "success": True}
        except Exception as e:
            return {"action": "restart", "success": False, "error": str(e)}

    def sleep(self) -> Dict[str, Any]:
        try:
            if self.is_windows:
                self._run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", capture=False, timeout=10)
            elif self.is_mac:
                self._run("pmset sleepnow", capture=False, timeout=10)
            else:
                self._run("systemctl suspend", capture=False, timeout=10)
            return {"action": "sleep", "success": True}
        except Exception as e:
            return {"action": "sleep", "success": False, "error": str(e)}

    def hibernate(self) -> Dict[str, Any]:
        try:
            if self.is_windows:
                self._run("shutdown /h", capture=False, timeout=10)
            else:
                self._run("systemctl hibernate", capture=False, timeout=10)
            return {"action": "hibernate", "success": True}
        except Exception as e:
            return {"action": "hibernate", "success": False, "error": str(e)}

    def system_info(self) -> Dict[str, Any]:
        import platform, psutil
        boot = psutil.boot_time()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/" if not self.is_windows else "C:\\")
        return {
            "node": platform.node(),
            "os": f"{platform.system()} {platform.release()}",
            "version": platform.version(),
            "arch": platform.machine(),
            "processor": platform.processor() or "unknown",
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=0.3),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "ram_used_gb": round(mem.used / (1024 ** 3), 2),
            "ram_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_used_gb": round(disk.used / (1024 ** 3), 2),
            "disk_percent": disk.percent,
            "booted": time.ctime(boot),
            "uptime_seconds": int(time.time() - boot),
        }


def _urlq(s: str) -> str:
    import urllib.parse
    return urllib.parse.quote(s)
