import json
import logging
import urllib.request
import urllib.parse
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from core.models import VeterinaryClinic
from core.utils import haversine_distance, get_city_coordinates, get_state_coordinates

logger = logging.getLogger(__name__)

class ClinicItem(dict):
    """
    Dictionary supporting both attribute access (clinic.name) and key access (clinic['name']),
    providing complete interoperability between template, view, and test assertions.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ClinicItem' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value


EMERGENCY_KEYWORDS = [
    'emergency', '24x7', '24/7', '24 hours', 'hospital', 'trauma',
    'icu', 'critical care', 'urgency', 'casualty', 'round the clock'
]


def is_emergency_clinic(name, types=None):
    """Detects whether a clinic provides emergency or 24x7 services based on keywords."""
    combined = (name or "").lower()
    if types and isinstance(types, list):
        combined += " " + " ".join(str(t).lower() for t in types)
    return any(keyword in combined for keyword in EMERGENCY_KEYWORDS)


def fetch_google_places_vets(lat, lng, radius_km=10, search_q=None, city=None, state=None):
    """
    Queries Google Places API (New) Text Search with multi-page pagination (up to 60 clinics)
    around (lat, lng) or for a selected city/state.
    Falls back to Places Nearby Search and legacy endpoints if needed.
    Caches successful results for 24 hours to conserve quota and ensure sub-second response times.
    """
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '').strip()
    if not api_key:
        return None

    r_km = radius_km if radius_km is not None else 'all'
    cache_key = f"gplaces_vets_v3_{round(lat, 3) if lat else 0}_{round(lng, 3) if lng else 0}_{r_km}_{city or ''}_{state or ''}_{search_q or ''}".replace(' ', '_')
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # 1. Primary: Try Places API (New) Text Search with multi-page pagination (up to 60 places)
    # Note: places:searchNearby has a hard Google ceiling of 20 results with NO pagination support.
    # places:searchText supports nextPageToken, letting us retrieve all 40-60+ clinics in a city/area.
    url_text_search = "https://places.googleapis.com/v1/places:searchText"
    headers_new = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.currentOpeningHours,places.nationalPhoneNumber,places.types,nextPageToken"
    }

    # Construct intelligent search query
    query_parts = []
    if search_q:
        query_parts.append(search_q.strip())
    query_parts.append("veterinary clinic pet hospital")
    if city:
        query_parts.append(f"in {city.strip()}")
    if state and not city:
        query_parts.append(f"in {state.strip()}")
    elif state and city:
        query_parts.append(state.strip())

    text_query = " ".join(query_parts)

    payload = {
        "textQuery": text_query,
        "pageSize": 20
    }
    if lat is not None and lng is not None:
        r_meters = float((radius_km if radius_km is not None else 30) * 1000)
        # Google Places locationBias circle has a max radius of 50,000 meters
        payload["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": float(lat),
                    "longitude": float(lng)
                },
                "radius": min(r_meters, 50000.0)
            }
        }

    try:
        all_raw_places = []
        seen_place_ids = set()
        page_token = None
        max_pages = 3  # Google Places allows up to 3 pages (up to 60 results)

        for page in range(max_pages):
            req_payload = dict(payload)
            if page_token:
                req_payload["pageToken"] = page_token

            req = urllib.request.Request(url_text_search, data=json.dumps(req_payload).encode('utf-8'), headers=headers_new)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                places = data.get('places', [])
                for p in places:
                    p_id = p.get('id')
                    if p_id and p_id not in seen_place_ids:
                        seen_place_ids.add(p_id)
                        all_raw_places.append(p)
                    elif not p_id:
                        all_raw_places.append(p)

                page_token = data.get('nextPageToken')
                if not page_token or not places:
                    break

        if all_raw_places:
            parsed_clinics = []
            for p in all_raw_places:
                loc = p.get('location', {})
                p_lat = loc.get('latitude')
                p_lng = loc.get('longitude')
                if p_lat is None or p_lng is None:
                    continue

                place_id = p.get('id', '')
                disp = p.get('displayName', {})
                name = disp.get('text') if isinstance(disp, dict) else str(disp or 'Veterinary Clinic')
                formatted_addr = p.get('formattedAddress', '')
                rating = float(p.get('rating', 4.7))
                user_ratings_total = p.get('userRatingCount', 0)
                phone = p.get('nationalPhoneNumber', '')
                is_open = p.get('currentOpeningHours', {}).get('openNow')
                types = p.get('types', [])

                city_name = city or ""
                if not city_name and formatted_addr:
                    parts = [pt.strip() for pt in formatted_addr.split(',')]
                    if len(parts) >= 2:
                        city_name = parts[-3] if len(parts) >= 3 else parts[0]

                parsed_clinics.append(ClinicItem({
                    'id': f"gp_{place_id}",
                    'place_id': place_id,
                    'name': name,
                    'doctor_name': 'Registered Veterinary Surgeon',
                    'specialization': 'Veterinary Medicine & Surgery',
                    'address': formatted_addr,
                    'city': city_name,
                    'state': state or '',
                    'phone_number': phone,
                    'rating': rating,
                    'user_ratings_total': user_ratings_total,
                    'latitude': float(p_lat),
                    'longitude': float(p_lng),
                    'is_24x7_emergency': is_emergency_clinic(name, types),
                    'open_now': is_open,
                    'is_verified': False,
                    'source': 'google_places',
                    'services_offered': 'Veterinary Consultations, Outpatient Care, Vaccinations, Surgery',
                    'maps_url': f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lng}&query_place_id={place_id}"
                }))

            if parsed_clinics:
                cache.set(cache_key, parsed_clinics, timeout=86400)
                return parsed_clinics

    except Exception as e:
        logger.info(f"Places API (New) Text Search attempt note: {e}. Trying searchNearby...")

    # 1b. Fallback: Places API (New) searchNearby
    try:
        url_new = "https://places.googleapis.com/v1/places:searchNearby"
        r_meters = float((radius_km if radius_km is not None else 10) * 1000)
        payload_nearby = {
            "includedTypes": ["veterinary_care"],
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(lat),
                        "longitude": float(lng)
                    },
                    "radius": min(r_meters, 50000.0)
                }
            }
        }
        req = urllib.request.Request(url_new, data=json.dumps(payload_nearby).encode('utf-8'), headers=headers_new)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            places = data.get('places', [])
            parsed_clinics = []
            for p in places:
                loc = p.get('location', {})
                p_lat = loc.get('latitude')
                p_lng = loc.get('longitude')
                if p_lat is None or p_lng is None:
                    continue

                place_id = p.get('id', '')
                disp = p.get('displayName', {})
                name = disp.get('text') if isinstance(disp, dict) else str(disp or 'Veterinary Clinic')
                formatted_addr = p.get('formattedAddress', '')
                rating = float(p.get('rating', 4.7))
                user_ratings_total = p.get('userRatingCount', 0)
                phone = p.get('nationalPhoneNumber', '')
                is_open = p.get('currentOpeningHours', {}).get('openNow')
                types = p.get('types', [])

                city_name = city or ""
                if not city_name and formatted_addr:
                    parts = [pt.strip() for pt in formatted_addr.split(',')]
                    if len(parts) >= 2:
                        city_name = parts[-3] if len(parts) >= 3 else parts[0]

                parsed_clinics.append(ClinicItem({
                    'id': f"gp_{place_id}",
                    'place_id': place_id,
                    'name': name,
                    'doctor_name': 'Registered Veterinary Surgeon',
                    'specialization': 'Veterinary Medicine & Surgery',
                    'address': formatted_addr,
                    'city': city_name,
                    'state': state or '',
                    'phone_number': phone,
                    'rating': rating,
                    'user_ratings_total': user_ratings_total,
                    'latitude': float(p_lat),
                    'longitude': float(p_lng),
                    'is_24x7_emergency': is_emergency_clinic(name, types),
                    'open_now': is_open,
                    'is_verified': False,
                    'source': 'google_places',
                    'services_offered': 'Veterinary Consultations, Outpatient Care, Vaccinations, Surgery',
                    'maps_url': f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lng}&query_place_id={place_id}"
                }))

            if parsed_clinics:
                cache.set(cache_key, parsed_clinics, timeout=86400)
                return parsed_clinics
    except Exception as e:
        logger.info(f"Places API (New) searchNearby attempt note: {e}. Trying legacy fallback...")

    # 2. Secondary Fallback: Legacy Places Nearby Search
    try:
        keyword = f"veterinary clinic pet hospital {search_q}".strip() if search_q else "veterinary clinic pet hospital"
        params = {
            'location': f"{lat},{lng}",
            'radius': int(radius_meters),
            'type': 'veterinary_care',
            'keyword': keyword,
            'key': api_key
        }
        query_string = urllib.parse.urlencode(params)
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?{query_string}"
        req = urllib.request.Request(url, headers={'User-Agent': 'K9Match-Places-Radar/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') in ('OK', 'ZERO_RESULTS'):
                results = data.get('results', [])
                parsed_clinics = []
                for place in results:
                    p_lat = place.get('geometry', {}).get('location', {}).get('lat')
                    p_lng = place.get('geometry', {}).get('location', {}).get('lng')
                    if p_lat is None or p_lng is None:
                        continue
                    place_id = place.get('place_id', '')
                    name = place.get('name', 'Veterinary Clinic')
                    vicinity = place.get('vicinity', '')
                    rating = float(place.get('rating', 4.7))
                    parsed_clinics.append(ClinicItem({
                        'id': f"gp_{place_id}",
                        'place_id': place_id,
                        'name': name,
                        'doctor_name': 'Registered Veterinary Surgeon',
                        'specialization': 'Veterinary Medicine & Surgery',
                        'address': vicinity,
                        'city': vicinity.split(',')[-1].strip() if ',' in vicinity else '',
                        'state': '',
                        'phone_number': '',
                        'rating': rating,
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'latitude': float(p_lat),
                        'longitude': float(p_lng),
                        'is_24x7_emergency': is_emergency_clinic(name, place.get('types', [])),
                        'open_now': place.get('opening_hours', {}).get('open_now'),
                        'is_verified': False,
                        'source': 'google_places',
                        'services_offered': 'Veterinary Consultations, Outpatient Care, Vaccinations, Surgery',
                        'maps_url': f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lng}&query_place_id={place_id}"
                    }))
                cache.set(cache_key, parsed_clinics, timeout=86400)
                return parsed_clinics
    except Exception as e:
        logger.warning(f"Google Places legacy fallback failed: {e}")

    return None


def fetch_osm_overpass_vets(lat, lng, radius_km=10):
    """
    Fallback: Queries OpenStreetMap Overpass API for veterinary amenities.
    Strict 4-second timeout to avoid any page latency.
    """
    r_km = radius_km if radius_km is not None else 10
    radius_meters = int(r_km * 1000)
    cache_key = f"osm_vets_{round(lat, 3)}_{round(lng, 3)}_{radius_meters}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    query = f"""
    [out:json][timeout:5];
    (
      node["amenity"="veterinary"](around:{radius_meters},{lat},{lng});
      way["amenity"="veterinary"](around:{radius_meters},{lat},{lng});
    );
    out center body;
    """
    url = "https://overpass-api.de/api/interpreter"
    req = urllib.request.Request(url, data=query.encode('utf-8'), headers={'User-Agent': 'K9Match-App/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elements = data.get('elements', [])
            parsed = []
            for el in elements:
                tags = el.get('tags', {})
                name = tags.get('name') or tags.get('operator') or 'Veterinary Clinic'
                c_lat = el.get('lat') or el.get('center', {}).get('lat')
                c_lng = el.get('lon') or el.get('center', {}).get('lon')
                if not c_lat or not c_lng:
                    continue
                parsed.append(ClinicItem({
                    'id': f"osm_{el.get('id')}",
                    'name': name,
                    'doctor_name': tags.get('operator', 'Licensed Veterinarian'),
                    'specialization': 'Veterinary Care',
                    'address': tags.get('addr:street', tags.get('addr:suburb', 'Local Area')),
                    'city': tags.get('addr:city', ''),
                    'phone_number': tags.get('phone', tags.get('contact:phone', '')),
                    'rating': 4.6,
                    'latitude': float(c_lat),
                    'longitude': float(c_lng),
                    'is_24x7_emergency': is_emergency_clinic(name),
                    'is_verified': False,
                    'source': 'osm',
                    'maps_url': f"https://www.google.com/maps/dir/?api=1&destination={c_lat},{c_lng}"
                }))
            cache.set(cache_key, parsed, timeout=86400)
            return parsed
    except Exception:
        return []


def get_nearby_vets_dynamic(lat=None, lng=None, radius_km=10, search_q=None, emergency_only=False, city=None, state=None):
    """
    Unified Veterinary Discovery Engine:
    1. If Google Places API key is present, calls live Google Places Nearby Search.
       Merges results with local verified partner clinics.
    2. If no key is set or Google is unavailable, gracefully falls back to:
       - Local database of verified clinics with live haversine distance calculation.
       - Any OpenStreetMap Overpass entries found in the area.
    Never fails or throws unhandled exceptions.
    """
    ref_lat = lat
    ref_lng = lng

    # 1. Resolve coordinates from city or state if not directly provided
    if (ref_lat is None or ref_lng is None) and city:
        c_lat, c_lng = get_city_coordinates(city)
        if c_lat and c_lng:
            ref_lat, ref_lng = c_lat, c_lng

    if (ref_lat is None or ref_lng is None) and state:
        s_lat, s_lng = get_state_coordinates(state)
        if s_lat and s_lng:
            ref_lat, ref_lng = s_lat, s_lng

    # 2. Check if Google Places API is configured
    api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '').strip()
    google_places_active = False
    clinics_list = []

    if ref_lat is not None and ref_lng is not None and api_key:
        google_results = fetch_google_places_vets(ref_lat, ref_lng, radius_km=radius_km, search_q=search_q, city=city, state=state)
        if google_results is not None:
            google_places_active = True
            clinics_list = google_results

    # 3. If Google Places gave results, cross-reference with local verified partner clinics
    if google_places_active:
        # Load local database partner clinics to highlight them
        db_qs = VeterinaryClinic.objects.all()
        if city:
            db_qs = db_qs.filter(city__iexact=city)
        elif state:
            db_qs = db_qs.filter(state__iexact=state)

        partner_clinics = []
        for db_c in db_qs:
            c_lat = db_c.latitude
            c_lng = db_c.longitude
            if not c_lat or not c_lng:
                c_lat, c_lng = get_city_coordinates(db_c.city)
            if not c_lat or not c_lng:
                continue

            partner_clinics.append(ClinicItem({
                'id': f"db_{db_c.id}",
                'name': db_c.name,
                'doctor_name': db_c.doctor_name,
                'specialization': db_c.specialization or "Canine Care",
                'address': f"{db_c.address}, {db_c.city}",
                'city': db_c.city,
                'state': db_c.state or '',
                'phone_number': db_c.phone_number,
                'rating': float(db_c.rating) if db_c.rating else 4.9,
                'user_ratings_total': 50,
                'latitude': float(c_lat),
                'longitude': float(c_lng),
                'is_24x7_emergency': bool(db_c.is_24x7_emergency),
                'is_verified': True,
                'source': 'k9match_verified',
                'services_offered': db_c.services_offered,
                'maps_url': f"https://www.google.com/maps/dir/?api=1&destination={c_lat},{c_lng}"
            }))

        # Merge partner clinics first, avoiding duplicate names
        existing_names = {c['name'].lower().strip() for c in clinics_list}
        for p in partner_clinics:
            if p['name'].lower().strip() not in existing_names:
                clinics_list.insert(0, p)
            else:
                # Mark matching clinic as verified partner
                for c in clinics_list:
                    if c['name'].lower().strip() == p['name'].lower().strip():
                        c['is_verified'] = True
                        c['doctor_name'] = p['doctor_name']
                        c['phone_number'] = p['phone_number'] or c.get('phone_number', '')

    else:
        # Fallback: Query local database
        db_qs = VeterinaryClinic.objects.all()
        if state:
            db_qs = db_qs.filter(state__iexact=state)
        if city:
            db_qs = db_qs.filter(city__iexact=city)
        if search_q:
            db_qs = db_qs.filter(
                Q(name__icontains=search_q) |
                Q(doctor_name__icontains=search_q) |
                Q(specialization__icontains=search_q) |
                Q(address__icontains=search_q) |
                Q(city__icontains=search_q) |
                Q(services_offered__icontains=search_q)
            )

        for db_c in db_qs:
            c_lat = db_c.latitude
            c_lng = db_c.longitude
            if not c_lat or not c_lng:
                c_lat, c_lng = get_city_coordinates(db_c.city)

            clinics_list.append(ClinicItem({
                'id': f"db_{db_c.id}",
                'name': db_c.name,
                'doctor_name': db_c.doctor_name,
                'specialization': db_c.specialization or "Canine Care",
                'address': f"{db_c.address}, {db_c.city}",
                'city': db_c.city,
                'state': db_c.state or '',
                'phone_number': db_c.phone_number,
                'rating': float(db_c.rating) if db_c.rating else 4.8,
                'latitude': float(c_lat) if c_lat is not None else None,
                'longitude': float(c_lng) if c_lng is not None else None,
                'is_24x7_emergency': bool(db_c.is_24x7_emergency),
                'is_verified': True,
                'source': 'database',
                'services_offered': db_c.services_offered,
                'maps_url': f"https://www.google.com/maps/dir/?api=1&destination={c_lat},{c_lng}" if (c_lat and c_lng) else ""
            }))

        # Also attempt OSM Overpass if coordinates are available, no specific city/state filter, and local count is 0
        if ref_lat is not None and ref_lng is not None and not city and not state and len(clinics_list) == 0:
            osm_results = fetch_osm_overpass_vets(ref_lat, ref_lng, radius_km=radius_km)
            existing_names = {c['name'].lower().strip() for c in clinics_list}
            for osm_c in osm_results:
                if osm_c['name'].lower().strip() not in existing_names:
                    clinics_list.append(ClinicItem(osm_c))

    # 4. Calculate Distance and Sort
    for c in clinics_list:
        c_lat = c.get('latitude')
        c_lng = c.get('longitude')
        if ref_lat is not None and ref_lng is not None and c_lat is not None and c_lng is not None:
            dist = haversine_distance(ref_lat, ref_lng, c_lat, c_lng)
            c['distance_km'] = round(dist, 1) if dist is not None else None
        else:
            c['distance_km'] = None

    if ref_lat is not None and ref_lng is not None:
        clinics_list.sort(key=lambda c: (c['distance_km'] is None, c['distance_km'] if c['distance_km'] is not None else float('inf')))

    # 5. Apply emergency filter if requested
    if emergency_only:
        clinics_list = [c for c in clinics_list if c.get('is_24x7_emergency')]

    # 6. Apply radius boundary if provided
    has_expanded_fallback = False
    max_fallback_dist = None
    if radius_km and ref_lat is not None and ref_lng is not None:
        filtered_by_radius = [c for c in clinics_list if c['distance_km'] is not None and c['distance_km'] <= radius_km]
        if not filtered_by_radius and clinics_list:
            # Smart expanded fallback: never leave user empty-handed
            has_expanded_fallback = True
            valid_pool = [c for c in clinics_list if c['distance_km'] is not None]
            if valid_pool:
                clinics_list = valid_pool[:6]
                max_fallback_dist = max(c['distance_km'] for c in clinics_list)
        else:
            clinics_list = filtered_by_radius

    return {
        'status': 'success',
        'source': 'google_places' if google_places_active else 'database_and_osm',
        'google_places_active': google_places_active,
        'google_places_configured': bool(api_key),
        'center': {'lat': ref_lat, 'lng': ref_lng} if (ref_lat and ref_lng) else None,
        'radius_km': radius_km,
        'has_expanded_fallback': has_expanded_fallback,
        'max_fallback_dist': max_fallback_dist,
        'total_count': len(clinics_list),
        'clinics': clinics_list
    }
