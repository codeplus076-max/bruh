from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import requests
import math
import os
from cachetools import cached, TTLCache

import datetime
import asyncio
import httpx

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
    return round(R * c, 2)

SPECIALTY_LABELS = {
    "hospital": "Hospital",
    "doctor": "Doctor's clinic",
    "pharmacy": "Pharmacy",
    "physiotherapist": "Physiotherapy",
    "dentist": "Dental clinic",
    "health": "Health centre",
}

def infer_specialty(types: list, name: str) -> str:
    name_lower = name.lower()
    if "multispecialt" in name_lower or "multi specialt" in name_lower:
        return "Multispecialty hospital"
    if "children" in name_lower or "pediatric" in name_lower or "paediatric" in name_lower:
        return "Children's hospital"
    if "maternity" in name_lower or "women" in name_lower:
        return "Maternity hospital"
    if "eye" in name_lower or "ophthal" in name_lower:
        return "Eye hospital"
    if "cancer" in name_lower or "oncolog" in name_lower:
        return "Cancer centre"
    if "cardiac" in name_lower or "heart" in name_lower:
        return "Cardiac centre"
    if "nursing home" in name_lower:
        return "Nursing home"
    for t in types:
        if t in SPECIALTY_LABELS:
            return SPECIALTY_LABELS[t]
    return "Hospital"

# Keep the detail cache in memory
detail_cache = TTLCache(maxsize=1000, ttl=604800)

async def fetch_place_details_async(client: httpx.AsyncClient, place_id: str) -> dict:
    if place_id in detail_cache:
        return detail_cache[place_id]
        
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        return {}
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,opening_hours,website,wheelchair_accessible_entrance,rating,user_ratings_total",
            "key": api_key
        }
        res = await client.get(url, params=params, timeout=5.0)
        if res.status_code == 200:
            data = res.json().get("result", {})
            detail_cache[place_id] = data
            return data
    except Exception:
        pass
    return {}

@router.get("/nearby", response_model=HospitalsListResponse)
async def get_nearby_hospitals(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude")
):
    rounded_lat = round(lat, 3)
    rounded_lng = round(lng, 3)
    return await _get_hospitals_cached(rounded_lat, rounded_lng, lat, lng)

@cached(cache=TTLCache(maxsize=500, ttl=86400))
def _fetch_hospitals_from_google(rounded_lat: float, rounded_lng: float) -> List[dict]:
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        raise ValueError("MAPS_API_KEY not configured")

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{rounded_lat},{rounded_lng}",
        "rankby": "distance",
        "type": "hospital",
        "key": api_key
    }
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        api_status = data.get("status", "UNKNOWN")
        if api_status not in ("OK", "ZERO_RESULTS"):
            raise ValueError(f"Google Places API error: {api_status} — {data.get('error_message', 'No details')}")
        return data.get("results", [])[:10]
    else:
        raise ValueError(f"HTTP Error: {response.status_code}")

async def _get_hospitals_cached(rounded_lat: float, rounded_lng: float, orig_lat: float, orig_lng: float) -> HospitalsListResponse:
    try:
        # 1. Get the base list (cached sync call to avoid overbilling)
        results = _fetch_hospitals_from_google(rounded_lat, rounded_lng)
        
        # 2. Parallel fetch for all Place Details using httpx
        place_ids = [p.get("place_id") for p in results if p.get("place_id")]
        details_map = {}
        
        async with httpx.AsyncClient() as client:
            tasks = [fetch_place_details_async(client, pid) for pid in place_ids]
            detail_results = await asyncio.gather(*tasks)
            details_map = {pid: detail for pid, detail in zip(place_ids, detail_results)}

        # 3. Assemble response
        hospitals = []
        for place in results:
            geometry = place.get("geometry", {}).get("location", {})
            h_lat = geometry.get("lat")
            h_lng = geometry.get("lng")

            if h_lat is None or h_lng is None:
                continue

            dist = calculate_distance(orig_lat, orig_lng, h_lat, h_lng)
            name = place.get("name", "Unknown Hospital")
            address = place.get("vicinity", "Unknown Address")
            place_id = place.get("place_id", "")
            types = place.get("types", [])

            emergency = "emergency" in types or any(kw in name.lower() for kw in ("emergency", "trauma", "casualty", "icu"))

            maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/maps?q={h_lat},{h_lng}"

            # Get the pre-fetched details
            details = details_map.get(place_id, {})

            phone = details.get("formatted_phone_number")
            website = details.get("website")
            rating = details.get("rating") or place.get("rating")
            user_ratings_total = details.get("user_ratings_total") or place.get("user_ratings_total")
            wheelchair_accessible = details.get("wheelchair_accessible_entrance")

            hours_data = details.get("opening_hours", {})
            open_now: Optional[bool] = None
            opening_hours: Optional[str] = None
            if hours_data:
                open_now = hours_data.get("open_now")
                weekday_text = hours_data.get("weekday_text", [])
                if weekday_text:
                    today_idx = datetime.datetime.now().weekday()
                    google_idx = (today_idx + 1) % 7
                    if google_idx < len(weekday_text):
                        today_text = weekday_text[google_idx]
                        parts = today_text.split(": ", 1)
                        opening_hours = parts[1] if len(parts) == 2 else today_text
                    else:
                        opening_hours = weekday_text[0]
                elif open_now is True:
                    opening_hours = "Open now"
                elif open_now is False:
                    opening_hours = "Closed now"

            if open_now is None:
                nb_hours = place.get("opening_hours", {})
                if nb_hours:
                    open_now = nb_hours.get("open_now")

            specialty = infer_specialty(types, name)

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
                rating=rating,
                user_ratings_total=user_ratings_total,
                website=website,
                wheelchair_accessible=wheelchair_accessible,
                open_now=open_now,
                specialty=specialty,
            ))

        hospitals.sort(key=lambda x: x.distance_km)

        if not hospitals:
            raise ValueError("No hospitals found nearby")

        return HospitalsListResponse(hospitals=hospitals)

    except Exception as e:
        print(f"[location.py] Hospital fetch error: {type(e).__name__}: {e}")
        fallback = HospitalResponse(
            name="Nearby Hospital Search Unavailable",
            address=f"Error: {str(e)[:120]}. Try again or search manually on Google Maps.",
            distance_km=0.0,
            lat=orig_lat,
            lng=orig_lng,
            emergency=False,
            maps_url=f"https://www.google.com/maps/search/hospital/@{orig_lat},{orig_lng},14z",
            phone=None,
            opening_hours=None
        )
        return HospitalsListResponse(hospitals=[fallback])
