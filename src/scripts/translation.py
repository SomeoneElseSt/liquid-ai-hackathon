"""
This script translates medical findings from a CSV file from Portuguese to English
using the Gemini API, processing the data sequentially to respect API rate limits.
"""

import os
import time
from pathlib import Path

from google import genai
import pandas as pd
from dotenv import load_dotenv

# --- Constants ---
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
INPUT_CSV_PATH = SRC_DIR / "data/inbreast-csv.csv"
OUTPUT_CSV_PATH = INPUT_CSV_PATH.with_name(f"{INPUT_CSV_PATH.stem}_translated.csv")

COLUMN_TO_TRANSLATE = 'Findings Notes (in Portuguese)'
TRANSLATED_COLUMN_NAME = 'Findings Notes (English)'
MODEL_NAME = "gemini-2.5-flash" # Using a more stable model
MAX_RETRIES = 3
# Delay in seconds to respect free-tier rate limits (10 reqs/min for flash, 2 for pro)
# 60s / 10 reqs = 6s/req. Using 7s to be safe.
REQUEST_DELAY = 7

# --- System Prompt ---
# Translation instructions for medical mammography findings from Portuguese to English
SYSTEM_PROMPT = """
You are a medical translator specializing in radiology and mammography reports.
Your task is to translate Portuguese breast imaging findings into English with complete medical accuracy.

CRITICAL TRANSLATION RULES:
1. Translate ONLY the text provided. Do not add explanations, interpretations, or extra information not present in the source.
2. Maintain the exact clinical meaning and level of detail from the source text.
3. Preserve all medical terminology precisely.
4. Always use FULL, NON-ABBREVIATED terms in the translation. Do not use abbreviations like UOQ, UIQ, LOQ, LIQ, or CC.
5. Use descriptive, complete phrases that provide anatomical context and clinical significance.
6. Standardize the structure: describe location, findings, and characteristics in clear, explicit language.
7. Expand connectors: use "with" or "and" instead of "+" symbols to make findings more explicit.
8. Output ONLY the English translation, nothing else.

STANDARD TERMINOLOGY TRANSLATIONS:
- "nódulo" = "nodule"
- "micro" / "micros" / "microcalcificações" = "microcalcifications"
- "calcificações" = "calcifications"
- "massa" = "mass"
- "opacidade nodular" = "nodular opacity"
- "densidade assimétrica" = "asymmetric density"
- "distorção do estroma" = "stromal distortion"
- "macrocistos" = "macrocysts"
- "fibroadenoma" = "fibroadenoma"
- "follow up" / "follow-up" = "follow-up"
- "exame follow up" = "follow-up examination"
- "benigno" / "benigna" = "benign"
- "cirurgia" = "surgery"
- "pós-cirurgia" = "post-surgery"
- "pós QT" = "post-chemotherapy"
- "biopsado" = "biopsied"
- "artefacto" = "artifact"
- "região espiculada" / "spiculated region" = "spiculated region"
- "cluster" = "cluster"
- "normal" = "normal"

BREAST QUADRANT ABBREVIATIONS (use full terms, not abbreviations):
- "QSE" = "upper outer quadrant"
- "QSI" = "upper inner quadrant"
- "QIE" = "lower outer quadrant"
- "QII" = "lower inner quadrant"
- "TQS" = "upper quadrants"
- "quadrantes internos" = "inner quadrants"

ANATOMICAL TERMS:
- "mama direita" = "right breast"
- "mama esquerda" = "left breast"
- "direita" = "right"
- "esquerda" = "left"
- "junto ao musculo peitoral" = "near the pectoral muscle"
- "cc direita" = "right craniocaudal view"

FORMATTING GUIDELINES:
- Use "with" or "and" to connect findings (never use "+")
- Include clinical context (benign, follow-up, post-surgery, post-chemotherapy, artifact)
- Use complete descriptive phrases

EXAMPLES OF EXPECTED TRANSLATIONS:
- "nódulo + micros" → "nodule with associated microcalcifications"
- "calcificações benignas" → "benign calcifications"
- "nódulo QSE + micros" → "nodule in the upper outer quadrant with associated microcalcifications"
- "densidade assimétrica mama esquerda + micros" → "asymmetric density in the left breast with microcalcifications"
- "follow up com micros" → "follow-up examination showing microcalcifications"
- "nódulo (pós QT)+ micro1" → "nodule (post-chemotherapy) with microcalcifications"
- "nódulo QII" → "nodule in the lower inner quadrant"
- "2 nódulos + micros" → "two nodules with microcalcifications"
- "massa + calcificações" → "mass with calcifications"
- "distorção do estroma QSE - benigna + micros" → "stromal distortion in the upper outer quadrant, benign, with microcalcifications"
- "nódulo QSE - já biopsado - fibroadenoma" → "nodule in the upper outer quadrant, previously biopsied, fibroadenoma"
- "micros - exame follow up - artefacto" → "microcalcifications on follow-up examination, artifact"
- "normal" → "normal examination"
- "normal - follow up" → "normal follow-up examination"

Translate accurately, preserving all clinical detail and meaning.
"""

def clean_input_text(text):
    """Cleans and validates input text before translation."""
    if pd.isna(text):
        return ""
    
    if not isinstance(text, str):
        text = str(text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Remove excessive internal whitespace
    text = " ".join(text.split())
    
    return text

def validate_translation_output(translation):
    """Validates that the translation output is a proper string."""
    if not isinstance(translation, str):
        return False
    
    if not translation.strip():
        return False
    
    # Check if it's an error marker
    if translation.strip() == "[Translation Error]":
        return False
    
    return True

def configure_llm():
    """Loads the API key and configures the generative model."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return None

    os.environ["GEMINI_API_KEY"] = api_key
    client = genai.Client()
    return client

def translate_text(client: genai.Client, text: str, retry_count: int = 0):
    """
    Translates text, using deterministic rules for simple cases.
    Returns a tuple: (translation_string, llm_was_called_boolean).
    """
    cleaned_text = clean_input_text(text)
    
    if not cleaned_text:
        return "", False

    lower_cleaned_text = cleaned_text.lower()
    if lower_cleaned_text == 'normal':
        return "normal examination", False
    if lower_cleaned_text == 'nódulo' or lower_cleaned_text == 'nodulo':
        return "nodule", False
    if lower_cleaned_text == 'micros' or lower_cleaned_text == 'micro':
        return "microcalcifications", False
    # If not a simple case, proceed with LLM translation
    try:
        # Construct the prompt with system instruction
        full_prompt = f"{SYSTEM_PROMPT}\n\nTranslate the following text:\n{cleaned_text}"
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt
        )
        translation = response.text.strip()
        
        if not validate_translation_output(translation):
            if retry_count < MAX_RETRIES:
                print(f"    Warning: Invalid translation output for '{cleaned_text[:30]}...', retrying ({retry_count + 1}/{MAX_RETRIES})...")
                time.sleep(REQUEST_DELAY * (retry_count + 1))
                return translate_text(client, text, retry_count + 1)
            print(f"    Error: Failed to get valid translation for '{cleaned_text[:30]}...' after {MAX_RETRIES} retries")
            return "[Translation Error]", True
        
        return translation, True
    
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) and retry_count < MAX_RETRIES:
            # Longer delay for rate limit errors
            delay = REQUEST_DELAY * (retry_count + 2)
            print(f"    Warning: Rate limit hit. Retrying in {delay}s...")
            time.sleep(delay)
            return translate_text(client, text, retry_count + 1)
        elif retry_count < MAX_RETRIES:
            print(f"    Error during translation: {e}, retrying ({retry_count + 1}/{MAX_RETRIES})...")
            time.sleep(REQUEST_DELAY)
            return translate_text(client, text, retry_count + 1)
        
        print(f"    Error: Translation failed for '{cleaned_text[:30]}...' after {MAX_RETRIES} retries: {e}")
        return "[Translation Error]", True

def main():
    """Main function to orchestrate the translation process."""
    client = configure_llm()
    if not client:
        return

    if not INPUT_CSV_PATH.is_file():
        print(f"Error: Input file not found at {INPUT_CSV_PATH}")
        return

    print(f"Reading data from {INPUT_CSV_PATH}...")
    df = pd.read_csv(INPUT_CSV_PATH)
    
    if COLUMN_TO_TRANSLATE not in df.columns:
        print(f"Error: Column '{COLUMN_TO_TRANSLATE}' not found in the CSV.")
        return
    
    notes_to_translate = df[COLUMN_TO_TRANSLATE].tolist()
    total_rows = len(notes_to_translate)
    all_translations = []

    print(f"Starting sequential translation of {total_rows} rows...")
    
    for i, note in enumerate(notes_to_translate):
        print(f"  - Processing row {i + 1}/{total_rows}...")
        
        translation, llm_used = translate_text(client, note)
        print(f"    -> Row {i + 1} Translation: {translation}")
        all_translations.append(translation)
        
        # Respect the rate limit before the next request, only if LLM was used
        if llm_used and i < total_rows - 1:
            time.sleep(REQUEST_DELAY)
            
    print("Translation complete.")
    
    # Validation statistics
    successful_translations = sum(1 for t in all_translations if validate_translation_output(t))
    empty_translations = sum(1 for t in all_translations if t == "")
    failed_translations = sum(1 for t in all_translations if t == "[Translation Error]")
    
    print(f"\nTranslation Statistics:")
    print(f"  - Total rows: {total_rows}")
    print(f"  - Successful: {successful_translations}")
    print(f"  - Empty (no input): {empty_translations}")
    print(f"  - Failed: {failed_translations}")
    
    df[TRANSLATED_COLUMN_NAME] = all_translations
    
    print(f"\nSaving translated data to {OUTPUT_CSV_PATH}...")
    try:
        df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8')
        print(f"Successfully saved translated file to {OUTPUT_CSV_PATH}")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    main()
