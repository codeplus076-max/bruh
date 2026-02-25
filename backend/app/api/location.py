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

class HospitalsListResponse(BaseModel):
    hospitals: List[HospitalResponse]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def fetch_place_details(place_id: str) -> dict:
    """Fetch phone and opening hours from Google Place Details API."""
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        return {}
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
        # Google Places Nearby Search API
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": "hospital",
            "key": api_key
        }
        response = requests.get(url, params=params, timeout=10)

        hospitals = []
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])[:10]  # Limit to 10 results

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
                
                # Check for emergency services via types
                types = place.get("types", [])
                emergency = "emergency" in types or place.get("permanently_closed") is None

                # Google Maps URL for navigation
                maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/maps?q={h_lat},{h_lng}"

                # Fetch detailed info (phone, hours) from Place Details
                details = fetch_place_details(place_id) if place_id else {}
                phone = details.get("formatted_phone_number")
                hours_data = details.get("opening_hours", {})
                if hours_data:
                    weekday_text = hours_data.get("weekday_text", [])
                    opening_hours = " | ".join(weekday_text[:2]) if weekday_text else None
                    if hours_data.get("open_now") is True and not opening_hours:
                        opening_hours = "Open Now"
                else:
                    opening_hours = None

                hospitals.append(HospitalResponse(
                    name=name,
                    address=address,
                    distance_km=dist,
                    lat=h_lat,
                    lng=h_lng,
                    emergency=emergency,
                    maps_url=maps_url,
                    phone=phone,
                    opening_hours=opening_hours
                ))

        # Sort by distance
        hospitals.sort(key=lambda x: x.distance_km)

        if not hospitals:
            raise ValueError("No hospitals found")

        return HospitalsListResponse(hospitals=hospitals)

    except Exception as e:
        # Fallback on error
        fallback = HospitalResponse(
            name="Central Hospital (Fallback)",
            address="Please enable location and try again",
            distance_km=0.0,
            lat=lat + 0.01,
            lng=lng + 0.01,
            emergency=True,
            maps_url=f"https://www.google.com/maps/search/hospital/@{lat},{lng},14z",
            phone=None,
            opening_hours=None
        )
        return HospitalsListResponse(hospitals=[fallback])

