from __future__ import annotations

import traceback

from modx.cli import commands, exceptions


def main() -> int:
    try:
        _main()
    except KeyboardInterrupt:
        return 130
    except exceptions.CLIException as e:
        traceback.print_exc()
        return e.exit_code
    except Exception:
        traceback.print_exc()
        return 1
    return 0


def _main() -> None:
    args = commands.parse_args()
    args.func(args)
