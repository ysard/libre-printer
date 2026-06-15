"""

- OutputFileWatcher:
    Watch an output file and signal when it is ready for consumption.
- run_subprocess_wait_output_file:
    Run a subprocess and wait until the expected output file is ready.
"""

# Standard imports
from pathlib import Path
from threading import Event, Timer
from watchdog.events import FileSystemEventHandler
from watchdog.observers.inotify import InotifyObserver

# Custom imports
from libreprinter.commons import logger

LOGGER = logger()


class OutputFileWatcher(FileSystemEventHandler):
    """Watch an output file and signal when it is ready for consumption"""

    def __init__(self, processed_file: Path, ready_event: Event):
        """Initialise the handler for the expected output file"""
        self.processed_file = processed_file.resolve()
        self.ready_event = ready_event
        self.timer = None

    def _check(self):
        """Trigger the ready event if the output file exists and is not empty"""
        if self.processed_file.exists() and self.processed_file.stat().st_size > 0:
            self.ready_event.set()

    def on_modified(self, event):
        """Handle file modification events for the monitored output file"""
        if Path(event.src_path).resolve() != self.processed_file:
            return

        if self.timer:
            self.timer.cancel()

        # Handle the 4 seconds timeout for the legacy converters
        self.timer = Timer(4.0, self._ready)
        self.timer.start()

    def _ready(self):
        """Mark the output file as ready"""
        self.ready_event.set()

    def on_closed(self, event):
        """Handle file close events for the monitored output file"""
        if Path(event.src_path).resolve() == self.processed_file:
            self._check()


def run_subprocess_wait_output_file(
    tmp_process, processed_file, func_wrapper, timeout=14
):
    """Run a subprocess and wait until the expected output file is ready

    :raises TimeoutError: If the output file is not produced.

    :param tmp_process: (fixture) Process waiting a reimplementation of `run`.
    :param processed_file: The file the observer is waiting for.
    :param func_wrapper: Function executed in the subprocess.
    :key timeout: Maximum file waiting time.
    :type tmp_process: multiprocessing.Process
    :type processed_file: Path
    :type func_wrapper: Callable
    :type timeout: int | float
    :return: Only if the expected file is found by the observer.
    """
    # Observer
    ready = Event()
    observer = InotifyObserver()
    observer.schedule(
        OutputFileWatcher(processed_file, ready),
        path=str(processed_file.parent),
        recursive=False,
    )
    observer.start()

    try:
        # Interface engine
        tmp_process.run = func_wrapper
        tmp_process.start()
        LOGGER.debug("Process started")

        if not ready.wait(timeout=timeout):
            raise TimeoutError(f"{processed_file} was not produced")
    finally:
        observer.stop()
        observer.join()
        # PS: the subprocess is terminated in the fixture
