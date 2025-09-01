from __future__ import annotations

import argparse
import pathlib as p
import warnings

import dotenv

from modx import __version__


def parse_args() -> argparse.Namespace:
    import modx.cli.cmd.run as run

    parser = argparse.ArgumentParser(
        description='ModX Server Command Line Interface',
        prog='python -m modx',
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'%(prog)s {__version__}',
        help='Show the version of ModX',
    )
    parser.add_argument(
        '--env-file', '-e',
        type=str,
        default='.env',
        help='Path to the environment file (default: %(default)s)',
    )
    subparser = parser.add_subparsers(
        title='subcommands',
        description='Available subcommands',
        dest='command',
    )
    run.register(subparser)

    def _print_help(args_: argparse.Namespace) -> None:
        parser.print_help()
        if args_.command is None:
            print("\nPlease specify a subcommand. Use -h for help.")

    parser.set_defaults(func=_print_help)

    args = parser.parse_args()

    env_file = p.Path(args.env_file)
    if not env_file.exists():
        warnings.warn(
            f"Environment file '{env_file}' does not exist. Skipping loading "
            f"environment variables from this file.",
            UserWarning
        )

    dotenv.load_dotenv(env_file)

    return args
