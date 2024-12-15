import json
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.meteor_score import meteor_score
import nltk
from tqdm import tqdm
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
import logging
from django.conf import settings
import os

# Download required NLTK data
nltk.download('wordnet')
nltk.download('punkt')

logger = logging.getLogger(__name__)

class ModelEvaluator:
    def __init__(self):
        self.models = self.load_models()
        self.test_data = self.load_test_data()
        self.metrics = {}

    def load_models(self):
        """Load all available translation models"""
        models = {}
        config_file = settings.TRANSLATION_MODELS['CONFIG_FILE']
        
        try:
            with open(config_file, 'r') as f:
                models_config = json.load(f)
                
            for model_key, info in models_config.items():
                if info['status'] == 'downloaded':
                    models[model_key] = {
                        'tokenizer': AutoTokenizer.from_pretrained(info['path']),
                        'model': AutoModelForSeq2SeqLM.from_pretrained(info['path'])
                    }
                    logger.info(f"Loaded {model_key} model")
                    
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            
        return models

    def load_test_data(self, file_path='test_data/language_pairs.json'):
        """Load test data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading test data: {str(e)}")
            return []

    def translate_text(self, model_key, text, source_lang, target_lang):
        """Translate text using specified model"""
        try:
            model_info = self.models[model_key]
            tokenizer = model_info['tokenizer']
            model = model_info['model']

            # Prepare input
            inputs = tokenizer(text, return_tensors="pt", padding=True)
            
            # Generate translation
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.lang_code_to_id[target_lang],
                max_length=128,
                num_beams=5,
                early_stopping=True
            )
            
            # Decode translation
            translated = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            return translated
            
        except Exception as e:
            logger.error(f"Translation error with {model_key}: {str(e)}")
            return None

    def calculate_metrics(self, reference, candidate):
        """Calculate basic translation metrics"""
        try:
            # Simple exact match
            exact_match = 1 if reference.lower() == candidate.lower() else 0
            
            # Word overlap score
            ref_words = set(reference.lower().split())
            cand_words = set(candidate.lower().split())
            overlap = len(ref_words.intersection(cand_words)) / len(ref_words)
            
            # Length ratio
            length_ratio = len(candidate) / len(reference)
            
            return {
                'exact_match': exact_match,
                'word_overlap': overlap,
                'length_ratio': length_ratio
            }
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return None

    def evaluate_models(self):
        """Evaluate all models on test data"""
        results = {}
        
        for model_key in self.models:
            logger.info(f"Evaluating {model_key} model...")
            model_results = {
                'translations': [],
                'metrics': {
                    'bleu_scores': [],
                    'meteor_scores': [],
                    'exact_matches': []
                }
            }
            
            for pair in tqdm(self.test_data):
                source_text = pair['source_text']
                target_text = pair['target_text']
                source_lang = pair['source_lang']
                target_lang = pair['target_lang']
                
                # Get translation
                translated = self.translate_text(
                    model_key, 
                    source_text, 
                    source_lang, 
                    target_lang
                )
                
                if translated:
                    # Calculate metrics
                    metrics = self.calculate_metrics(target_text, translated)
                    
                    if metrics:
                        model_results['translations'].append({
                            'source': source_text,
                            'reference': target_text,
                            'translation': translated,
                            'metrics': metrics
                        })
                        
                        model_results['metrics']['bleu_scores'].append(metrics['bleu'])
                        model_results['metrics']['meteor_scores'].append(metrics['meteor'])
                        model_results['metrics']['exact_matches'].append(metrics['exact_match'])
            
            # Calculate average scores
            results[model_key] = {
                'avg_bleu': sum(model_results['metrics']['bleu_scores']) / len(model_results['metrics']['bleu_scores']),
                'avg_meteor': sum(model_results['metrics']['meteor_scores']) / len(model_results['metrics']['meteor_scores']),
                'accuracy': sum(model_results['metrics']['exact_matches']) / len(model_results['metrics']['exact_matches']),
                'translations': model_results['translations']
            }
            
        return results

    def generate_report(self, results, output_file='model_evaluation_report.html'):
        """Generate HTML report with evaluation results"""
        report = """
        <html>
        <head>
            <title>Translation Model Evaluation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f5f5f5; }
                .model-section { margin-bottom: 30px; }
                .metrics { margin-bottom: 20px; }
                .translation-example { background-color: #f9f9f9; padding: 10px; margin: 5px 0; }
            </style>
        </head>
        <body>
            <h1>Translation Model Evaluation Report</h1>
        """
        
        for model_key, model_results in results.items():
            report += f"""
            <div class="model-section">
                <h2>{model_key} Model Results</h2>
                <div class="metrics">
                    <h3>Overall Metrics</h3>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Score</th>
                        </tr>
                        <tr>
                            <td>Average BLEU Score</td>
                            <td>{model_results['avg_bleu']:.4f}</td>
                        </tr>
                        <tr>
                            <td>Average METEOR Score</td>
                            <td>{model_results['avg_meteor']:.4f}</td>
                        </tr>
                        <tr>
                            <td>Accuracy (Exact Matches)</td>
                            <td>{model_results['accuracy']:.4f}</td>
                        </tr>
                    </table>
                </div>
                
                <h3>Translation Examples</h3>
                <table>
                    <tr>
                        <th>Source</th>
                        <th>Reference</th>
                        <th>Translation</th>
                        <th>BLEU</th>
                        <th>METEOR</th>
                    </tr>
            """
            
            # Add some example translations
            for translation in model_results['translations'][:10]:  # Show first 10 examples
                report += f"""
                    <tr>
                        <td>{translation['source']}</td>
                        <td>{translation['reference']}</td>
                        <td>{translation['translation']}</td>
                        <td>{translation['metrics']['bleu']:.4f}</td>
                        <td>{translation['metrics']['meteor']:.4f}</td>
                    </tr>
                """
                
            report += """
                </table>
            </div>
            """
            
        report += """
        </body>
        </html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        logger.info(f"Evaluation report saved to {output_file}")

def main():
    # Example test data format
    test_data = [
        {
            "source_text": "Hello, how are you?",
            "target_text": "Mhoro, makadii?",
            "source_lang": "eng_Latn",
            "target_lang": "sna_Latn"
        },
        # Add more test pairs...
    ]
    
    # Save test data
    os.makedirs('test_data', exist_ok=True)
    with open('test_data/language_pairs.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2)
    
    # Run evaluation
    evaluator = ModelEvaluator()
    results = evaluator.evaluate_models()
    evaluator.generate_report(results)

if __name__ == "__main__":
    main() 