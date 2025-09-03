from __future__ import annotations

import traceback

from modx.cli import cmd, exceptions


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
    args = cmd.parse_args()
    args.func(args)
