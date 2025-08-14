"""Manual script to verify treatment persistence for a screenplay.

Usage:
    poetry run python scripts/demo_treatment_persistence.py <screenplay_id> <treatment_text>

The script updates the treatment of the given screenplay and prints the stored
value, ensuring it is correctly associated with the screenplay ID.
"""

import asyncio
import sys

from app.db.database import SessionLocal
from app.db.models import Screenplay


async def main(screenplay_id: str, treatment: str) -> None:
    async with SessionLocal() as session:
        sp = await session.get(Screenplay, screenplay_id)
        if not sp:
            print("Screenplay not found")
            return
        sp.treatment = treatment
        await session.commit()
        refreshed = await session.get(Screenplay, screenplay_id)
        print("Stored treatment:", refreshed.treatment)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/demo_treatment_persistence.py <screenplay_id> <treatment_text>")
    else:
        asyncio.run(main(sys.argv[1], sys.argv[2]))

