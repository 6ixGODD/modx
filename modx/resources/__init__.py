from __future__ import annotations

import abc
import pathlib as p
import threading
import typing as t

import watchdog.events as evt
import watchdog.observers as obsrv

from modx.helpers.mixin import LoggingTagMixin
from modx.logger import Logger


class FileHandler(evt.FileSystemEventHandler):
    def __init__(self, callback: t.Callable[[], None], fpath: p.Path):
        self.callback = callback
        self.fpath = fpath

    def on_modified(
        self,
        event: evt.FileModifiedEvent | evt.DirModifiedEvent
    ) -> None:
        if not event.is_directory and p.Path(event.src_path) == self.fpath:
            self.callback()


T = t.TypeVar('T')


class WatchedResource(abc.ABC, LoggingTagMixin, t.Generic[T]):
    def __init__(self, fpath: str | p.Path, logger: Logger):
        LoggingTagMixin.__init__(self, logger)
        self.fpath = p.Path(fpath)
        self.data: T | None = None
        self.backup: T | None = None
        self.lock = threading.RLock()
        self.observer: obsrv.Observer | None = None

        self.load()
        self.watch()

    @abc.abstractmethod
    def _parse(self) -> T:
        pass

    def load(self) -> None:
        try:
            with self.lock:
                data = self._parse()
                self.backup = self.data  # Backup current data
                self.data = data
                self.logger.info(f"Loaded data from file: {self.fpath}")
        except Exception as e:
            self.logger.error(
                f"Failed to load data from file: {self.fpath} - {e}",
            )
            if self.backup is not None:
                self.logger.info("Rolling back to previous data")
                self.data = self.backup

    def watch(self) -> None:
        if not self.fpath.exists():
            self.logger.warning(
                f"File does not exist: {self.fpath}, skipping watch"
            )
            return

        self.observer = obsrv.Observer()
        handler = FileHandler(self.load, self.fpath)
        self.observer.schedule(
            handler,
            str(self.fpath.parent),
            recursive=False
        )
        self.observer.start()
        self.logger.info(f"Monitoring file: {self.fpath}")

    def stop(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info(f"Stopped monitoring file: {self.fpath}")

    def __del__(self):
        self.stop()
