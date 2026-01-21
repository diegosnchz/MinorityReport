from fastapi import APIRouter
from typing import List
from app.models.schemas_location import Location
from app.repositories.location_repo import location_repo

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.get("/", response_model=List[Location])
async def get_locations():
    return await location_repo.find_all()

@router.get("/hotspots", response_model=List[Location])
async def get_crime_hotspots():
    return await location_repo.find_hotspots()
