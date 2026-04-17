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

@router.get("/nearby", response_model=HospitalsListResponse)
async def get_nearby_hospitals(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(5.0)
):
    """
    Fetches nearby hospitals using Google Places API (New) with a persistent async client.
    """
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Maps API Key missing")

    client = await get_location_client()
    
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.primaryType,places.rating,places.userRatingCount,places.internationalPhoneNumber,places.regularOpeningHours,places.googleMapsUri,places.accessibilityOptions",
        "Content-Type": "application/json"
    }
    
    payload = {
        "includedTypes": ["hospital"],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": int(radius_km * 1000.0)
            }
        }
    }

    try:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"[Places API Error] Status: {response.status_code}, Body: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        raw_results = data.get("places", [])
        hospitals = []
        
        for place in raw_results:
            try:
                p_location = place.get("location", {})
                p_lat = p_location.get("latitude")
                p_lng = p_location.get("longitude")
                
                if p_lat is None or p_lng is None:
                    continue
                    
                dist = calculate_distance(lat, lng, p_lat, p_lng)
                
                # Map "New API" fields to legacy HospitalResponse structure
                name = place.get("displayName", {}).get("text", "Unknown Hospital")
                address = place.get("formattedAddress", "Address not available")
                primary_type = place.get("primaryType", "hospital")
                
                is_emergency = "emergency" in name.lower() or "emergency" in primary_type.lower() or primary_type == "hospital"
                
                hospitals.append(HospitalResponse(
                    name=name,
                    address=address,
                    distance_km=round(dist, 2),
                    lat=p_lat,
                    lng=p_lng,
                    emergency=is_emergency,
                    maps_url=place.get("googleMapsUri") or f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lng}",
                    phone=place.get("internationalPhoneNumber"),
                    rating=place.get("rating"),
                    user_ratings_total=place.get("userRatingCount"),
                    open_now=place.get("regularOpeningHours", {}).get("openNow"),
                    wheelchair_accessible=place.get("accessibilityOptions", {}).get("wheelchairAccessibleEntrance")
                ))
            except Exception as item_err:
                print(f"Error parsing hospital item: {item_err}")
                continue
            
        return HospitalsListResponse(hospitals=sorted(hospitals, key=lambda x: x.distance_km))
        
    except httpx.HTTPStatusError as e:
        error_detail = "Hospital search failed (upstream API error)"
        try:
            error_json = e.response.json()
            if "error" in error_json:
                error_detail = f"Maps API Error: {error_json['error'].get('message', 'Unknown error')}"
        except:
            pass
        print(f"Places API HTTP Error: {e.response.text}")
        raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        print(f"Unexpected error fetching hospitals: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during hospital search")
