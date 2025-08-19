import os
import time
import threading
import sys
import json
import ctypes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pystray
from PIL import Image
import tkinter as tk
from tkinter import messagebox, filedialog

def get_config_path():
    app_data = os.getenv("APPDATA")  # C:\Users\<User>\AppData\Roaming
    app_folder = os.path.join(app_data, "FolderMonitor")
    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, "config.json")

CONFIG_FILE = get_config_path()

class BatchFileHandler(FileSystemEventHandler):
    def __init__(self, alert_callback):
        super().__init__()
        self.alert_callback = alert_callback
        self.batch_prefix = None
        self.batch_count = 0
        self.timer_thread = None
        self.lock = threading.Lock()

    def start_timer(self):
        time.sleep(12)
        with self.lock:
            if self.batch_prefix is not None and self.batch_count != 7:
                self.alert_callback(self.batch_prefix, self.batch_count)
            self.batch_prefix = None
            self.batch_count = 0
            self.timer_thread = None

    def on_created(self, event):
        if event.is_directory:
            return

        file_name = os.path.basename(event.src_path)

        if "calibration" in file_name.lower():
            return

        prefix = file_name[:10]

        with self.lock:
            if self.batch_prefix is None:
                self.batch_prefix = prefix
                self.batch_count = 1
                self.timer_thread = threading.Thread(target=self.start_timer, daemon=True)
                self.timer_thread.start()
            elif prefix == self.batch_prefix:
                self.batch_count += 1
            else:
                self.batch_prefix = prefix
                self.batch_count = 1
                if self.timer_thread is None:
                    self.timer_thread = threading.Thread(target=self.start_timer, daemon=True)
                    self.timer_thread.start()

def windows_popup(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)

def alert_user(prefix, count):
    show_alert("Batch Incomplete", f"{count} file(s) with prefix '{prefix}' created. Please check the folder.")

def show_alert(title, message):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    messagebox.showwarning(title, message, parent=root)
    root.destroy()

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def create_image():
    logo_path = resource_path("logo.ico")
    return Image.open(logo_path)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

class FolderMonitorApp:
    def __init__(self):
        self.config = load_config()
        self.observer = None
        self.icon = pystray.Icon("Folder Monitor", create_image(), "Folder Monitor")
        self.icon.menu = pystray.Menu(
            pystray.MenuItem("Set Folder", self.set_folder),
            pystray.MenuItem("Exit", self.exit_app)
        )

    def run_monitor(self):
        folder = self.config.get("folder", "")
        if not folder or not os.path.isdir(folder):
            windows_popup("Error", f"No valid folder selected.")
            return

        handler = BatchFileHandler(alert_user)
        self.observer = Observer()
        self.observer.schedule(handler, folder, recursive=True)
        self.observer.start()
        windows_popup("Folder Monitor Running", f"Monitoring {folder}\n\nRight-click tray icon to change folder or exit.")

    def set_folder(self, icon, item):
        threading.Thread(target=self._select_folder, daemon=True).start()

    def _select_folder(self):
        root = tk.Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Select Folder to Monitor")
        root.destroy()
        if folder:
            self.stop_observer()
            self.config["folder"] = folder
            save_config(self.config)
            self.run_monitor()

    def stop_observer(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def exit_app(self, icon, item):
        self.stop_observer()
        self.icon.stop()

    def run(self):
        self.run_monitor()
        self.icon.run()

if __name__ == "__main__":
    app = FolderMonitorApp()
    app.run()
