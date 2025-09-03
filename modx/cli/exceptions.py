from __future__ import annotations

from modx import exceptions

class CLIException(exceptions.BootstrapException):
    exit_code = 1
