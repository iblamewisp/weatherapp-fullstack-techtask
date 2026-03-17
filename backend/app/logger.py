import logging
import sys
from app.config import settings

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        stream=sys.stdout,
        level=log_level,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )

logger = logging.getLogger("weather_app")
