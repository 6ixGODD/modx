from __future__ import annotations

import datetime
import typing as t

import pydantic as pydt

import modx.exceptions as exc
from modx.value_obj import BaseValueObject


class Birthday(BaseValueObject):
    date: datetime.date

    @pydt.field_validator('date', mode='before')
    @classmethod
    def validate_date(cls, v: object) -> datetime.date:
        if isinstance(v, str):
            try:
                return datetime.date.fromisoformat(v)
            except ValueError:
                raise exc.InvalidParametersError(
                    f"Invalid date format: {v}. Expected ISO format ("
                    f"YYYY-MM-DDThh:mm:ss)."
                )

        if isinstance(v, datetime.date):
            # Ensure earlier than current time
            if v > datetime.datetime.now():
                raise exc.InvalidParametersError(
                    f"Date {v} cannot be in the future. "
                    "Please provide a date earlier than the current time."
                )
            # Ensure not too far in the past
            if v < datetime.date(1900, 1, 1):
                raise exc.InvalidParametersError(
                    f"Date {v} is too far in the past. "
                    "Please provide a date after January 1, 1900."
                )
            return v
        else:
            raise exc.InvalidParametersError(
                "date must be a datetime object or an ISO format string."
            )

    @classmethod
    def from_date(cls, date: datetime.date) -> Birthday:
        return cls(date=datetime.date(date.year, date.month, date.day))

    @classmethod
    def from_iso(cls, iso_date: str) -> Birthday:
        return cls(date=datetime.date.fromisoformat(iso_date))

    @property
    def age(self) -> int:
        today = datetime.datetime.now()
        age = today.year - self.date.year
        if (today.month, today.day) < (self.date.month, self.date.day):
            age -= 1
        return age


class OptionalTimeRange(BaseValueObject):
    start_time: datetime.datetime | None = None
    end_time: datetime.datetime | None = None

    @pydt.model_validator(mode='after')
    def check_time_range(self) -> t.Self:
        if (
            self.start_time
            and self.end_time
            and self.start_time > self.end_time
        ):
            raise exc.InvalidParametersError(
                "Invalid time range",
                params={
                    "start_time": "start_time must be less than end_time",
                    "end_time": "end_time must be greater than start_time"
                }
            )
        return self


class TimeRange(BaseValueObject):
    start_time: datetime.datetime
    end_time: datetime.datetime

    @pydt.model_validator(mode='after')
    def check_time_range(self) -> t.Self:
        if self.start_time > self.end_time:
            raise exc.InvalidParametersError(
                "Invalid time range",
                params={
                    "start_time": "start_time must be less than end_time",
                    "end_time": "end_time must be greater than start_time"
                }
            )
        return self


class OptionalTimeRangISO(BaseValueObject):
    start_time: str | None = None
    end_time: str | None = None

    def to_optional_time_range(self) -> OptionalTimeRange:
        """Convert ISO8601 strings to OptionalTimeRange."""
        start = (
            datetime.datetime.fromisoformat(self.start_time)
            if self.start_time else None
        )
        end = (
            datetime.datetime.fromisoformat(self.end_time)
            if self.end_time else None
        )
        return OptionalTimeRange(start_time=start, end_time=end)


class TimeRangeISO(BaseValueObject):
    start_time: str
    end_time: str

    def to_time_range(self) -> TimeRange:
        """Convert ISO8601 strings to TimeRange."""
        start = datetime.datetime.fromisoformat(self.start_time)
        end = datetime.datetime.fromisoformat(self.end_time)
        return TimeRange(start_time=start, end_time=end)
