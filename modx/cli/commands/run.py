from __future__ import annotations

import argparse
import pathlib as p
import typing as t

from dependency_injector.wiring import inject, Provide

import modx.http.routers.compat
from modx import config
from modx.cli.helpers.args import BaseArgs
from modx.containers import Container
from modx.http import HTTPServer

if t.TYPE_CHECKING:
    from argparse import _SubParsersAction


class Args(BaseArgs):
    __slots__ = ('keys_file', 'models_file', 'config')
    _field_optional = {'keys_file', 'models_file', 'config'}

    keys_file: str | None
    models_file: str | None
    config: str | None

    def _func(self) -> None:
        container = Container()
        container.wire(
            modules=[modx.http.routers.compat,
                     modx.cli.commands.run]
        )

        c = config.get()
        if self.config:
            fpath = p.Path(self.config)
            if not fpath.exists():
                raise FileNotFoundError(f'Config file not found: {fpath}')
            if not fpath.is_file():
                raise ValueError(f'Config path is not a file: {fpath}')

            if fpath.suffix in {'.yaml', '.yml'}:
                c = config.ModXConfig.from_yaml(fpath)
            elif fpath.suffix == '.json':
                c = config.ModXConfig.from_json(fpath)
            else:
                raise ValueError('Config file must be .yaml, .yml, or .json')

            config.set(c)

        if self.keys_file:
            c.keys_file = self.keys_file
        if self.models_file:
            c.models_file = self.models_file

        config.set(c)
        run()

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            '--keys-file', '-k',
            type=str,
            default=None,
            help='Path to the keys file (default: %(default)s)',
        )
        parser.add_argument(
            '--models-file', '-m',
            type=str,
            default=None,
            help='Path to the models file (default: %(default)s)',
        )
        parser.add_argument(
            '--config', '-c',
            type=str,
            default=None,
            help='Path to the config file (default: %(default)s)',
        )


@inject
def run(server: HTTPServer = Provide[Container.http_server]) -> None:
    server.run()


def register(subparser: _SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparser.add_parser(
        'run',
        help='Run the HTTP server',
    )
    Args.add_args(parser)
    parser.set_defaults(func=Args.func)
