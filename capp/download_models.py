import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from huggingface_hub import snapshot_download
import json

class ModelDownloader:
    def __init__(self):
        self.models_config = {
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
        self.base_dir = os.path.expanduser("~/translation_models")
        self.config_file = os.path.join(self.base_dir, "models_config.json")

    def download_models(self):
        """Download all configured models"""
        os.makedirs(self.base_dir, exist_ok=True)
        
        for model_key, model_info in self.models_config.items():
            try:
                print(f"\nDownloading {model_key} model...")
                model_path = os.path.join(self.base_dir, model_key)
                
                # Download model files
                snapshot_download(
                    repo_id=model_info['name'],
                    local_dir=model_path,
                    local_dir_use_symlinks=False
                )
                
                # Test load the model
                self.test_model(model_key, model_path)
                
                # Update model info
                model_info['path'] = model_path
                model_info['status'] = 'downloaded'
                print(f"Successfully downloaded {model_key} model")
                
            except Exception as e:
                print(f"Error downloading {model_key} model: {str(e)}")
                model_info['status'] = 'failed'
                model_info['error'] = str(e)
        
        # Save configuration
        self.save_config()

    def test_model(self, model_key, model_path):
        """Test if model can be loaded"""
        print(f"Testing {model_key} model...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
            
            # Test tokenizer and model with sample text
            if model_key == 'nllb':
                test_input = "Hello, how are you?"
                inputs = tokenizer(test_input, return_tensors="pt")
                outputs = model.generate(**inputs, forced_bos_token_id=tokenizer.lang_code_to_id['sna_Latn'])
            else:  # opus model
                test_input = "Hello, how are you?"
                inputs = tokenizer(test_input, return_tensors="pt")
                outputs = model.generate(**inputs)
            
            decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            print(f"Test translation successful: {decoded[0]}")
            
        except Exception as e:
            print(f"Error testing {model_key} model: {str(e)}")
            raise

    def save_config(self):
        """Save model configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.models_config, f, indent=4)
        print(f"\nConfiguration saved to {self.config_file}")

    def get_model_path(self, model_key):
        """Get path for a specific model"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config[model_key]['path']
        except:
            return None

def main():
    downloader = ModelDownloader()
    
    print("Starting model downloads...")
    print("This may take some time depending on your internet connection.")
    print("Models will be saved to:", downloader.base_dir)
    
    downloader.download_models()
    
    print("\nDownload Summary:")
    with open(downloader.config_file, 'r') as f:
        config = json.load(f)
        for model_key, info in config.items():
            status = info['status']
            print(f"{model_key}: {status}")
            if status == 'failed':
                print(f"  Error: {info.get('error', 'Unknown error')}")
            else:
                print(f"  Path: {info['path']}")

if __name__ == "__main__":
    main() 