from __future__ import annotations

from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class DependencyMiddleware(BaseMiddleware):
    def __init__(self, **deps: Any):
        super().__init__()
        self.deps = deps

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        data.update(self.deps)
        return await handler(event, data)
