from __future__ import annotations

import collections.abc as coll
import contextvars as cvs
import typing as t


class Context(coll.MutableMapping):
    _context: cvs.ContextVar[dict[str, t.Any]] = (
        cvs.ContextVar('_context', default=None)
    )

    def __init__(self, init_data: dict[str, t.Any] | None = None):
        self._context.set((init_data or {}).copy())

    def __getitem__(self, key: str, /) -> t.Any:
        context = self._context.get()
        return context[key]

    def __setitem__(self, key: str, /, value: t.Any) -> None:
        context = self._context.get().copy()
        context[key] = value
        self._context.set(context)
        print('Context set:', self._context.get())

    def __delitem__(self, key: str, /) -> None:
        context = self._context.get().copy()
        if key in context:
            del context[key]
        self._context.set(context)
        print('Context delete:', self._context.get())

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._context.get())

    def __len__(self) -> int:
        return len(self._context.get())

    def __contains__(self, key: str, /) -> bool:
        return key in self._context.get()

    def __repr__(self) -> str:
        return f"Context({self._context.get()})"

    __str__ = __repr__

    def get(self, key: str, /, default: t.Any = None) -> t.Any:
        return self._context.get().get(key, default)

    def set(self, key: str, /, value: t.Any) -> t.Self:
        self[key] = value
        return self

    def setx(self, **kwargs) -> t.Self:
        context = self._context.get().copy()
        context.update(kwargs)
        self._context.set(context)
        return self

    def delete(self, key: str, /) -> t.Self:
        if key in self:
            del self[key]
        return self

    def clear(self) -> t.Self:
        self._context.set({})
        return self

    def copy(self) -> dict[str, t.Any]:
        return self._context.get().copy()

    def keys(self) -> t.KeysView[str]:
        return self._context.get().keys()

    def values(self) -> t.ValuesView[t.Any]:
        return self._context.get().values()

    def items(self) -> t.ItemsView[str, t.Any]:
        return self._context.get().items()

    def pop(self, key: str, /, default: t.Any = None) -> t.Any:
        context = self._context.get().copy()
        value = context.pop(key, default)
        self._context.set(context)
        return value

    def update(
        self,
        other: dict[str, t.Any] | Context,
        **kwargs
    ) -> t.Self:
        """Update context with another dict or Context"""
        context = self._context.get().copy()
        if isinstance(other, Context):
            context.update(other.copy())
        else:
            context.update(other)
        self._context.set(context)
        return self

    # Type-safe convenience methods
    def get_str(self, key: str, default: str = '') -> str:
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.get(key, default)
        if isinstance(value, (str, t.SupportsInt, t.SupportsIndex)):
            return int(value)
        else:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
