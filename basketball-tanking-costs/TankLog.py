"""
TankLog.py

A lightweight, multi-level logging utility for the NBA analytics project.
Supports console and file-based logging with thread-aware formatting,
timestamping, and modular control over log verbosity.

Classes:
    - TankLog: Configurable logger with level-based filtering and optional file output.

Logging Levels:
    Supports a variety of flags (INFO_LOGGING, WARNING_LOGGING, SQL_LOGGING, etc.)
    that can be toggled via the `enabled_levels` bitmask.

Static Access:
    - get_console_logger(): Console-only logger
    - get_file_logger(): File logger (also echoes to console)
    - get_shared_logger(): Shared singleton logger for app-wide use

Example:
    log = TankLog.get_shared_logger()
    log.log(TankLog.WARNING_LOGGING, "This is a warning!", __file__, "main", 42)
"""

# === Standard Library Imports ===
import os
import threading
import datetime

# === Local Application Imports ===
from Paths import FILE_PATH_TO_LOG


class TankLog:
    # Logging levels
    INFO_LOGGING = 1
    EXECUTION_FLOW_LOGGING = 2
    API_LOGGING = 4
    SERIOUS_LOGGING = 8
    CONFIGURATION_LOGGING = 16
    WARNING_LOGGING = 32
    ERROR_LOGGING = 64
    ACTION_LOGGING = 128
    TIMER_LOGGING = 256
    UI_LOGGING = 512
    DATA_STORE_LOGGING = 1024
    BUILD_SUBMISSION_LOGGING = 2048
    UPDATE_LOGGING = 4096
    SQL_LOGGING = 8192
    RECORD_ENCODING_LOGGING = 16384

    # Enabled log levels
    enabled_levels = (
        SERIOUS_LOGGING | ERROR_LOGGING | WARNING_LOGGING |
        ACTION_LOGGING | UPDATE_LOGGING | EXECUTION_FLOW_LOGGING |
        SQL_LOGGING
    )

    def __init__(self, to_file=False, also_echo_to_console=True):
        self.to_file = to_file
        self.also_echo_to_console = also_echo_to_console
        self.log_file_path = self._default_log_file_path() if to_file else None

        if self.to_file:
            self._write_initial_log_message()

    def log(self, level, message, file=None, function=None, line=None):
        if not (level & TankLog.enabled_levels):
            return

        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            thread = threading.current_thread()
            thread_desc = f"{thread.name} (ident = {thread.ident})" if thread else "UnknownThread"

            source_info = f"[{os.path.basename(file)}:{line} {function}]" if file and function and line else ""
            formatted = f"[{timestamp}] [{thread_desc}] {source_info} {message}"

            if self.to_file and self.log_file_path:
                self._append_to_file(formatted)

            if not self.to_file or self.also_echo_to_console:
                print(formatted)

        except Exception as e:
            # Optional: Only if you want a fallback during shutdown, comment out if noisy
            print(f"[LOGGING ERROR] Logging failed during shutdown: {e}")

    def _append_to_file(self, msg):
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")

    def _write_initial_log_message(self):
        msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] Log file created: {self.log_file_path}"
        self._append_to_file(msg)
        if self.also_echo_to_console:
            print(msg)

    def _default_log_file_path(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.expanduser(FILE_PATH_TO_LOG)
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, f"tank_log_{now}.log")

    # Static singleton access
    @staticmethod
    def get_console_logger():
        if TankLog._console_logger is None:
            TankLog._console_logger = TankLog(to_file=False)
        return TankLog._console_logger

    @staticmethod
    def get_file_logger():
        if TankLog._file_logger is None:
            TankLog._file_logger = TankLog(to_file=True, also_echo_to_console=True)
        return TankLog._file_logger

    @staticmethod
    def get_shared_logger():
        if TankLog._shared_logger is None:
            TankLog._shared_logger = TankLog.get_file_logger()
        return TankLog._shared_logger

# Singleton instances for TankLog's loggers.
try:
    TankLog._console_logger
except AttributeError:
    TankLog._console_logger = None

try:
    TankLog._file_logger
except AttributeError:
    TankLog._file_logger = None

try:
    TankLog._shared_logger
except AttributeError:
    TankLog._shared_logger = None

# Example usage
if __name__ == "__main__":
    log = TankLog.get_shared_logger()
    log.log(TankLog.INFO_LOGGING, "Starting up! Won't appear though.", __file__, "main", 12)
    log.log(TankLog.WARNING_LOGGING, "Already started! This should print!", __file__, "main", 12)
