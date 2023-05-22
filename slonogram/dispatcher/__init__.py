from ..bot import Bot
from ..schemas.updates import UpdateType

from .local_set import LocalSet

from typing import List, Optional
from anyio import create_task_group


class Dispatcher:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._sets: List[LocalSet] = []
        self._task_group = create_task_group()

    async def run_polling(
        self,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Optional[List[UpdateType]] = None,
    ) -> None:
        offset = None

        while True:
            updates = await self._bot.updates.get_updates(
                offset, limit, timeout, allowed_updates
            )
            if not updates:
                continue

            last_update = updates[-1]
            offset = last_update.id + 1

            for update in updates:
                print(update)

    def register_set(self, set_: LocalSet):
        self._sets.append(set_)


__all__ = ["Dispatcher"]
