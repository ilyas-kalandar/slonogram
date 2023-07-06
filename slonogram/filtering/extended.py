from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic, Awaitable
from .types import FilterFn

from ..dispatching.context import Context

T = TypeVar("T")
D = TypeVar("D")


class ExtendedFilter(Generic[D, T], metaclass=ABCMeta):
    def __invert__(self) -> Inverted[D, T]:
        return Inverted(self)

    def __or__(self, rhs: FilterFn[D, T]) -> Or[D, T]:
        return Or(self, rhs, False)

    def __xor__(self, rhs: FilterFn[D, T]) -> Or[D, T]:
        return Or(self, rhs, True)

    def __and__(self, rhs: FilterFn[D, T]) -> And[D, T]:
        return And(self, rhs)

    @abstractmethod
    def __call__(self, ctx: Context[D, T]) -> Awaitable[bool]:
        _ = ctx
        raise NotImplementedError


class Just(ExtendedFilter[D, T]):
    def __init__(self, fn: FilterFn[D, T]) -> None:
        self.fn = fn

    def __call__(self, ctx: Context[D, T]) -> Awaitable[bool]:
        return self.fn(ctx)


class Or(ExtendedFilter[D, T]):
    def __init__(
        self, lhs: FilterFn[D, T], rhs: FilterFn[D, T], exclusive: bool
    ) -> None:
        self.lhs_fn = lhs
        self.rhs_fn = rhs
        self.exclusive = exclusive

    @property
    def symbol(self) -> str:
        return "^" if self.exclusive else "|"

    def __repr__(self) -> str:
        return f"{self.lhs_fn} {self.symbol} {self.rhs_fn}"

    async def __call__(self, ctx: Context[D, T]) -> bool:
        if self.exclusive:
            lhs = await self.lhs_fn(ctx)
            rhs = await self.rhs_fn(ctx)
            return bool(lhs ^ rhs)
        else:
            lhs = await self.lhs_fn(ctx)
            if not lhs:
                return await self.rhs_fn(ctx)
            return lhs


class And(ExtendedFilter[D, T]):
    def __init__(self, lhs: FilterFn[D, T], rhs: FilterFn[D, T]) -> None:
        self.lhs_fn = lhs
        self.rhs_fn = rhs

    def __repr__(self) -> str:
        return f"{self.lhs_fn} & {self.rhs_fn}"

    async def __call__(self, ctx: Context[D, T]) -> bool:
        lhs = await self.lhs_fn(ctx)
        if not lhs:
            return False
        return await self.rhs_fn(ctx)


class Inverted(ExtendedFilter[D, T]):
    def __init__(self, fn: FilterFn[D, T]) -> None:
        self.fn = fn

    def __repr__(self) -> str:
        return f"~{self.fn}"

    async def __call__(self, ctx: Context[D, T]) -> bool:
        result = await self.fn(ctx)
        return not result


async def always_true(_: Context[D, T]) -> bool:
    return True


def not_(fn: FilterFn[D, T]) -> Inverted[D, T]:
    return Inverted(fn)


__all__ = ["not_", "always_true", "And", "Or", "ExtendedFilter"]