from fastapi import APIRouter
from typing import List
from app.models.schemas_crime import CrimeEvent
from app.repositories.crime_repo import crime_repo

router = APIRouter(prefix="/crimes", tags=["Crimes"])

@router.get("/recent", response_model=List[CrimeEvent])
async def get_recent_crimes():
    return await crime_repo.find_recent_activity()
