from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tests translation models with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-file',
            type=str,
            help='Path to test data file',
            default='test_data/language_pairs.json'
        )

    def handle(self, *args, **kwargs):
        test_file = kwargs['test_file']
        
        if not os.path.exists(test_file):
            self.stdout.write(self.style.ERROR(
                f"Test file not found: {test_file}"
            ))
            return
        
        try:
            # Load test data
            with open(test_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            # Load models
            models = self.load_models()
            if not models:
                self.stdout.write(self.style.ERROR("No models available for testing"))
                return
            
            # Test each model
            results = {}
            for model_name, model_info in models.items():
                self.stdout.write(f"Testing {model_name} model...")
                model_results = self.test_model(model_info, test_data['test_pairs'])
                results[model_name] = model_results
            
            # Generate report
            self.generate_report(results)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during testing: {str(e)}"))

    def load_models(self):
        """Load available translation models"""
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
                    self.stdout.write(f"Loaded {model_key} model")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading models: {str(e)}"))
            
        return models

    def test_model(self, model_info, test_pairs):
        """Test a single model on test data"""
        results = {
            'translations': [],
            'metrics': {
                'exact_matches': 0,
                'total_tests': len(test_pairs)
            }
        }
        
        tokenizer = model_info['tokenizer']
        model = model_info['model']
        
        for pair in test_pairs:
            try:
                # Prepare input
                inputs = tokenizer(pair['source_text'], return_tensors="pt", padding=True)
                
                # Generate translation
                outputs = model.generate(
                    **inputs,
                    forced_bos_token_id=tokenizer.lang_code_to_id[pair['target_lang']],
                    max_length=128,
                    num_beams=5,
                    early_stopping=True
                )
                
                # Decode translation
                translated = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
                
                # Calculate metrics
                exact_match = 1 if translated.lower() == pair['target_text'].lower() else 0
                results['metrics']['exact_matches'] += exact_match
                
                # Store translation
                results['translations'].append({
                    'source': pair['source_text'],
                    'reference': pair['target_text'],
                    'translation': translated,
                    'exact_match': exact_match
                })
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Error translating: {pair['source_text']} - {str(e)}"
                ))
        
        # Calculate accuracy
        results['metrics']['accuracy'] = (
            results['metrics']['exact_matches'] / results['metrics']['total_tests']
        )
        
        return results

    def generate_report(self, results):
        """Generate HTML report with test results"""
        report = """
        <html>
        <head>
            <title>Translation Model Test Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f5f5f5; }
                .model-section { margin-bottom: 30px; }
                .metrics { margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <h1>Translation Model Test Results</h1>
        """
        
        for model_name, model_results in results.items():
            report += f"""
            <div class="model-section">
                <h2>{model_name} Model Results</h2>
                <div class="metrics">
                    <h3>Overall Metrics</h3>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                        <tr>
                            <td>Accuracy (Exact Matches)</td>
                            <td>{model_results['metrics']['accuracy']:.2%}</td>
                        </tr>
                        <tr>
                            <td>Total Tests</td>
                            <td>{model_results['metrics']['total_tests']}</td>
                        </tr>
                    </table>
                </div>
                
                <h3>Translation Examples</h3>
                <table>
                    <tr>
                        <th>Source</th>
                        <th>Reference</th>
                        <th>Translation</th>
                        <th>Exact Match</th>
                    </tr>
            """
            
            for translation in model_results['translations']:
                report += f"""
                    <tr>
                        <td>{translation['source']}</td>
                        <td>{translation['reference']}</td>
                        <td>{translation['translation']}</td>
                        <td>{'Yes' if translation['exact_match'] else 'No'}</td>
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
        
        # Save report
        with open('model_test_report.html', 'w', encoding='utf-8') as f:
            f.write(report)
            
        self.stdout.write(self.style.SUCCESS(
            "Test report generated: model_test_report.html"
        ))