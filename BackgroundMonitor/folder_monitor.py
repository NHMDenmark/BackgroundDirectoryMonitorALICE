import os
import time
import threading
import sys
import ctypes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pystray
from PIL import Image

# Default folder to monitor
FOLDER_TO_MONITOR = r"C:/Users/tvs157/Desktop/ingestionTest/yup"

class BatchFileHandler(FileSystemEventHandler):
    def __init__(self, alert_callback):
        super().__init__()
        self.alert_callback = alert_callback
        self.batch_prefix = None
        self.batch_count = 0
        self.timer_thread = None
        self.lock = threading.Lock()

    def start_timer(self):
        time.sleep(5)
        with self.lock:
            if self.batch_prefix is not None and self.batch_count < 7:
                self.alert_callback(self.batch_prefix, self.batch_count)
            self.batch_prefix = None
            self.batch_count = 0
            self.timer_thread = None

    def on_created(self, event):
        if event.is_directory:
            return

        file_name = os.path.basename(event.src_path)

        # Skip files with "calibration" in the name
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
    windows_popup("Batch Incomplete", f"Only {count} file(s) with prefix '{prefix}' created. Please check the folder.")


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller EXE"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def create_image():
    logo_path = resource_path("logo.ico")
    return Image.open(logo_path)

def run_monitor():
    if not os.path.isdir(FOLDER_TO_MONITOR):
        windows_popup("Error", f"Folder does not exist:\n{FOLDER_TO_MONITOR}")
        sys.exit(1)

    windows_popup("Folder Monitor Running", f"Monitoring {FOLDER_TO_MONITOR}\n\nRight-click the logo in the icons tray -> exit to close program.")

    handler = BatchFileHandler(alert_user)
    observer = Observer()
    observer.schedule(handler, FOLDER_TO_MONITOR, recursive=True)
    observer.start()

    return observer

def on_exit(icon, item):
    icon.stop()

def main():

    observer = run_monitor()

    icon = pystray.Icon("Folder Monitor", create_image(), "Folder Monitor", menu=pystray.Menu(
        pystray.MenuItem("Exit", lambda icon, item: on_exit(icon, item))
    ))

    try:
        icon.run()
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()
