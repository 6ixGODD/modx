from __future__ import annotations

import json
import pathlib as p
import typing as t

import jinja2 as j2

from modx import constants
from modx.config import ModXConfig
from modx.logger import Logger
from modx.resources import WatchedResource
from modx.resources.models import types


class Models(
    WatchedResource[t.Dict[str, types.ModelDefinition]],
    t.Mapping[str, types.ModelDefinition]
):
    __logging_tag__ = 'modx.resources.model'

    def __init__(self, config: ModXConfig, logger: Logger):
        self.config = config
        self.templates = dict[str, j2.Template]()
        self.jinja_env = j2.Environment(trim_blocks=True, lstrip_blocks=True)
        WatchedResource.__init__(
            self,
            fpath=config.models_file,
            logger=logger
        )

    def _parse(self) -> t.Dict[str, types.ModelDefinition]:
        content = self.fpath.read_text(encoding='utf-8')
        data = json.loads(content)
        models = dict[str, types.ModelDefinition]()
        templates = dict[str, j2.Template]()
        for k, v in data.items():
            definition = types.ModelDefinition.model_validate(v)
            if definition.prompt_path:
                prompt_path = p.Path(definition.prompt_path)
                if not prompt_path.exists() or not prompt_path.is_file():
                    self.logger.warning(
                        f'Prompt file not found: {prompt_path}'
                    )
                    prompt = constants.DEFAULT_PROMPT
                    self.logger.debug(
                        f'Using default prompt for model {definition.id}'
                    )
                else:
                    prompt = prompt_path.read_text(encoding='utf-8')
                    self.logger.debug(
                        f'Loaded prompt from {prompt_path} for model '
                        f'{definition.id}'
                    )
                templates[definition.id] = self.jinja_env.from_string(prompt)

            models[k] = definition
            self.logger.debug(
                f'Loaded model definition: {k} -> {models[k]}'
            )
        self.templates = templates
        return models

    def list_models(self) -> types.ModelList:
        if self.data is None:
            return types.ModelList(object='list', data=[])
        return types.ModelList(
            object='list',
            data=[
                types.Model(
                    id=model.id,
                    object='model',
                    created=model.created,
                    owned_by=model.owned_by,
                )
                for model in self.data.values()
            ]
        )

    def retrieve_model(self, id: str, /) -> types.Model:
        if self.data is None:
            raise KeyError('Model data is not loaded')

        if id not in self.data:
            raise KeyError(f'Model "{id}" not found')

        model = self.data[id]
        return types.Model(
            id=model.id,
            object='model',
            created=model.created,
            owned_by=model.owned_by,
        )

    def render(self, id: str, /, **kwargs: t.Any) -> str:
        if self.data is None or self.templates is None:
            raise RuntimeError('Model data is not loaded')

        if id not in self.data:
            raise KeyError(f'Model "{id}" not found')

        if id not in self.templates:
            raise RuntimeError(f'No template found for model "{id}"')

        template = self.templates[id]
        try:
            return template.render(**kwargs)
        except j2.TemplateError as e:
            self.logger.error(
                f'Error rendering template for model "{id}": {e}'
            )
            raise RuntimeError(
                f'Error rendering template for model "{id}": {e}'
            ) from e

    def render_safe(
        self,
        id: str,
        default: str = constants.DEFAULT_PROMPT, /,
        **kwargs: t.Any
    ) -> str:
        try:
            return self.render(id, **kwargs)
        except (KeyError, RuntimeError) as e:
            self.logger.error(f'Error rendering model "{id}": {e}')
            return default

    def __len__(self) -> int:
        return len(self.data or {})

    def __iter__(self) -> t.Iterator[str]:
        return iter(self.data or {})

    def __getitem__(self, key: str, /) -> types.ModelDefinition:
        if self.data is None:
            raise KeyError('Model data is not loaded')

        if key not in self.data:
            raise KeyError(f'Model "{key}" not found')

        return self.data[key]
