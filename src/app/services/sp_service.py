import asyncio
from typing import Any

from sqlalchemy import text

from app.db.base import async_session_maker


class SPService:
    def __init__(self):
        pass

    async def _execute_sp(self, sp_name: str, args: dict[str, Any]):
        args_list: list[str] = []
        for key, value in args.items():
            if isinstance(value, str):
                args_list.append(f"@{key} = '{value}'")
            else:
                args_list.append(f"@{key} = {value}")
        args_str = ", ".join(args_list)
        query = f"EXEC {sp_name} {args_str};"
        async with async_session_maker() as session:
            result = await session.execute(text(query))
            return result.mappings().all()

    async def get_occupancy_upcoming(self, start_date: str, end_date: str):
        # TODO: Add validation for start_date and end_date
        args = {"start_date": start_date, "end_date": end_date}
        return await self._execute_sp("sp_get_occupancy_upcoming", args)


if __name__ == "__main__":
    sp_service = SPService()
    result = asyncio.run(sp_service.get_occupancy_upcoming(start_date="2025-09-01", end_date="2026-09-30"))
    print(result)
