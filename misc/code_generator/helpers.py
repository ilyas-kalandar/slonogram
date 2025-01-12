from dataclasses import dataclass, field
from typing import Sequence, Optional, Protocol, TypeVar

T = TypeVar("T")


class GenerationHelper(Protocol):
    def generate(self, indent: int, /) -> str:
        raise NotImplementedError


@dataclass
class SelfArg:
    def generate(self, level: int, /) -> str:
        return f"{gen_indent(level)}self"


@dataclass
class FunctionArgument:
    name: str
    hint: str
    default: Optional[str] = None

    def generate(self, level: int, /) -> str:
        default = f" = {self.default}" if self.default is not None else ""
        return f"{gen_indent(level)}{self.name}: {self.hint}{default}"


@dataclass
class ClassField:
    name: str
    hint: Optional[str] = None
    default: Optional[str] = None

    def generate(self, level: int, /) -> str:
        base = f"{gen_indent(level)}{self.name}"
        if self.hint is not None:
            base += f": {self.hint}"
        if self.default is not None:
            return base + f" = {self.default}"
        return base


@dataclass
class Pass:
    def generate(self, level: int, /) -> str:
        return f"{gen_indent(level)}pass"


@dataclass
class Function:
    name: str
    args: Sequence[FunctionArgument | SelfArg]
    body: GenerationHelper
    return_hint: str

    async_: bool = False

    def generate(self, level: int, /) -> str:
        indent = gen_indent(level)
        asyncness = "async " if self.async_ else ""
        args = ", ".join(arg.generate(0) for arg in self.args)
        lines = [
            f"{indent}{asyncness}def {self.name}({args}) "
            f"-> {self.return_hint}:",
            self.body.generate(level + 1),
        ]

        return "\n".join(lines)


@dataclass
class Decorate:
    expr: str
    body: GenerationHelper

    def generate(self, level: int, /) -> str:
        return f"{gen_indent(level)}@{self.expr}\n" + self.body.generate(
            level
        )


@dataclass
class Class:
    name: str

    methods: Sequence[Function]
    fields: Sequence[ClassField] = field(default_factory=list)

    inherits: Optional[Sequence[str]] = None

    def generate(self, level: int, /) -> str:
        body_level = level + 1
        base_ind = gen_indent(level)
        indent = gen_indent(body_level)

        if self.inherits is not None:
            inherits = f"({', '.join(self.inherits)})"
        else:
            inherits = ""
        out = [f"{base_ind}class {self.name}{inherits}:"]
        out.extend(
            f.generate(body_level)
            for f in sorted(
                self.fields, key=lambda f: f.default is not None
            )
        )
        out.extend(m.generate(body_level) for m in self.methods)

        if len(out) == 1:
            out.append(f"{indent}pass")

        return "\n".join(out)


@dataclass
class IndentedLines:
    lines: Sequence[str]

    def generate(self, level: int, /) -> str:
        indent = gen_indent(level)
        return "\n".join(indent + line for line in self.lines)


@dataclass
class Import:
    package: str
    only: Optional[str | Sequence[str]] = None

    def generate(self, level: int, /) -> str:
        indent = gen_indent(level)
        if self.only is not None:
            if isinstance(self.only, str):
                return f"{indent}from {self.package} import {self.only}"
            return (
                f"{indent}from {self.package} "
                f"import ({', '.join(self.only)})"
            )
        return f"{indent}import {self.package}"


def generate(*helpers: GenerationHelper, use_black: bool = True) -> str:
    result = "\n".join(helper.generate(0) for helper in helpers)
    if use_black:
        import black
        from black.report import NothingChanged

        mode = black.FileMode(line_length=75)
        try:
            result = black.format_file_contents(
                result, fast=True, mode=mode
            )
        except NothingChanged:
            pass
    return result


def gen_indent(level: int) -> str:
    return "    " * level
