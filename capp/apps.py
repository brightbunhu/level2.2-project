from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'capp'

    def ready(self):
        try:
            # Initialize translator when Django starts
            from .translation import Translator
            Translator()
            logger.info("Translator initialized during app startup")
        except Exception as e:
            logger.error(f"Error initializing translator during startup: {str(e)}")
