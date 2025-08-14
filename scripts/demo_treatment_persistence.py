"""Manual script to verify treatment persistence for a project.

Usage:
    poetry run python scripts/demo_treatment_persistence.py <project_id> <treatment_text>

The script updates the treatment of the given project and prints the stored
value, ensuring it is correctly associated with the project ID.
"""

import asyncio
import sys

from app.db.database import SessionLocal
from app.db.models import Project


async def main(project_id: str, treatment: str) -> None:
    async with SessionLocal() as session:
        project = await session.get(Project, project_id)
        if not project:
            print("Project not found")
            return
        project.treatment = treatment
        await session.commit()
        refreshed = await session.get(Project, project_id)
        print("Stored treatment:", refreshed.treatment)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/demo_treatment_persistence.py <project_id> <treatment_text>")
    else:
        asyncio.run(main(sys.argv[1], sys.argv[2]))

