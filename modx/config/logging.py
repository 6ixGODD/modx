from __future__ import annotations

import typing as t

import pydantic as pydt


class SizeBasedRotation(pydt.BaseModel):
    max_size: int = pydt.Field(default=10,
                               description="Maximum size (MB) of the log file before rotation")
    backup_count: int = pydt.Field(default=5, description="Number of backup files to keep")


class TimeBasedRotation(pydt.BaseModel):
    interval: int = pydt.Field(default=1, description="Interval in hours for log rotation")
    backup_count: int = pydt.Field(default=5, description="Number of backup files to keep")


class Rotation(pydt.BaseModel):
    size_based: SizeBasedRotation | None = pydt.Field(
        default=None, description="Configuration for size-based log rotation")
    time_based: TimeBasedRotation | None = pydt.Field(
        default=None, description="Configuration for time-based log rotation")

    @pydt.model_validator(mode='after')
    def validate_rotation_config(self) -> t.Self:
        if not self.size_based and not self.time_based:
            raise ValueError("At least one rotation configuration must be provided")

        if self.size_based and self.time_based:
            raise ValueError("Only one type of rotation configuration can be provided")

        return self


class LoggingTarget(pydt.BaseModel):
    logname: t.Literal['stdout', 'stderr'] | str = pydt.Field(
        default='stdout',
        description="Name of the target, can be 'stdout', 'stderr', "
        "or a file path")

    loglevel: t.Literal['debug', 'info', 'warning', 'error',
                        'critical'] = pydt.Field(default='info',
                                                 description="Log level for this target")

    rotation: Rotation | None = pydt.Field(default=None,
                                           description="Configuration for log rotation")


class LoggingConfig(pydt.BaseModel):
    backend: t.Literal['native', 'loguru'] = 'native'

    targets: t.List[LoggingTarget] = [
        LoggingTarget(logname='stdout', loglevel='debug'),
        LoggingTarget(logname='stderr', loglevel='error')
    ]

    extra_context: t.Dict[str, t.Any] = {}
