from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import requests
import math
import os
from cachetools import cached, TTLCache

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

@cached(cache=TTLCache(maxsize=1000, ttl=604800)) # Cache details (phone, etc) for 7 days
def fetch_place_details(place_id: str) -> dict:
    """Fetch phone, website, opening hours, rating, and wheelchair info via Places API v2."""
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        return {}
    try:
        # Places API v2 - Get Place by ID
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "formattedAddress,nationalPhoneNumber,regularOpeningHours,"
                "websiteUri,accessibilityOptions,rating,userRatingCount"
            )
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            # Normalize to the field names the rest of the code expects
            result = {}
            if "nationalPhoneNumber" in data:
                result["formatted_phone_number"] = data["nationalPhoneNumber"]
            if "websiteUri" in data:
                result["website"] = data["websiteUri"]
            if "rating" in data:
                result["rating"] = data["rating"]
            if "userRatingCount" in data:
                result["user_ratings_total"] = data["userRatingCount"]
            if "accessibilityOptions" in data:
                result["wheelchair_accessible_entrance"] = data["accessibilityOptions"].get("wheelchairAccessibleEntrance")
            if "regularOpeningHours" in data:
                oh = data["regularOpeningHours"]
                result["opening_hours"] = {
                    "open_now": oh.get("openNow"),
                    "weekday_text": oh.get("weekdayDescriptions", [])
                }
            return result
    except Exception:
        pass
    return {}

@router.get("/nearby", response_model=HospitalsListResponse)
async def get_nearby_hospitals(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude")
):
    # Round coordinates to 3 decimal places (approx. 110 meters) to group nearby requests
    # and maximize cache hits while remaining accurate enough for mapping.
    rounded_lat = round(lat, 3)
    rounded_lng = round(lng, 3)
    
    return await _get_hospitals_cached(rounded_lat, rounded_lng, lat, lng)

# Cache for 24 hours (86400 seconds), storing up to 500 distinct regional queries in RAM
@cached(cache=TTLCache(maxsize=500, ttl=86400))
def _fetch_hospitals_from_google(rounded_lat: float, rounded_lng: float) -> List[dict]:
    """
    Internal cached method to fetch the raw data from Google Places API v2 (Nearby Search).
    This prevents duplicate identical queries from racking up GCP billing costs.
    """
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        raise ValueError("MAPS_API_KEY not configured")

    # New Places API v2 - Nearby Search (POST)
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.types,places.rating,places.userRatingCount,"
            "places.regularOpeningHours,places.nationalPhoneNumber,places.websiteUri,"
            "places.accessibilityOptions"
        ),
        "Content-Type": "application/json"
    }
    body = {
        "includedTypes": ["hospital", "doctor", "health"],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": rounded_lat, "longitude": rounded_lng},
                "radius": 5000.0
            }
        },
        "rankPreference": "DISTANCE"
    }
    response = requests.post(url, headers=headers, json=body, timeout=10)

    if response.status_code == 200:
        data = response.json()
        raw_places = data.get("places", [])
        # Normalize new API response to a consistent schema for downstream use
        normalized = []
        for p in raw_places:
            loc = p.get("location", {})
            name_obj = p.get("displayName", {})
            oh = p.get("regularOpeningHours", {})
            normalized.append({
                "place_id": p.get("id", ""),
                "name": name_obj.get("text", "Unknown Hospital"),
                "vicinity": p.get("formattedAddress", "Unknown Address"),
                "geometry": {"location": {"lat": loc.get("latitude"), "lng": loc.get("longitude")}},
                "types": p.get("types", []),
                "rating": p.get("rating"),
                "user_ratings_total": p.get("userRatingCount"),
                "opening_hours": {"open_now": oh.get("openNow")} if oh else {},
                # Pre-populated details to avoid a second round-trip
                "_details": {
                    "formatted_phone_number": p.get("nationalPhoneNumber"),
                    "website": p.get("websiteUri"),
                    "rating": p.get("rating"),
                    "user_ratings_total": p.get("userRatingCount"),
                    "wheelchair_accessible_entrance": (p.get("accessibilityOptions") or {}).get("wheelchairAccessibleEntrance"),
                    "opening_hours": {
                        "open_now": oh.get("openNow"),
                        "weekday_text": oh.get("weekdayDescriptions", [])
                    } if oh else {}
                }
            })
        return normalized
    else:
        raise ValueError(f"Google Places API v2 error: HTTP {response.status_code} — {response.text[:200]}")



async def _get_hospitals_cached(rounded_lat: float, rounded_lng: float, orig_lat: float, orig_lng: float) -> HospitalsListResponse:
    try:
        results = _fetch_hospitals_from_google(rounded_lat, rounded_lng)

        hospitals = []
        for place in results:
            geometry = place.get("geometry", {}).get("location", {})
            h_lat = geometry.get("lat")
            h_lng = geometry.get("lng")

            if h_lat is None or h_lng is None:
                continue

            # Compute distance strictly on the *exact* original user coordinates vs the hospital pos
            dist = calculate_distance(orig_lat, orig_lng, h_lat, h_lng)
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

            # Use pre-populated details from the new Places API v2 response (embedded in one round-trip)
            details = place.get("_details") or (fetch_place_details(place_id) if place_id else {})

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

            # Fallback: get open_now from the embedded opening_hours in the place dict
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
            lat=orig_lat,
            lng=orig_lng,
            emergency=False,
            maps_url=f"https://www.google.com/maps/search/hospital/@{orig_lat},{orig_lng},14z",
            phone=None,
            opening_hours=None
        )
        return HospitalsListResponse(hospitals=[fallback])
