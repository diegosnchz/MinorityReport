import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import db_manager
from app.services.simulation_service import simulation_service

async def main():
    print("Connecting to DB...")
    await db_manager.connect()
    try:
        print("Running simulation step...")
        await simulation_service.run_step()
        print("Simulation step successful!")
    except Exception as e:
        print("CAUGHT EXCEPTION:")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
