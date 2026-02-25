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
    # New Google Maps-style fields
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    website: Optional[str] = None
    wheelchair_accessible: Optional[bool] = None
    open_now: Optional[bool] = None
    specialty: Optional[str] = None   # e.g. "Multispecialty hospital", "Clinic"

class HospitalsListResponse(BaseModel):
    hospitals: List[HospitalResponse]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# Map of Google Places types → human-readable specialty labels
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

def fetch_place_details(place_id: str) -> dict:
    """Fetch phone, website, opening hours, rating, and wheelchair info from Google Place Details API."""
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        return {}
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": (
                "formatted_phone_number,"
                "opening_hours,"
                "website,"
                "wheelchair_accessible_entrance,"
                "rating,"
                "user_ratings_total"
            ),
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
    radius: int = Query(10000, description="Search radius in meters")
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
            api_status = data.get("status", "UNKNOWN")
            if api_status not in ("OK", "ZERO_RESULTS"):
                raise ValueError(f"Google Places API error: {api_status} — {data.get('error_message', 'No details')}")
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
                types = place.get("types", [])

                # Emergency: only if explicitly tagged or name contains emergency keywords
                emergency = "emergency" in types or any(
                    kw in name.lower()
                    for kw in ("emergency", "trauma", "casualty", "icu")
                )

                # Google Maps URL for navigation
                maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/maps?q={h_lat},{h_lng}"

                # Fetch detailed info (phone, hours, website, rating, wheelchair)
                details = fetch_place_details(place_id) if place_id else {}

                phone = details.get("formatted_phone_number")
                website = details.get("website")
                rating = details.get("rating") or place.get("rating")
                user_ratings_total = details.get("user_ratings_total") or place.get("user_ratings_total")
                wheelchair_accessible = details.get("wheelchair_accessible_entrance")

                # Opening hours
                hours_data = details.get("opening_hours", {})
                open_now: Optional[bool] = None
                opening_hours: Optional[str] = None
                if hours_data:
                    open_now = hours_data.get("open_now")
                    weekday_text = hours_data.get("weekday_text", [])
                    if weekday_text:
                        # Show today's hours
                        import datetime
                        today_idx = datetime.datetime.now().weekday()  # Mon=0, Sun=6
                        # Google weekday_text starts Sunday
                        google_idx = (today_idx + 1) % 7
                        if google_idx < len(weekday_text):
                            # e.g. "Monday: Open 24 hours" → "Open 24 hours"
                            today_text = weekday_text[google_idx]
                            parts = today_text.split(": ", 1)
                            opening_hours = parts[1] if len(parts) == 2 else today_text
                        else:
                            opening_hours = weekday_text[0]
                    elif open_now is True:
                        opening_hours = "Open now"
                    elif open_now is False:
                        opening_hours = "Closed now"

                # From nearbysearch result open_now if details didn't have it
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

        # Sort by distance
        hospitals.sort(key=lambda x: x.distance_km)

        if not hospitals:
            raise ValueError("No hospitals found nearby")

        return HospitalsListResponse(hospitals=hospitals)

    except Exception as e:
        # Log the real error and return a helpful fallback
        print(f"[location.py] Hospital fetch error: {type(e).__name__}: {e}")
        fallback = HospitalResponse(
            name="Nearby Hospital Search Unavailable",
            address=f"Error: {str(e)[:120]}. Try again or search manually on Google Maps.",
            distance_km=0.0,
            lat=lat,
            lng=lng,
            emergency=False,
            maps_url=f"https://www.google.com/maps/search/hospital/@{lat},{lng},14z",
            phone=None,
            opening_hours=None
        )
        return HospitalsListResponse(hospitals=[fallback])
