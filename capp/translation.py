# translation.py
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import time
from .models import TranslationMetric
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class Translator:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Translator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Translator._initialized:
            self.model = None
            self.tokenizer = None
            self.model_name = settings.NLLB_SETTINGS['MODEL_NAME']
            self.initialize()
            Translator._initialized = True

    def initialize(self):
        """Initialize the NLLB model"""
        try:
            # Use CUDA if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")

            # Load model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(device)
            
            # Keep model in evaluation mode
            self.model.eval()
            logger.info("NLLB model loaded successfully")
        except Exception as e:
            logger.error(f"Error initializing NLLB model: {str(e)}")

    def translate_text(self, text, source_code, target_code):
        """Translate text using NLLB model"""
        if not text or not source_code or not target_code:
            return text

        start_time = time.time()
        try:
            # Create translation pipeline (reusing existing model and tokenizer)
            translator = pipeline('translation', 
                               model=self.model, 
                               tokenizer=self.tokenizer,
                               src_lang=source_code,
                               tgt_lang=target_code)

            # Perform translation
            output = translator(text, 
                             max_length=settings.NLLB_SETTINGS['MAX_LENGTH'],
                             num_beams=settings.NLLB_SETTINGS['NUM_BEAMS'],
                             early_stopping=settings.NLLB_SETTINGS['EARLY_STOPPING'])
            
            translated = output[0]['translation_text']

            # Store metrics asynchronously
            self.store_metrics(text, translated, source_code, target_code, start_time)
            
            return translated

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return text

    def store_metrics(self, original_text, translated_text, source_code, target_code, start_time):
        """Store translation metrics"""
        try:
            translation_time = time.time() - start_time
            
            TranslationMetric.objects.create(
                source_language=source_code,
                target_language=target_code,
                original_text=original_text,
                translated_text=translated_text,
                translation_time=translation_time,
                character_count=len(original_text),
                word_count=len(original_text.split()),
                confidence_score=0.8,
                success=True
            )
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
