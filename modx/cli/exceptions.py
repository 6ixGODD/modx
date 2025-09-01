from __future__ import annotations

import modx.exceptions as exc


class CLIException(exc.BootstrapException):
    exit_code = 1
