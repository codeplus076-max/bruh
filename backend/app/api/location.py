from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import requests
import math
import os

router = APIRouter(prefix="/hospitals", tags=["hospitals"])

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
    open_now: Optional[bool] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None

class HospitalsListResponse(BaseModel):
    hospitals: List[HospitalResponse]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def fetch_place_details(place_id: str, api_key: str) -> dict:
    """Fetch phone and opening hours from Google Place Details API."""
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,opening_hours",
            "key": api_key
        }
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            return res.json().get("result", {})
    except Exception:
        pass
    return {}

@router.get("/nearby", response_model=HospitalsListResponse)
async def get_nearby_hospitals(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius: int = Query(5000, description="Search radius in meters")
):
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="MAPS_API_KEY not configured")

    try:
        # Google Places Nearby Search — ranked by prominence
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": "hospital",
            "rankby": "prominence",
            "key": api_key
        }
        response = requests.get(url, params=params, timeout=10)

        hospitals = []
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])[:12]

            for place in results:
                geometry = place.get("geometry", {}).get("location", {})
                h_lat = geometry.get("lat")
                h_lng = geometry.get("lng")

                if h_lat is None or h_lng is None:
                    continue

                dist = calculate_distance(lat, lng, h_lat, h_lng)
                name = place.get("name", "Unknown Hospital")
                address = place.get("vicinity", "Unknown Address")
                place_id = place.get("place_id", "")
                rating = place.get("rating")
                rating_count = place.get("user_ratings_total")

                # open_now comes from the Nearby Search result directly
                opening_hours_brief = place.get("opening_hours", {})
                open_now = opening_hours_brief.get("open_now") if opening_hours_brief else None

                types = place.get("types", [])
                emergency = "hospital" in types

                # Google Maps URL using place_id
                maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/maps?q={h_lat},{h_lng}"

                # Fetch phone from Place Details (separate call)
                details = fetch_place_details(place_id, api_key) if place_id else {}
                phone = details.get("formatted_phone_number")

                # Get opening hours text from details if available
                hours_data = details.get("opening_hours", {})
                weekday_text = hours_data.get("weekday_text", []) if hours_data else []
                opening_hours = weekday_text[0] if weekday_text else None  # today's hours

                hospitals.append(HospitalResponse(
                    name=name,
                    address=address,
                    distance_km=dist,
                    lat=h_lat,
                    lng=h_lng,
                    emergency=emergency,
                    maps_url=maps_url,
                    phone=phone,
                    opening_hours=opening_hours,
                    open_now=open_now,
                    rating=rating,
                    rating_count=rating_count
                ))

        # Sort by distance
        hospitals.sort(key=lambda x: x.distance_km)

        if not hospitals:
            raise ValueError("No hospitals found in radius")

        return HospitalsListResponse(hospitals=hospitals)

    except Exception as e:
        fallback = HospitalResponse(
            name="Central Hospital (Fallback)",
            address="Please enable location access and try again",
            distance_km=0.0,
            lat=lat + 0.01,
            lng=lng + 0.01,
            emergency=True,
            maps_url=f"https://www.google.com/maps/search/hospital/@{lat},{lng},14z",
            phone=None,
            opening_hours=None,
            open_now=None,
            rating=None,
            rating_count=None
        )
        return HospitalsListResponse(hospitals=[fallback])
