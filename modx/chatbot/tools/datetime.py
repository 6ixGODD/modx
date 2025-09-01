from __future__ import annotations

import typing_extensions as te

from modx.chatbot.tools import BaseTool


class Date(te.TypedDict):
    year: int
    month: int
    day: int


class Time(te.TypedDict):
    hour: int
    minute: int
    second: int


class DateTime(te.TypedDict):
    date: Date
    time: Time


class GetCurrentDateTime(BaseTool):
    __function_description__ = 'Get the current date and time in UTC.'

    def __call__(self) -> DateTime:
        pass
