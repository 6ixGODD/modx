from __future__ import annotations

import collections.abc as coll
import contextvars as cvs
import typing as t


class Context(coll.MutableMapping):
    _context_var: cvs.ContextVar[t.Dict[str, t.Any]] = (
        cvs.ContextVar('request_context', default={})
    )

    def __init__(self, init_data: t.Dict[str, t.Any] | None = None):
        self._context_var.set((init_data or {}).copy())

    def __getitem__(self, key: str) -> t.Any:
        context = self._context_var.get()
        return context[key]

    def __setitem__(self, key: str, value: t.Any) -> None:
        context = self._context_var.get().copy()
        context[key] = value
        self._context_var.set(context)

    def __delitem__(self, key: str) -> None:
        context = self._context_var.get().copy()
        del context[key]
        self._context_var.set(context)

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._context_var.get())

    def __len__(self) -> int:
        return len(self._context_var.get())

    def __contains__(self, key: str) -> bool:
        return key in self._context_var.get()

    def __repr__(self) -> str:
        return f"Context({self._context_var.get()})"

    __str__ = __repr__

    def get(self, key: str, default: t.Any = None) -> t.Any:
        return self._context_var.get().get(key, default)

    def set(self, key: str, value: t.Any) -> t.Self:
        self[key] = value
        return self

    def setx(self, **kwargs) -> t.Self:
        context = self._context_var.get().copy()
        context.update(kwargs)
        self._context_var.set(context)
        return self

    def delete(self, key: str) -> t.Self:
        if key in self:
            del self[key]
        return self

    def clear(self) -> t.Self:
        self._context_var.set({})
        return self

    def copy(self) -> t.Dict[str, t.Any]:
        return self._context_var.get().copy()

    def keys(self) -> t.KeysView[str]:
        return self._context_var.get().keys()

    def values(self) -> t.ValuesView[t.Any]:
        return self._context_var.get().values()

    def items(self) -> t.ItemsView[str, t.Any]:
        return self._context_var.get().items()

    def pop(self, key: str, default: t.Any = None) -> t.Any:
        context = self._context_var.get().copy()
        value = context.pop(key, default)
        self._context_var.set(context)
        return value

    def update(
        self,
        other: t.Dict[str, t.Any] | Context,
        **kwargs
    ) -> t.Self:
        """Update context with another dict or Context"""
        context = self._context_var.get().copy()
        if isinstance(other, Context):
            context.update(other.copy())
        else:
            context.update(other)
        self._context_var.set(context)
        return self

    # Type-safe convenience methods
    def get_str(self, key: str, default: str = '') -> str:
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
