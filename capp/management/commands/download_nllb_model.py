from django.core.management.base import BaseCommand
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Downloads and sets up translation models'

    def handle(self, *args, **kwargs):
        # Define model configurations
        models = {
            'nllb': {
                'name': 'facebook/nllb-200-distilled-600M',
                'description': 'NLLB Model for multiple languages'
            },
            'opus': {
                'name': 'Helsinki-NLP/opus-mt-en-sn',
                'description': 'Helsinki OPUS model for English-Shona'
            }
        }
        
        # Set up model directory
        base_dir = os.path.expanduser("~/translation_models")
        os.makedirs(base_dir, exist_ok=True)
        
        for model_key, model_info in models.items():
            try:
                self.stdout.write(f"Downloading {model_key} model...")
                model_path = os.path.join(base_dir, model_key)
                os.makedirs(model_path, exist_ok=True)
                
                # Download model and tokenizer
                tokenizer = AutoTokenizer.from_pretrained(
                    model_info['name'],
                    cache_dir=model_path
                )
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_info['name'],
                    cache_dir=model_path
                )
                
                # Save model and tokenizer
                tokenizer.save_pretrained(model_path)
                model.save_pretrained(model_path)
                
                # Update model info
                model_info['path'] = model_path
                model_info['status'] = 'downloaded'
                
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully downloaded {model_key} model"
                ))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Failed to download {model_key} model: {str(e)}"
                ))
                model_info['status'] = 'failed'
                model_info['error'] = str(e)
        
        # Save configuration
        config_file = os.path.join(base_dir, "models_config.json")
        with open(config_file, 'w') as f:
            json.dump(models, f, indent=4)
        
        self.stdout.write(self.style.SUCCESS(
            f"Configuration saved to {config_file}"
        ))