from typing import List, Tuple

# Records fresher than this are returned from DB without calling OWM.
CACHE_TTL_MINUTES: int = 30

# Sliding window bounds for the background refresh task.
# Records older than STALE_MIN but younger than STALE_MAX are refreshed proactively.
STALE_MIN_MINUTES: int = 30
STALE_MAX_MINUTES: int = 60

# Fixed list of popular cities refreshed every 5 minutes by Celery Beat.
# Stored as (city, country_code) to match the OWM API and DB unique constraint.
POPULAR_CITIES: List[Tuple[str, str]] = [
    ("London", "GB"),
    ("New York", "US"),
    ("Tokyo", "JP"),
    ("Paris", "FR"),
    ("Berlin", "DE"),
    ("Dubai", "AE"),
    ("Sydney", "AU"),
    ("Toronto", "CA"),
    ("Singapore", "SG"),
    ("Moscow", "RU"),
]
