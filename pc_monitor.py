# pyre-ignore-all-errors
"""
Advanced PC Monitoring Module for Lily
Tracks app usage, time spent, daily activities, and automatically takes notes
"""

import json
import os
import platform
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil  # pyre-ignore

# Database for tracking
MONITOR_DB = "pc_monitor.db"
monitor_lock = threading.Lock()


def init_monitor_db():
    """Initialize the monitoring database"""
    with sqlite3.connect(MONITOR_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                window_title TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                note TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activity_type TEXT NOT NULL,
                details TEXT
            )
        """)
        conn.commit()


def get_current_app() -> Dict[str, Any]:
    """Get the currently active application"""
    try:
        if platform.system() == "Windows":
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32  # pyre-ignore
            kernel32 = ctypes.windll.kernel32  # pyre-ignore

            # Get foreground window
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                # Get window title
                length = user32.GetWindowTextLengthW(hwnd)
                title_buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title_buffer, length + 1)
                window_title = title_buffer.value

                # Get process ID
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

                # Get process name
                try:
                    process = psutil.Process(pid.value)
                    app_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    app_name = "Unknown"

                return {
                    "app_name": app_name,
                    "window_title": window_title,
                    "pid": pid.value,
                    "timestamp": datetime.now().isoformat()
                }
    except Exception:
        pass
    return {"app_name": "Unknown", "window_title": "Unknown"}


def log_app_switch(app_name: str, window_title: str):
    """Log when user switches to a different app"""
    with monitor_lock:
        with sqlite3.connect(MONITOR_DB) as conn:
            cursor = conn.cursor()
            # Close previous app session
            cursor.execute("""
                UPDATE app_usage
                SET end_time = CURRENT_TIMESTAMP,
                    duration_seconds = CAST((julianday('now') - julianday(start_time)) * 24 * 60 * 60 AS INTEGER)
                WHERE end_time IS NULL
            """)
            # Start new app session
            cursor.execute("""
                INSERT INTO app_usage (app_name, window_title)
                VALUES (?, ?)
            """, (app_name, window_title))
            conn.commit()


def add_daily_note(note: str, category: str = "general"):
    """Add a note about user's day"""
    with monitor_lock:
        with sqlite3.connect(MONITOR_DB) as conn:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT INTO daily_notes (date, category, note)
                VALUES (?, ?, ?)
            """, (today, category, note))
            conn.commit()


def log_user_activity(activity_type: str, details: str = ""):
    """Log a user activity"""
    with monitor_lock:
        with sqlite3.connect(MONITOR_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_activity (activity_type, details)
                VALUES (?, ?)
            """, (activity_type, details))
            conn.commit()


def get_today_app_usage() -> List[Dict[str, Any]]:
    """Get today's app usage summary"""
    with sqlite3.connect(MONITOR_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT app_name, SUM(duration_seconds) as total_time,
                   COUNT(*) as sessions
            FROM app_usage
            WHERE date(start_time) = date('now')
            GROUP BY app_name
            ORDER BY total_time DESC
            LIMIT 20
        """)
        results = []
        for row in cursor.fetchall():
            app_name, total_seconds, sessions = row
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            results.append({
                "app_name": app_name,
                "time_spent": f"{hours}h {minutes}m",
                "total_seconds": total_seconds,
                "sessions": sessions
            })
        return results


def get_currently_active_app() -> str:
    """Get the currently active app info"""
    current = get_current_app()
    return f"Currently using: {current['app_name']} - {current['window_title'][:50]}"


def get_today_summary() -> str:
    """Get a summary of today's activities"""
    lines = ["📊 **Today's Activity Summary**\n"]

    # App usage
    app_usage = get_today_app_usage()
    if app_usage:
        lines.append("🖥️ **Apps you've used today:**")
        for app in app_usage[:10]:  # pyre-ignore
            lines.append(f"  • {app['app_name']}: {app['time_spent']}")
        lines.append("")
    else:
        lines.append("🖥️ No app usage tracked yet today\n")

    # Notes
    with sqlite3.connect(MONITOR_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, note, timestamp
            FROM daily_notes
            WHERE date = date('now')
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        notes = cursor.fetchall()
        if notes:
            lines.append("📝 **Today's Notes:**")
            for category, note, timestamp in notes:
                lines.append(f"  [{category}] {note}")
            lines.append("")

    # Recent activities
    cursor.execute("""
        SELECT activity_type, details, timestamp
        FROM user_activity
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    activities = cursor.fetchall()
    if activities:
        lines.append("📋 **Recent Activities:**")
        for activity_type, details, timestamp in activities:
            lines.append(f"  • {activity_type}: {details or 'N/A'}")

    return "\n".join(lines) if len(lines) > 1 else "No activities tracked yet today."


def get_time_spent_today() -> str:
    """Get total time spent on PC today"""
    with sqlite3.connect(MONITOR_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(duration_seconds) as total
            FROM app_usage
            WHERE date(start_time) = date('now')
        """)
        result = cursor.fetchone()
        total_seconds = result[0] or 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"⏰ You've been active for {hours} hours and {minutes} minutes today"


def get_top_apps_today(limit: int = 5) -> str:
    """Get top apps used today"""
    app_usage = get_today_app_usage()
    if not app_usage:
        return "No apps tracked yet today."

    lines = ["🔝 **Top Apps Today:**"]
    for i, app in enumerate(app_usage[:limit], 1):  # pyre-ignore
        lines.append(f"{i}. {app['app_name']} - {app['time_spent']}")
    return "\n".join(lines)


# Initialize database on import
init_monitor_db()
