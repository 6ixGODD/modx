from __future__ import annotations

import typing as t

class Secret:
    __algorithm__: t.ClassVar[t.Literal['argon2', 'bcrypt']] = 'argon2'
