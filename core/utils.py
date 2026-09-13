import math

# Coordinate mapping for major Indian cities
INDIAN_CITY_COORDINATES = {
    'mumbai': (19.0760, 72.8777),
    'delhi': (28.6139, 77.2090),
    'new delhi': (28.6139, 77.2090),
    'bengaluru': (12.9716, 77.5946),
    'bangalore': (12.9716, 77.5946),
    'hyderabad': (17.3850, 78.4867),
    'chennai': (13.0827, 80.2707),
    'kolkata': (22.5726, 88.3639),
    'pune': (18.5204, 73.8567),
    'ahmedabad': (23.0225, 72.5714),
    'jaipur': (26.9124, 75.7873),
    'surat': (21.1702, 72.8311),
    'lucknow': (26.8467, 80.9462),
    'kanpur': (26.4499, 80.3319),
    'nagpur': (21.1458, 79.0882),
    'indore': (22.7196, 75.8577),
    'thane': (19.2183, 72.9781),
    'bhopal': (23.2599, 77.4126),
    'visakhapatnam': (17.6868, 83.2185),
    'patna': (25.5941, 85.1376),
    'vadodara': (22.3072, 73.1812),
    'ghaziabad': (28.6692, 77.4538),
    'ludhiana': (30.9010, 75.8573),
    'agra': (27.1767, 78.0081),
    'nashik': (19.9975, 73.7898),
    'faridabad': (28.4089, 77.3178),
    'meerut': (28.9845, 77.7064),
    'rajkot': (22.3039, 70.8022),
    'varanasi': (25.3176, 82.9739),
    'srinagar': (34.0837, 74.7973),
    'aurangabad': (19.8762, 75.3433),
    'dhanbad': (23.7957, 86.4304),
    'amritsar': (31.6340, 74.8723),
    'navi mumbai': (19.0330, 73.0297),
    'allahabad': (25.4358, 81.8463),
    'prayagraj': (25.4358, 81.8463),
    'ranchi': (23.3441, 85.3096),
    'howrah': (22.5958, 88.2636),
    'coimbatore': (11.0168, 76.9558),
    'jabalpur': (23.1815, 79.9864),
    'gwalior': (26.2183, 78.1828),
    'vijayawada': (16.5062, 80.6480),
    'jodhpur': (26.2389, 73.0243),
    'madurai': (9.9252, 78.1198),
    'raipur': (21.2514, 81.6296),
    'kota': (25.2138, 75.8648),
    'chandigarh': (30.7333, 76.7794),
    'guwahati': (26.1445, 91.7362),
    'solapur': (17.6599, 75.9064),
    'mysore': (12.2958, 76.6394),
    'mysuru': (12.2958, 76.6394),
    'gurgaon': (28.4595, 77.0266),
    'gurugram': (28.4595, 77.0266),
    'noida': (28.5355, 77.3910),
    'kochi': (9.9312, 76.2673),
    'dehradun': (30.3165, 78.0322),
    'mangalore': (12.9141, 74.8560),
    'bhubaneswar': (20.2961, 85.8245),
}

def get_city_coordinates(city_name):
    """
    Returns (latitude, longitude) tuple for a given city name if found in coordinates dictionary.
    """
    if not city_name:
        return None, None
    
    clean_name = city_name.strip().lower()
    if clean_name in INDIAN_CITY_COORDINATES:
        return INDIAN_CITY_COORDINATES[clean_name]
    
    # Try partial match if city is part of key or vice versa
    for key, coords in INDIAN_CITY_COORDINATES.items():
        if key in clean_name or clean_name in key:
            return coords
            
    return None, None


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on the Earth (in km)
    using the Haversine formula.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (ValueError, TypeError):
        return None

    R = 6371.0  # Earth's radius in kilometers

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 1)
