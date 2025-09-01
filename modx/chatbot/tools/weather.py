from __future__ import annotations

import typing as t

import typing_extensions as te

from modx.chatbot.tools import BaseTool, Property


class Weather(te.TypedDict, total=False):
    location: te.Required[str]
    temperature: float
    condition: str
    humidity: float
    wind_speed: float


class GetCurrentWeather(BaseTool):
    __function_description__ = 'Get the current weather for a given location.'

    def __init__(self):
        raise NotImplementedError

    def __call__(
        self,
        location: t.Annotated[
            str,
            Property(
                description="ISO 3166-2 code of the location to get the "
                            "weather for, e.g., 'US-CA' for California, USA.",
            )
        ]
    ) -> Weather:
        raise NotImplementedError(
            'This is a stub implementation. Replace with actual logic to '
            'fetch weather data.'
        )
