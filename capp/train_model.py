import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer
)
from datasets import Dataset
import pandas as pd
import os

class CustomModelTrainer:
    def __init__(self, base_model_path, output_dir):
        self.base_model_path = base_model_path
        self.output_dir = output_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(base_model_path)
        
        # Move model to GPU if available
        self.model.to(self.device)

    def prepare_dataset(self, csv_path):
        """Load and prepare dataset from CSV file"""
        # CSV should have columns: source_text, target_text, source_lang, target_lang
        df = pd.read_csv(csv_path)
        
        # Convert to HuggingFace dataset
        dataset = Dataset.from_pandas(df)
        
        # Tokenize function
        def tokenize_function(examples):
            source_texts = examples['source_text']
            target_texts = examples['target_text']
            
            # Tokenize source texts
            source_tokenized = self.tokenizer(
                source_texts,
                padding="max_length",
                truncation=True,
                max_length=128,
                return_tensors="pt"
            )
            
            # Tokenize target texts
            target_tokenized = self.tokenizer(
                target_texts,
                padding="max_length",
                truncation=True,
                max_length=128,
                return_tensors="pt"
            )
            
            return {
                'input_ids': source_tokenized['input_ids'],
                'attention_mask': source_tokenized['attention_mask'],
                'labels': target_tokenized['input_ids']
            }
        
        # Apply tokenization
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        return tokenized_dataset

    def train(self, train_dataset, validation_dataset=None, num_epochs=3):
        """Train the model"""
        training_args = Seq2SeqTrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir=f"{self.output_dir}/logs",
            logging_steps=100,
            evaluation_strategy="epoch" if validation_dataset else "no",
            save_strategy="epoch",
            save_total_limit=2,
            load_best_model_at_end=True if validation_dataset else False,
            gradient_accumulation_steps=4,
        )

        # Initialize trainer
        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=validation_dataset,
            tokenizer=self.tokenizer,
            data_collator=DataCollatorForSeq2Seq(
                self.tokenizer,
                model=self.model,
                padding=True
            )
        )

        # Train the model
        trainer.train()

        # Save the final model
        trainer.save_model(f"{self.output_dir}/final")

def main():
    # Define paths
    base_model_path = "facebook/nllb-200-distilled-600M"
    output_dir = "custom_nllb_model"
    
    # Initialize trainer
    trainer = CustomModelTrainer(base_model_path, output_dir)
    
    # Prepare datasets
    print("Loading and preparing datasets...")
    
    # English-Shona dataset
    en_sn_dataset = trainer.prepare_dataset("data/en_sn_dataset.csv")
    
    # Shona-Zulu dataset
    sn_zu_dataset = trainer.prepare_dataset("data/sn_zu_dataset.csv")
    
    # Combine datasets
    combined_dataset = en_sn_dataset.concatenate(sn_zu_dataset)
    
    # Split into train/validation
    split_dataset = combined_dataset.train_test_split(test_size=0.1)
    
    # Train the model
    print("Starting training...")
    trainer.train(
        train_dataset=split_dataset['train'],
        validation_dataset=split_dataset['test'],
        num_epochs=5
    )
    
    print("Training completed!")

if __name__ == "__main__":
    main() 