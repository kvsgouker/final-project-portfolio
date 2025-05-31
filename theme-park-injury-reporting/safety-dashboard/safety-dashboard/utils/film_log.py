"""
FilmLog.py

A lightweight, multi-level logging utility for the NBA analytics project.
Supports console and file-based logging with thread-aware formatting,
timestamping, and modular control over log verbosity.

Classes:
    - FilmLog: Configurable logger with level-based filtering and optional file output.

Logging Levels:
    Supports a variety of flags (INFO_LOGGING, WARNING_LOGGING, SQL_LOGGING, etc.)
    that can be toggled via the `enabled_levels` bitmask.

Static Access:
    - get_console_logger(): Console-only logger
    - get_file_logger(): File logger (also echoes to console)
    - get_shared_logger(): Shared singleton logger for app-wide use

Example:
    log = FilmLog.get_shared_logger()
    log.log(FilmLog.WARNING_LOGGING, "This is a warning!", __file__, "main", 42)


Author: Kyle Salgado-Gouker

"""

# === Standard Library Imports ===
import os
import threading
import datetime

# === Local Application Imports ===
from access.paths import LOG_DIRECTORY


class FilmLog:
    # Logging levels
    INFO_LOGGING = 1
    EXECUTION_FLOW_LOGGING = 2
    ANALYSIS_LOGGING = 4
    ROTTEN_TOMATO_LOGGING = 8
    CONFIGURATION_LOGGING = 16
    WARNING_LOGGING = 32
    ERROR_LOGGING = 64
    ACTION_LOGGING = 128
    IMDB_LOGGING = 256
    UI_LOGGING = 512
    SQL_LOGGING = 1024
    MERGE_LOGGING = 2048
    BOX_OFFICE_MOJO_LOGGING = 4096
    CACHE_LOGGING = 8192
    CREDITS_LOGGING = 16384
    BRIDGE_LOGGING = 32768

    # Enabled log levels
    enabled_levels = (
        ERROR_LOGGING | WARNING_LOGGING | CACHE_LOGGING |  BRIDGE_LOGGING |
        ACTION_LOGGING | EXECUTION_FLOW_LOGGING | SQL_LOGGING
    )

    def __init__(self, to_file=False, also_echo_to_console=True):
        self.to_file = to_file
        self.also_echo_to_console = also_echo_to_console
        self.log_file_path = self._default_log_file_path() if to_file else None

        if self.to_file:
            self._write_initial_log_message()

    def log(self, level, message, file=None, function=None, line=None):
        if not (level & FilmLog.enabled_levels):
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
        log_dir = os.path.expanduser(LOG_DIRECTORY)
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, f"film_log_{now}.log")

    # Static singleton access
    @staticmethod
    def get_console_logger():
        if FilmLog._console_logger is None:
            FilmLog._console_logger = FilmLog(to_file=False)
        return FilmLog._console_logger

    @staticmethod
    def get_file_logger():
        if FilmLog._file_logger is None:
            FilmLog._file_logger = FilmLog(to_file=True, also_echo_to_console=True)
        return FilmLog._file_logger

    @staticmethod
    def get_shared_logger():
        if FilmLog._shared_logger is None:
            FilmLog._shared_logger = FilmLog.get_file_logger()
        return FilmLog._shared_logger

# Singleton instances for FilmLog's loggers.
try:
    FilmLog._console_logger
except AttributeError:
    FilmLog._console_logger = None

try:
    FilmLog._file_logger
except AttributeError:
    FilmLog._file_logger = None

try:
    FilmLog._shared_logger
except AttributeError:
    FilmLog._shared_logger = None

# Example usage
if __name__ == "__main__":
    log = FilmLog.get_shared_logger()
    log.log(FilmLog.INFO_LOGGING, "Starting up! Won't appear though.", __file__, "main", 12)
    log.log(FilmLog.WARNING_LOGGING, "Already started! This should print!", __file__, "main", 12)
