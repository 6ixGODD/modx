from __future__ import annotations

import traceback

import modx.cli.cmd as cmd
import modx.cli.exceptions as exc


def main() -> int:
    try:
        _main()
    except KeyboardInterrupt:
        return 130
    except exc.CLIException as e:
        traceback.print_exc()
        return e.exit_code
    except Exception:
        traceback.print_exc()
        return 1
    return 0


def _main() -> None:
    args = cmd.parse_args()
    args.func(args)
