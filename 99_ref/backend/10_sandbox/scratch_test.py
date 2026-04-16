import asyncio
import os
import sys
from importlib import import_module
from pathlib import Path

import asyncpg


async def main():
    # Attempt to load database URL from application settings
    # This assumes the repository root is in sys.path or the script is run as a module.
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        try:
            # Add repo root to path to allow importing the backend package
            repo_root = Path(__file__).resolve().parents[2]
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            
            settings_mod = import_module("backend.00_config.settings")
            settings = settings_mod.load_settings()
            database_url = settings.database_url
        except Exception:
            pass

    if not database_url:
        print("Error: DATABASE_URL not found in environment and could not load backend settings.")
        sys.exit(1)

    conn = await asyncpg.connect(database_url)
    
    rows = await conn.fetch("""
        SELECT v.id, v.framework_code, v.control_count,
               (SELECT COUNT(*) FROM "05_grc_library"."13_fct_controls" cc WHERE cc.framework_id = v.id AND cc.is_deleted = FALSE) AS working_control_count
        FROM "05_grc_library"."40_vw_framework_catalog" v
    """)
    for r in rows:
        print(dict(r))
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
