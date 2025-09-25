from __future__ import annotations

import datetime as dt
import os
import platform
import random
import types

import psutil
import pyfiglet
import rich.align as ralign
import rich.box as rbox
import rich.console as rconsole
import rich.panel as rpanel
import rich.table as rtable
import rich.text as rtext

from modx import __project__
from modx.config import ModXConfig


class Display:
    ASCII_FONTS = ['slant', 'doom', 'starwars', 'chunky', 'graffiti']

    ASCII_BORDERS = ["bold red", "bold green", "bold cyan", "bold yellow"]

    def __init__(self, config: ModXConfig):
        self.config = config
        self.console = rconsole.Console(width=100, highlight=False)
        self.startup_time = dt.datetime.now()

    def display_startup(self) -> None:
        self.clear()
        self._display_ascii_art()
        self._display_sysinfo()
        self._display_status()

    def display_shutdown(self,
                         exc_type: type[BaseException] | None = None,
                         exc_value: BaseException | None = None,
                         traceback: types.TracebackType | None = None) -> None:
        self.console.print("\n")
        self._display_shutdown_banner(exc_type, exc_value)
        if exc_value:
            self._display_exception_info(exc_type, exc_value, traceback)
        self._display_runtime_stats()
        self._display_goodbye_message(exc_value)

    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')

    def _display_ascii_art(self) -> None:
        font = random.choice(self.ASCII_FONTS)
        border_style = random.choice(self.ASCII_BORDERS)
        ascii_art = pyfiglet.figlet_format(__project__, font=font)

        self.console.print(
            rpanel.Panel(ralign.Align.center(rtext.Text(ascii_art, style="bright_white")),
                         border_style=border_style,
                         box=rbox.DOUBLE,
                         title=f'{self.config.server.appname} v'
                         f'{self.config.server.version}',
                         width=100,
                         padding=(0, 2),
                         title_align='center'))
        self.console.print("\n")

    def _display_sysinfo(self):
        sysinfo = rtable.Table(title='System Info', box=rbox.SQUARE, width=100)
        sysinfo.add_column('Component', style='white', width=20)
        sysinfo.add_column('Details', style='magenta', width=80)

        sysinfo.add_row('OS', platform.platform())
        sysinfo.add_row('Python', platform.python_version())
        sysinfo.add_row('CPU Cores', f"{psutil.cpu_count(logical=False)} / {psutil.cpu_count()}")
        sysinfo.add_row('CPU Usage', f"{psutil.cpu_percent(interval=1):.1f}%")
        mem = psutil.virtual_memory()
        sysinfo.add_row('Memory', f"{mem.percent:.1f}% used of {mem.total // (1024 ** 3)}GB")
        self.console.print(sysinfo)
        self.console.print("\n")

    def _display_status(self) -> None:
        route = (f"http://{self.config.server.http_host}:"
                 f"{self.config.server.http_port}"
                 f"{self.config.server.route_prefix}")
        self.console.print(
            rpanel.Panel(
                ralign.Align.center(rtext.Text(route, style="bold magenta")),
                title='🚀 Ready (probably)',
                border_style='green',
                box=rbox.SQUARE,
                width=100,
            ))

    def _display_shutdown_banner(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
    ) -> None:
        if exc_value:
            title, style, subtitle = ("💀 CRASHED", "red",
                                      f"{exc_type.__name__ if exc_type else 'Unknown'}")
        else:
            title, style, subtitle = "SHUTDOWN", "green", "寄了。"

        art = pyfiglet.figlet_format("BYE", font="small")
        self.console.print(
            rpanel.Panel(ralign.Align.center(rtext.Text(art, style="white")),
                         title=title,
                         subtitle=subtitle,
                         border_style=style,
                         box=rbox.HEAVY,
                         width=100))

    def _display_exception_info(self,
                                exc_type: type[BaseException] | None = None,
                                exc_value: BaseException | None = None,
                                _traceback: types.TracebackType | None = None) -> None:
        if not exc_value or isinstance(exc_value, KeyboardInterrupt):
            return
        txt = rtext.Text.assemble(("Exception: ", "bold red"),
                                  (exc_type.__name__ if exc_type else "Unknown", "red"), "\n",
                                  ("Message: ", "bold red"), (str(exc_value), "red"))
        self.console.print(
            rpanel.Panel(txt, title="💥 Exception", border_style="red", box=rbox.ASCII, width=100))

    def _display_runtime_stats(self) -> None:
        runtime = dt.datetime.now() - self.startup_time
        stats = rtable.Table(title='Runtime', box=rbox.ASCII, width=100)
        stats.add_column('Metric', style='white', width=25)
        stats.add_column('Value', style='cyan', width=70)
        stats.add_row('Uptime', str(runtime).split('.')[0])
        stats.add_row('Stopped At', dt.datetime.now().strftime('%H:%M:%S'))
        stats.add_row('CPU Usage', f"{psutil.cpu_percent():.1f}%")
        stats.add_row('Mem Usage', f"{psutil.virtual_memory().percent:.1f}%")
        self.console.print(stats)

    def _display_goodbye_message(self, exc_value: BaseException | None) -> None:
        if not exc_value:
            msg, style = "Server exited peacefully (this time).", "green"
        else:
            msg = random.choice(
                ["异常退出，不出所料。", "挂了。", "报错？习惯就好。", "崩了，但还能更糟。", "系统罢工，挺正常。", "寄了，但不意外。"])
            style = "grey70"
        self.console.print(
            rpanel.Panel(ralign.Align.center(rtext.Text(msg, style=f"bold {style}")),
                         border_style="blue",
                         box=rbox.MINIMAL,
                         width=100))
