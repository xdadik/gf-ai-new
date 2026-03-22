# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
import ast  # type: ignore  # pyre-ignore
import json  # type: ignore  # pyre-ignore
import psutil  # type: ignore  # pyre-ignore
import subprocess  # type: ignore  # pyre-ignore
import platform  # type: ignore  # pyre-ignore
import sys  # type: ignore  # pyre-ignore
import pyautogui  # type: ignore  # pyre-ignore
import pyperclip  # type: ignore  # pyre-ignore
import webbrowser  # type: ignore  # pyre-ignore
import requests  # type: ignore  # pyre-ignore
import shutil  # type: ignore  # pyre-ignore
from datetime import datetime  # type: ignore  # pyre-ignore
from pathlib import Path  # type: ignore  # pyre-ignore
from collections import Counter  # type: ignore  # pyre-ignore
from typing import Dict, Any, Optional  # type: ignore  # pyre-ignore
from bs4 import BeautifulSoup  # type: ignore  # pyre-ignore

try:
    from encryption import secure_channel, encrypted_commands, get_secure_channel  # type: ignore  # pyre-ignore
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

AUDIT_LOG_FILE = "pc_control_audit.log"
dangerous_processes = {
    "cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe",
    "mshta.exe", "regsvr32.exe", "rundll32.exe", "cmstp.exe"
}

def log_audit(user_id: str, operation: str, args: dict, result: str):
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] USER:{user_id} OP:{operation} ARGS:{args} RESULT:{result}\n"  # type: ignore  # pyre-ignore
    try:
        with open(AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        pass

def sanitize_path(path: str, base_dir: str = ".") -> Optional[str]:  # type: ignore  # pyre-ignore
    try:
        base = Path(base_dir).resolve()
        target = (base / path).resolve()
        target.relative_to(base)
        return str(target)
    except Exception:
        return None  # type: ignore  # pyre-ignore

def validate_process_name(name: str) -> bool:  # type: ignore  # pyre-ignore
    clean_name = os.path.basename(name).lower()
    for dangerous in dangerous_processes:
        if dangerous.lower() == clean_name:
            return False
    return True

def take_screenshot(filename: str = "screenshot.png", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "take_screenshot", {"filename": filename}, "started")
    try:
        screenshot = pyautogui.screenshot()

        # Create screenshots directory if it doesn't exist
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(exist_ok=True)

        # If filename is just a name (no path), save to screenshots dir
        # If filename has a path, validate it and use it
        if os.path.dirname(filename):
            # Custom path provided - sanitize and validate
            target_dir = Path(os.path.dirname(filename)).resolve()
            # Only allow saving to user-accessible locations, not system dirs
            allowed_roots = [Path.home(), Path.cwd(), Path("C:/Users")]
            is_allowed = any(str(target_dir).startswith(str(root)) for root in allowed_roots)

            if not is_allowed:
                log_audit(user_id, "take_screenshot", {"filename": filename}, "blocked_path")
                safe_path = screenshots_dir / os.path.basename(filename)
            else:
                os.makedirs(target_dir, exist_ok=True)
                safe_path = target_dir / os.path.basename(filename)
        else:
            # No path provided - use screenshots dir
            safe_path = screenshots_dir / os.path.basename(filename)

        screenshot.save(safe_path)

        if ENCRYPTION_AVAILABLE:
            try:
                secure_channel.sign_command(f"screenshot:{safe_path}", user_id)
            except Exception:
                pass

        return f"Screenshot saved to: {safe_path}"
    except Exception as e:
        log_audit(user_id, "take_screenshot", {"filename": filename}, f"error:{e}")
        return f"Error taking screenshot: {e}"

def get_clipboard(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "get_clipboard", {}, "started")
    try:
        content = pyperclip.paste()
        
        if ENCRYPTION_AVAILABLE and len(content) > 0:
            if len(content) > 1000:
                content = content[:1000] + "... [truncated for security]"  # type: ignore  # pyre-ignore
            content = secure_channel.encrypt(content)
            return f"[ENCRYPTED]{content}"
        return content
    except Exception as e:
        return f"Error reading clipboard: {e}"

def set_clipboard(text: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "set_clipboard", {"length": len(text)}, "started")
    try:
        if ENCRYPTION_AVAILABLE and text.startswith("[ENCRYPTED]"):  # type: ignore  # pyre-ignore
            text = secure_channel.decrypt(text[11:])  # type: ignore  # pyre-ignore
            if not text:
                return "Decryption failed"
        
        pyperclip.copy(text)
        return "Clipboard updated successfully."
    except Exception as e:
        return f"Error writing to clipboard: {e}"

def open_website(url: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "open_website", {"url": url}, "started")
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        blocked_domains = {'malware', 'phishing', '.onion'}
        url_lower = url.lower()
        for blocked in blocked_domains:
            if blocked in url_lower:
                log_audit(user_id, "open_website", {"url": url}, "blocked")
                return f"URL blocked for security: {blocked} detected"
        
        webbrowser.open(url)
        return f"Opening {url}..."
    except Exception as e:
        return f"Error opening website: {e}"

def search_google(query: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "search_google", {"query": query[:50]}, "started")  # type: ignore  # pyre-ignore
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for g in soup.find_all('div', class_='tF2Cxc'):
            title_elem = g.find('h3')
            link_elem = g.find('a')
            
            if title_elem and link_elem:
                title = title_elem.text[:100]  # type: ignore  # pyre-ignore
                link = link_elem.get('href', '')
                results.append(f"🔍 {title}\n🔗 {link}")
            if len(results) >= 5:
                break
        
        if not results:
            return "No results found."
        return "\n\n".join(results)
    except Exception as e:
        return f"Error searching Google: {e}"

def get_running_processes(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "get_running_processes", {}, "started")
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):  # type: ignore  # pyre-ignore
            try:
                info = proc.info
                if info['name'] and validate_process_name(info['name']):  # type: ignore  # pyre-ignore
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:15]  # type: ignore  # pyre-ignore
        
        lines = ["🚀 **Top Running Processes:**\n"]  # type: ignore  # pyre-ignore
        lines.append(f"{'Name':<25} {'PID':<8} {'CPU%':<8} {'RAM%':<8}")
        lines.append("-" * 55)
        
        for p in processes:
            name = p['name'][:23] if p['name'] else "Unknown"  # type: ignore  # pyre-ignore
            pid = p['pid']
            cpu = f"{p.get('cpu_percent', 0):.1f}"
            mem = f"{p.get('memory_percent', 0):.1f}"
            lines.append(f"⚙️ {name:<23} {pid:<8} {cpu:<8} {mem:<8}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing processes: {e}"

# Critical system processes that should never be killed
CRITICAL_PROCESSES = {
    "svchost.exe", "csrss.exe", "smss.exe", "services.exe", "lsass.exe",
    "wininit.exe", "winlogon.exe", "dwm.exe", "system", "system idle process",
    "registry", "kernel", "memory compression", "crss.exe", "explorer.exe",
    "taskmgr.exe", "taskhostw.exe", "sihost.exe", "fontdrvhost.exe"
}

def kill_process(process_name: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "kill_process", {"name": process_name}, "started")

    if not process_name:
        return "No process name provided."

    process_lower = process_name.lower().strip()

    # Check if it's a critical system process
    if process_lower in CRITICAL_PROCESSES:
        log_audit(user_id, "kill_process", {"name": process_name}, "blocked_critical")
        return f"Cannot terminate critical system process: {process_name}"

    if not validate_process_name(process_name):
        log_audit(user_id, "kill_process", {"name": process_name}, "blocked")
        return f"Cannot terminate system process: {process_name}"

    if ENCRYPTION_AVAILABLE:
        if not secure_channel.check_rate_limit(user_id, "kill_process", max_calls=5, window=60):
            return "Rate limit exceeded. Max 5 process kills per minute."

    try:
        killed_count: int = 0
        errors = []
        for proc in psutil.process_iter(['name', 'pid']):  # type: ignore  # pyre-ignore
            try:
                if proc.info['name'].lower() == process_lower:  # type: ignore  # pyre-ignore
                    try:
                        proc.kill()
                        killed_count += 1  # type: ignore  # pyre-ignore
                    except psutil.AccessDenied:
                        errors.append(f"Access denied for PID {proc.info['pid']}")  # type: ignore  # pyre-ignore
                    except psutil.NoSuchProcess:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                pass

        if killed_count > 0:
            log_audit(user_id, "kill_process", {"name": process_name}, f"killed:{killed_count}")
            return f"Terminated {killed_count} instance(s) of {process_name}."
        if errors:
            return f"Process found but could not terminate: {', '.join(errors[:3])}"  # pyre-ignore
        return f"Process '{process_name}' not found."
    except Exception as e:
        return f"Error terminating process: {e}"

def manage_file(action: str, filename: str, content: Optional[str] = None, allowed_dir: str = "./files_safe", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "manage_file", {"action": action, "filename": filename}, "started")
    
    from config import SETTINGS  # type: ignore  # pyre-ignore
    allow_unsafe = SETTINGS.allow_unsafe_file_ops

    if allow_unsafe and os.path.isabs(filename):
        safe_path = filename
    elif ENCRYPTION_AVAILABLE:
        valid, result = encrypted_commands.validate_file_operation(filename, allowed_dir)
        if not valid:
            log_audit(user_id, "manage_file", {"action": action, "filename": filename}, "blocked")
            return f"Security blocked: {result}"
        safe_path = result
    else:
        safe_path = sanitize_path(filename, allowed_dir)
        if not safe_path:
            return "Invalid path - path traversal detected."
    
    os.makedirs(allowed_dir, exist_ok=True)

    try:
        if action == "create":
            data = content or ""
            if ENCRYPTION_AVAILABLE and isinstance(data, str) and data.startswith("[ENCRYPTED]"):  # type: ignore  # pyre-ignore
                decrypted = secure_channel.decrypt(data[len("[ENCRYPTED]"):])  # type: ignore  # pyre-ignore
                if decrypted is None:
                    return "Decryption failed"
                data = decrypted
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(data)
            log_audit(user_id, "manage_file", {"action": action, "filename": filename}, "ok")
            return f"File '{os.path.basename(filename)}' created in {allowed_dir}."

        if action == "read":
            if not os.path.exists(safe_path):
                return "File not found."
            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
            if ENCRYPTION_AVAILABLE and data:
                encrypted = secure_channel.encrypt(data[:5000])  # type: ignore  # pyre-ignore
                return f"[ENCRYPTED]{encrypted}"
            return data[:5000] + ("... [truncated]" if len(data) > 5000 else "")  # type: ignore  # pyre-ignore

        if action == "delete":
            if os.path.exists(safe_path):
                os.remove(str(safe_path))  # type: ignore  # pyre-ignore
                log_audit(user_id, "manage_file", {"action": action, "filename": filename}, "ok")
                return f"File '{os.path.basename(filename)}' deleted."
            return "File not found."

        return "Invalid action."

    except Exception as e:
        log_audit(user_id, "manage_file", {"action": action, "filename": filename}, f"error:{e}")
        return f"Error managing file: {e}"


def summarize_user_activity(user_id: str = "unknown", days: int = 1) -> str:  # type: ignore  # pyre-ignore
    if not os.path.exists(AUDIT_LOG_FILE):
        return "No activity log found yet."
    try:
        cutoff = datetime.now().timestamp() - max(1, days) * 86400
        op_counter = Counter()
        websites: list[str] = []  # type: ignore  # pyre-ignore
        commands: list[str] = []  # type: ignore  # pyre-ignore
        files: list[str] = []  # type: ignore  # pyre-ignore
        lines_scanned = 0

        with open(AUDIT_LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                lines_scanned += 1
                if f"USER:{user_id}" not in line:
                    continue
                if not line.startswith("["):
                    continue
                try:
                    ts_end = line.index("]")
                    ts = datetime.fromisoformat(line[1:ts_end]).timestamp()  # type: ignore  # pyre-ignore
                except Exception:
                    continue
                if ts < cutoff:
                    continue
                op_marker = " OP:"
                args_marker = " ARGS:"
                result_marker = " RESULT:"
                if op_marker not in line or args_marker not in line:
                    continue
                op = line.split(op_marker, 1)[1].split(args_marker, 1)[0].strip()
                args_raw = line.split(args_marker, 1)[1].split(result_marker, 1)[0].strip()
                try:
                    args_dict = ast.literal_eval(args_raw) if args_raw else {}
                    if not isinstance(args_dict, dict):
                        args_dict = {}
                except Exception:
                    args_dict = {}
                op_counter[op] += 1
                if op == "open_website" and isinstance(args_dict.get("url"), str):
                    websites.append(args_dict["url"])
                if op == "execute_cmd" and isinstance(args_dict.get("command"), str):
                    commands.append(args_dict["command"])
                if op == "manage_file" and isinstance(args_dict.get("filename"), str):
                    files.append(args_dict["filename"])

        if sum(op_counter.values()) == 0:
            return "No tracked actions in the selected period."

        top_ops = ", ".join([f"{k}({v})" for k, v in op_counter.most_common(6)])
        unique_sites = list(dict.fromkeys(websites))[:8]  # type: ignore  # pyre-ignore
        unique_cmds = list(dict.fromkeys(commands))[:5]  # type: ignore  # pyre-ignore
        unique_files = list(dict.fromkeys(files))[:8]  # type: ignore  # pyre-ignore
        parts = [
            f"Daily activity summary ({days} day):",
            f"- Actions: {sum(op_counter.values())}",
            f"- Most used: {top_ops}",
        ]
        if unique_sites:
            parts.append(f"- Websites visited via Nova: {', '.join(unique_sites)}")
        if unique_cmds:
            parts.append(f"- Commands run: {' | '.join(unique_cmds)}")
        if unique_files:
            parts.append(f"- Files touched: {', '.join(unique_files)}")
        parts.append(f"- Log lines scanned: {lines_scanned}")
        return "\n".join(parts)
    except Exception:
        return "Could not summarize activity right now."


# Common app name mappings for easier launching
COMMON_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "vscode": "code",
    "code": "code",
    "visual studio code": "code",
    "notepad": "notepad",
    "calc": "calc",
    "calculator": "calc",
    "spotify": "spotify",
    "discord": "discord",
    "steam": "steam",
    "explorer": "explorer",
    "file explorer": "explorer",
    "cmd": "cmd",
    "terminal": "wt" if platform.system() == "Windows" else "terminal",
    "powershell": "powershell",
    "task manager": "taskmgr",
}

def open_app(app_name: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "open_app", {"app_name": app_name}, "started")

    if not app_name:
        return "No app name provided."

    # Normalize app name
    app_lower = app_name.lower().strip()
    resolved_name = COMMON_APPS.get(app_lower, app_name)

    if not validate_process_name(resolved_name):
        log_audit(user_id, "open_app", {"app_name": resolved_name}, "blocked")
        return f"Blocked for security: {resolved_name}"

    try:
        system = platform.system()
        if system == "Windows":
            # Use start command which handles various app types well
            CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            subprocess.Popen(["cmd", "/c", "start", "", resolved_name], shell=False, creationflags=CREATE_NO_WINDOW)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", resolved_name], shell=False)
        else:
            subprocess.Popen([resolved_name], shell=False)
        log_audit(user_id, "open_app", {"app_name": resolved_name}, "ok")
        return f"Opening {resolved_name}..."
    except Exception as e:
        log_audit(user_id, "open_app", {"app_name": resolved_name}, f"error:{e}")
        return f"Error opening {resolved_name}: {e}"


def get_system_stats(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "get_system_stats", {}, "started")
    try:
        cpu_usage = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        return (
            "🖥️ **System Stats**\n"
            f"CPU Usage: {cpu_usage}%\n"
            f"RAM Usage: {ram.percent}% ({ram.used // (1024*1024)}MB / {ram.total // (1024*1024)}MB)\n"
            f"Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)"
        )
    except Exception as e:
        return f"Error retrieving stats: {e}"


def list_files(path: str = ".", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "list_files", {"path": path}, "started")
    try:
        if not os.path.exists(path):
            return f"Path '{path}' does not exist."
        files = os.listdir(path)
        if not files:
            return f"Directory '{path}' is empty."
        shown = files[:30]  # type: ignore  # pyre-ignore
        lines = []
        for f in shown:
            full = os.path.join(path, f)
            lines.append(("📄 " if os.path.isfile(full) else "📁 ") + f)
        if len(files) > 30:
            lines.append(f"...and {len(files) - 30} more.")
        return f"📂 **Files in {path}:**\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing files: {e}"


def run_script(script_path: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "run_script", {"script_path": script_path}, "started")
    try:
        if not os.path.exists(script_path):
            return f"Script path '{script_path}' not found."

        ext = os.path.splitext(script_path)[1].lower()
        if ext != ".py":
            return f"Blocked: only .py scripts are allowed (got {ext})."

        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            out = (result.stdout or "").strip()
            return out if out else "Script executed successfully."
        err = (result.stderr or "").strip()
        return err if err else f"Script failed (exit {result.returncode})."
    except subprocess.TimeoutExpired:
        return "Script timed out (60s limit)."
    except Exception as e:
        return f"Error running script: {e}"


def execute_cmd(command: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "execute_cmd", {"command": command[:50]}, "started")  # type: ignore  # pyre-ignore
    
    # More specific blocked patterns - must match as complete commands, not substrings
    dangerous_patterns = ["del *", "rm -rf /", "format c:", "shutdown /s", "shutdown -s", "icacls * /deny"]
    command_lower = command.lower().strip()

    # Block obviously dangerous operations but allow safe commands
    if command_lower.startswith(("del ", "del\\", "rmdir /s ", "rd /s ")) and ("*" in command_lower or "\\" in command_lower):
        log_audit(user_id, "execute_cmd", {"command": command[:50]}, "blocked")  # type: ignore  # pyre-ignore
        return "Command blocked: Mass deletion commands are restricted for safety."

    if command_lower.startswith(("format ", "format\\")):
        log_audit(user_id, "execute_cmd", {"command": command[:50]}, "blocked")  # type: ignore  # pyre-ignore
        return "Command blocked: Disk formatting is not allowed."

    if command_lower.startswith(("shutdown", "reboot", "restart-computer")):
        log_audit(user_id, "execute_cmd", {"command": command[:50]}, "blocked")  # type: ignore  # pyre-ignore
        return "Command blocked: System shutdown/restart commands are not allowed."
    
    if ENCRYPTION_AVAILABLE:
        if not secure_channel.check_rate_limit(user_id, "execute_cmd", max_calls=5, window=60):
            return "Rate limit exceeded. Max 5 commands per minute."
    
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        log_audit(user_id, "execute_cmd", {"command": command[:50]}, f"exit:{result.returncode}")  # type: ignore  # pyre-ignore
        
        if result.returncode == 0:
            output = result.stdout[:3000] if result.stdout else "Command executed successfully."  # type: ignore  # pyre-ignore
            return f"**Output:**\n{output}"
        else:
            error = result.stderr[:1000] if result.stderr else "Unknown error"  # type: ignore  # pyre-ignore
            return f"**Error:**\n{error}"
    except subprocess.TimeoutExpired:
        return "Command timed out (30s limit)."
    except Exception as e:
        return f"Command failed: {e}"

def check_pc_health():
    """
    Performs a comprehensive PC health check including resource usage and antivirus status (on Windows).
    """
    health_report = ["🏥 **PC Health Check Report**\n"]
    
    # Check CPU
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 85:
        health_report.append(f"⚠️ **CPU:** High usage ({cpu_usage}%). Consider closing heavy applications.")
    else:
        health_report.append(f"✅ **CPU:** Normal ({cpu_usage}%)")
        
    # Check RAM
    ram = psutil.virtual_memory()
    if ram.percent > 85:
        health_report.append(f"⚠️ **RAM:** High usage ({ram.percent}%). Memory is nearly full.")
    else:
        health_report.append(f"✅ **RAM:** Normal ({ram.percent}%)")
        
    # Check Disk
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    if disk.percent > 90:
        health_report.append(f"⚠️ **Disk:** critically low space on root drive ({disk.percent}% used).")
    else:
        health_report.append(f"✅ **Disk:** Healthy ({disk.percent}% used)")
        
    # Check Antivirus (Windows only)
    if platform.system() == "Windows":
        try:
            # Using WMIC to query Security Center for Antivirus product
            cmd = 'wmic /namespace:\\\\root\\SecurityCenter2 path AntiVirusProduct get displayName /value'
            CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and line.strip() != 'displayName']
            if lines:
                av_names = ", ".join(lines)
                health_report.append(f"🛡️ **Antivirus:** Detected ({av_names})")
            else:
                health_report.append("⚠️ **Antivirus:** No active antivirus detected by Windows Security Center.")
        except Exception:
            health_report.append("❓ **Antivirus:** Could not verify antivirus status.")
            
    return "\n".join(health_report)

USER_FACTS_FILE = "user_facts.json"

def load_user_facts() -> dict:  # type: ignore  # pyre-ignore
    if os.path.exists(USER_FACTS_FILE):
        try:
            with open(USER_FACTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_facts(facts: dict):
    with open(USER_FACTS_FILE, 'w') as f:
        json.dump(facts, f, indent=2)

def get_user_facts() -> str:  # type: ignore  # pyre-ignore
    """Retrieves all saved facts about the user."""
    try:
        facts = load_user_facts()
        all_facts = []
        for uid, user_facts in facts.items():
            all_facts.extend(user_facts)
        
        if all_facts:
            return "User Profile / Facts:\n" + "\n".join([f"- {fact}" for fact in set(all_facts)])  # type: ignore  # pyre-ignore
        return "No facts remembered yet."
    except Exception as e:
        return f"Error reading facts: {e}"

def get_weather(city: str) -> str:  # type: ignore  # pyre-ignore
    """Fetches the current weather for a given city using OpenWeather API."""
    from config import SETTINGS  # type: ignore  # pyre-ignore
    api_key = SETTINGS.openweather_api_key
    
    if not api_key:
        return "Error: OpenWeather API key is not configured in the .env file."
        
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            desc = data['weather'][0]['description']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            
            return (
                f"Weather in {city.title()}:\n"
                f"Condition: {desc.capitalize()}\n"
                f"Temperature: {temp}°C (Feels like {feels_like}°C)\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind_speed} m/s"
            )
        elif response.status_code == 404:
            return f"City '{city}' not found. Please check the spelling."
        else:
            return f"Failed to fetch weather. API returned status code {response.status_code}."
    except requests.exceptions.RequestException as e:
        return f"Network error while fetching weather: {e}"
    except Exception as e:
        return f"Error processing weather data: {e}"

def remember_user_fact(fact: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    log_audit(user_id, "remember_user_fact", {"fact": fact[:50]}, "started")  # type: ignore  # pyre-ignore
    try:
        facts = load_user_facts()
        if user_id not in facts:
            facts[user_id] = []
        facts[user_id].append(fact)
        
        if len(facts[user_id]) > 50:  # type: ignore  # pyre-ignore
            facts[user_id] = facts[user_id][-50:]  # type: ignore  # pyre-ignore
        
        save_user_facts(facts)
        return f"Got it! I'll remember: {fact}"
    except Exception as e:
        return f"Error saving fact: {e}"

# Optional News module integration (kept optional so missing deps don't break the bot)
try:
    from news_module import (  # type: ignore  # type: ignore  # pyre-ignore
        get_gaming_news,
        get_news,
        get_science_news,
        get_tech_news,
        get_trending_news,
        search_news,
    )

    NEWS_MODULE_AVAILABLE = True
except Exception:
    NEWS_MODULE_AVAILABLE = False


def check_news(category: str = "general", limit: int = 5, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not NEWS_MODULE_AVAILABLE:
        return "News module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_news(category, limit, user_id))


def search_news_topic(query: str, limit: int = 5, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not NEWS_MODULE_AVAILABLE:
        return "News module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(search_news(query, limit, user_id))


def get_trending(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not NEWS_MODULE_AVAILABLE:
        return "News module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_trending_news(user_id))


def get_tech(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not NEWS_MODULE_AVAILABLE:
        return "News module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_tech_news(5, user_id))


def get_science(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not NEWS_MODULE_AVAILABLE:
        return "News module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_science_news(5, user_id))


def get_gaming(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not NEWS_MODULE_AVAILABLE:
        return "News module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_gaming_news(5, user_id))


# Optional Exchange module integration (kept optional so missing deps don't break the bot)
try:
    from exchange_module import (  # type: ignore  # type: ignore  # pyre-ignore
        get_exchange_rate,
        convert_currency,
        get_rates,
        get_crypto,
    )

    EXCHANGE_MODULE_AVAILABLE = True
except Exception:
    EXCHANGE_MODULE_AVAILABLE = False


def check_exchange_rate(from_curr: str, to_curr: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not EXCHANGE_MODULE_AVAILABLE:
        return "Exchange module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_exchange_rate(from_curr, to_curr, user_id))


def convert_money(amount: float, from_curr: str, to_curr: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not EXCHANGE_MODULE_AVAILABLE:
        return "Exchange module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(convert_currency(amount, from_curr, to_curr, user_id))


def get_all_rates(base: str = "USD", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not EXCHANGE_MODULE_AVAILABLE:
        return "Exchange module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_rates(base, user_id))


def check_crypto(crypto: str, currency: str = "USD", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not EXCHANGE_MODULE_AVAILABLE:
        return "Exchange module unavailable (optional dependency missing)."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_crypto(crypto, currency, user_id))


# Optional Skills module integration
try:
    from skills_module import (  # type: ignore  # type: ignore  # pyre-ignore
        tell_joke,
        get_quote,
        get_fun_fact,
        calculate,
        roll_dice,
        flip_coin,
        generate_password,
        play_rps,
        analyze_sentiment,
    )

    SKILLS_MODULE_AVAILABLE = True
except Exception:
    SKILLS_MODULE_AVAILABLE = False


def get_joke(category: str = "any", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(tell_joke(category, user_id))


def get_inspirational_quote(category: str = "inspirational", user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_quote(category, user_id))


def get_random_fact(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(get_fun_fact(user_id))


def do_calculation(expression: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(calculate(expression, user_id))


def roll_the_dice(sides: int = 6, count: int = 1, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(roll_dice(sides, count, user_id))


def flip_the_coin(user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(flip_coin(user_id))


def create_password(length: int = 16, include_symbols: bool = True, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(generate_password(length, include_symbols, user_id))


def play_rock_paper_scissors(choice: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(play_rps(choice, user_id))


def analyze_mood(text: str, user_id: str = "unknown") -> str:  # type: ignore  # pyre-ignore
    if not SKILLS_MODULE_AVAILABLE:
        return "Skills module unavailable."
    import asyncio  # type: ignore  # pyre-ignore

    return asyncio.run(analyze_sentiment(text, user_id))

