"""
mammography_inference.py
Run inference with fine-tuned LFM2-VL-1.6B mammography model
"""

import csv
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import torch
import argparse

class MammographyAssistant:
    def __init__(self, model_path):
        """
        Initialize the fine-tuned mammography model
        
        Args:
            model_path: Path to fine-tuned checkpoint
                       (e.g., './mammography-finetune-4/checkpoint-final')
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading model and processor onto {self.device}...")
        
        # Load fine-tuned model in full precision (float32) for CPU compatibility
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            trust_remote_code=True
        ).to(self.device)
        
        self.processor = AutoProcessor.from_pretrained(
            model_path, 
            trust_remote_code=True
        )
        print("✓ Model loaded")
    
    def analyze_mammogram(self, image_path, custom_prompt=None):
        """ 
        Analyze a mammogram image
        
        Args:
            image_path: Path to mammogram image
            custom_prompt: Optional custom prompt (uses default if None)
        
        Returns:
            str: Model's analysis
        """
        # Load image
        image = Image.open(image_path).convert('RGB')
        
        # Default prompt matching your fine-tuning format
        if custom_prompt is None:
            custom_prompt = "Please provide a complete radiological assessment of this mammogram. Include the BI-RADS category, detailed finding notes, your diagnosis, and any recommended next steps."
        
        # Create conversation
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": custom_prompt}
                ]
            }
        ]
        
        # Prepare inputs
        inputs = self.processor.apply_chat_template(
            conversation,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            tokenize=True
        ).to(self.model.device)
        
        # Generate response
        print("Analyzing mammogram...")
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False, 
                temperature=None,
                min_p=None,
                repetition_penalty=None
            )
        
        # Decode and return
        response = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
        # Clean up the response to only get the assistant's answer
        if "assistant\n" in response:
            response = response.split("assistant\n")[1].strip()
        return response
    
    def batch_analyze(self, image_paths, csv_writer):
        """
        Analyze multiple mammograms and write results to a CSV file row by row.
        
        Args:
            image_paths: List of paths to mammogram images.
            csv_writer: A csv.writer object to write results.
        """
        for i, img_path in enumerate(image_paths, 1):
            print(f"\n[{i}/{len(image_paths)}] Analyzing: {img_path}")
            
            try:
                analysis = self.analyze_mammogram(img_path)
                print(f"-> Analysis result: {analysis[:120]}...") # Print a snippet
                
                # Extract image ID and write to CSV
                image_id = os.path.basename(img_path).split('_')[0]
                csv_writer.writerow([image_id, analysis])
                
            except Exception as e:
                print(f"!! Failed to analyze {img_path}: {e}")
                image_id = os.path.basename(img_path).split('_')[0]
                csv_writer.writerow([image_id, f"ERROR: {e}"])

# Example usage
if __name__ == "__main__":
    import os

    # Get the absolute path of the script's directory
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Get the project root (which is two levels up from src/scripts)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    # Hardcoded model path for mamography-finetune-8
    MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "mamography-finetune-8", "merged_model")
    # Define the output CSV path
    RESULTS_CSV_PATH = os.path.join(PROJECT_ROOT, "mammography_results.csv")
    
    # Check if the model path exists
    if not os.path.isdir(MODEL_PATH):
        print(f"Error: Model directory not found at '{MODEL_PATH}'")
        print("Please make sure the model is located at 'models/mamography-finetune-8/merged_model'")
        exit(1)

    print(f"Using model: {MODEL_PATH}")
    
    # Initialize assistant
    assistant = MammographyAssistant(MODEL_PATH)
    
    # Construct absolute paths for all test images
    test_images_dir = os.path.join(PROJECT_ROOT, "src", "data", "test-set", "images")
    test_images = sorted([os.path.join(test_images_dir, f) for f in os.listdir(test_images_dir) if f.endswith(".jpg")])

    # Open CSV file and start batch analysis
    try:
        with open(RESULTS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Image ID", "Analysis"])

            print("\n" + "="*60)
            print(f"Batch Analysis Started: Writing results to {RESULTS_CSV_PATH}")
            print("="*60)
            
            assistant.batch_analyze(test_images, writer)

        print(f"\n✓ Batch analysis complete. Results saved to {RESULTS_CSV_PATH}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
