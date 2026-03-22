from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import math
import os
import httpx

router = APIRouter(prefix="/hospitals", tags=["hospitals"])

_client = None

async def get_location_client():
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=15.0)
    return _client

class HospitalResponse(BaseModel):
    name: str
    address: str
    distance_km: float
    lat: float
    lng: float
    emergency: bool
    maps_url: str
    phone: Optional[str] = None
    opening_hours: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    website: Optional[str] = None
    wheelchair_accessible: Optional[bool] = None
    open_now: Optional[bool] = None
    specialty: Optional[str] = None

class HospitalsListResponse(BaseModel):
    hospitals: List[HospitalResponse]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@router.get("", response_model=HospitalsListResponse)
async def get_nearby_hospitals(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(5.0)
):
    """
    Fetches nearby hospitals using Google Places API with a persistent async client.
    """
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Maps API Key missing")

    client = await get_location_client()
    
    # 1. Nearby Search (Hospitals, Clinics, Health Centers)
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": int(radius_km * 1000),
        "type": "hospital",
        "key": api_key
    }

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        raw_results = data.get("results", [])
        hospitals = []
        
        for place in raw_results:
            p_lat = place["geometry"]["location"]["lat"]
            p_lng = place["geometry"]["location"]["lng"]
            dist = calculate_distance(lat, lng, p_lat, p_lng)
            
            # Enrich maps URL
            maps_url = f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lng}&query_place_id={place.get('place_id')}"
            
            hospitals.append(HospitalResponse(
                name=place.get("name", "Unknown"),
                address=place.get("vicinity", "Address undisclosed"),
                distance_km=round(dist, 2),
                lat=p_lat,
                lng=p_lng,
                emergency=any(x in place.get("name", "").lower() for x in ["emergency", "trauma", "cardiac"]),
                maps_url=maps_url,
                phone=None, # Nearby search doesn't return phone numbers
                rating=place.get("rating"),
                user_ratings_total=place.get("user_ratings_total"),
                open_now=place.get("opening_hours", {}).get("open_now")
            ))
            
        return HospitalsListResponse(hospitals=sorted(hospitals, key=lambda x: x.distance_km))
        
    except Exception as e:
        print(f"Error fetching hospitals: {e}")
        raise HTTPException(status_code=500, detail="Hospital search failed")
