from __future__ import annotations

import typing as t

from modx.chatbot.types import BaseSchema

T = t.TypeVar('T', bound=BaseSchema)
U = t.TypeVar('U')
V = t.TypeVar('V')


class AsyncStream(t.AsyncIterable[T], t.Generic[T]):
    def __init__(
        self,
        source: t.AsyncIterable[V],
        mapper: t.Callable[[V], T] | None = None
    ):
        self._source = source
        self._mapper = mapper
        self._is_consumed = False
        self._items: t.List[T] = []
        self._error: Exception | None = None
        self._completed = False

    async def __aiter__(self):
        if self._is_consumed:
            # If the stream has already been consumed, return the cached items
            for item in self._items:
                yield item
            return

        self._is_consumed = True
        try:
            async for raw_item in self._source:
                if self._mapper:
                    item = self._mapper(raw_item)
                else:
                    item = raw_item

                self._items.append(item)
                yield item

        except Exception as e:
            self._error = e
            raise
        finally:
            self._completed = True

    async def __anext__(self) -> T:
        if not hasattr(self, '_iterator'):
            self._iterator = self.__aiter__()
        return await self._iterator.__anext__()

    def filter(self, predicate: t.Callable[[T], bool]) -> AsyncStream[T]:
        async def filtered_source():
            async for item in self:
                if predicate(item):
                    yield item

        return AsyncStream(filtered_source())

    def tap(self, action: t.Callable[[T], None]) -> AsyncStream[T]:
        async def tap_source():
            async for item in self:
                action(item)
                yield item

        return AsyncStream(tap_source())

    def map(self, mapper: t.Callable[[T], U]) -> AsyncStream[U]:
        async def mapped_source():
            async for item in self:
                yield mapper(item)

        return AsyncStream(mapped_source())

    def take(self, n: int) -> AsyncStream[T]:
        async def take_source():
            count = 0
            async for item in self:
                if count >= n:
                    break
                yield item
                count += 1

        return AsyncStream(take_source())

    def skip(self, n: int) -> AsyncStream[T]:
        async def skip_source():
            count = 0
            async for item in self:
                if count < n:
                    count += 1
                    continue
                yield item

        return AsyncStream(skip_source())

    def chunk(self, size: int) -> AsyncStream[t.List[T]]:
        async def chunk_source():
            batch = []
            async for item in self:
                batch.append(item)
                if len(batch) >= size:
                    yield batch
                    batch = []
            if batch:
                yield batch

        return AsyncStream(chunk_source())

    def take_while(self, predicate: t.Callable[[T], bool]) -> AsyncStream[T]:
        async def take_while_source():
            async for item in self:
                if not predicate(item):
                    break
                yield item

        return AsyncStream(take_while_source())

    def enumerate(self, start: int = 0) -> AsyncStream[t.Tuple[int, T]]:
        async def enumerate_source():
            index = start
            async for item in self:
                yield index, item
                index += 1

        return AsyncStream(enumerate_source())

    async def foreach(self, action: t.Callable[[T], t.Awaitable[None]]) -> None:
        async for item in self:
            await action(item)

    async def reduce(self, func: t.Callable[[U, T], U], initial: U) -> U:
        result = initial
        async for item in self:
            result = func(result, item)
        return result

    async def all(self, predicate: t.Callable[[T], bool] | None = None) -> bool:
        if predicate is None:
            def predicate(v: T) -> bool:
                return bool(v)

        async for item in self:
            if not predicate(item):
                return False
        return True

    @property
    def is_completed(self) -> bool:
        return self._completed

    @property
    def error(self) -> Exception | None:
        return self._error

    @property
    def items_count(self) -> int:
        return len(self._items)
