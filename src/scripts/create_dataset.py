import os
import csv
import json
import random
import logging
import shutil
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

WORKSPACE_ROOT = Path(
    "/Users/steve/Documents/Files/Minerva/Internships & Hackathons/Hackathons/liquid-ai-hackathon"
)
CSV_FILE_PATH = WORKSPACE_ROOT / "src" / "data" / "inbreast-csv-translated.csv"
IMAGES_DIR = WORKSPACE_ROOT / "src" / "data" / "images_jpg"
OUTPUT_DIR = WORKSPACE_ROOT / "src" / "data"
TEST_SET_DIR = WORKSPACE_ROOT / "src" / "data" / "test-set"

TRAINING_JSONL_FILE = OUTPUT_DIR / "dataset.jsonl"
TEST_SET_CSV_FILE = TEST_SET_DIR / "test_set.csv"

LAMBDA_IMAGE_BASE_PATH = "/home/ubuntu/data/images"
TEST_SET_SIZE = 25
RANDOM_SEED = 42

SYSTEM_PROMPT = """You are a radiologist assistant specializing in providing advice to radiology analysts. You analyze mamography images, helping provide:

          1.  Breast Imaging Reporting and Data System rating (BI-RADS). Your assessment should follow these categories:
              - BI-RADS 0 (Incomplete): Needs additional imaging evaluation.
              - BI-RADS 1 (Negative): There's nothing to comment on. The breasts are symmetric and have no masses, architectural distortion, or suspicious calcifications.
              - BI-RADS 2 (Benign): A definite benign finding. This includes things like secretory calcifications, simple cysts, fat-containing lesions, etc.
              - BI-RADS 3 (Probably Benign): A finding that has a very high probability of being benign (>98%). A short-interval follow-up is suggested.
              - BI-RADS 4 (Suspicious): A finding that has a reasonable suspicion of being malignant. This category is subdivided:
                  - BI-RADS 4a: Low suspicion for malignancy (2% to <10% likelihood).
                  - BI-RADS 4b: Moderate suspicion for malignancy (10% to <50% likelihood).
                  - BI-RADS 4c: High suspicion for malignancy (50% to <95% likelihood).
              - BI-RADS 5 (Highly Suggestive of Malignancy): A finding that is almost certainly malignant (>=95% likelihood).
              - BI-RADS 6 (Known Biopsy-Proven Malignancy): Used for findings on a mammogram that have already been shown to be cancerous by a previous biopsy.
          2. Finding Notes
              - Your notes should describe any abnormalities found in the image. Common patterns to describe are:
                  - Calcifications: Such as "microcalcifications" or "calcifications". Note if they are "benign", "clustered", or associated with "vascular calcifications".
                  - Nodules/Masses: Such as "nodule", "mass", or "fibroadenoma". Describe their location (e.g., "in the upper outer quadrant") and any associated findings (e.g., "with associated microcalcifications", "with a spiculated region").
                  - Architectural Distortion: Describe any "stromal distortion", noting its location.
                  - Asymmetric Density: Note any "asymmetric density" and its location.
              - Contextual Information: Always include relevant context like "follow-up examination", "post-surgery", "post-chemotherapy", or "previously biopsied".
              - Breast Density: Include an explicit breast density category when clear and appropriate.
              - Lesion Characteristics: Include other suspicious features whenever appropriate.
            3. Most likely diagnosis
              - Your diagnosis should be based on the findings in the image and the criteria above. Based on what you see, provide a recommendation for the doctor assessing this patient. You are essentially a second opinion radiologist, so you want to be as helpful as possible, stating what you aren't sure about and what you are sure about. You should provide only one recommendation, what evidence from the image drove you to your diagnosis, and what the most likely next step might be.
          
          Outputs should be clinically grounded and accurate. If you're not sure, state so. Otherwise, state conversationally a diagonis for the image based on the criteria above. Do not offer analysis for criteria not listed above. Offer next steps based on the BI-Rads category."""

USER_TEXT_PROMPT = "Please provide a complete radiological assessment of this mammogram. Include the BI-RADS category, finding notes, your diagnosis, and any recommended next steps."

ACR_BREAST_DENSITY = {
    "1": "ACR A (Almost entirely fatty) - The breasts are almost entirely composed of fat with less than 25% fibroglandular tissue. Mammography has high sensitivity in this density category",
    "2": "ACR B (Scattered fibroglandular densities) - There are scattered areas of fibroglandular density, comprising approximately 25-50% of the breast. Mammography generally has good sensitivity",
    "3": "ACR C (Heterogeneously dense) - The breasts are heterogeneously dense, comprising approximately 51-75% fibroglandular tissue, which may obscure small masses and reduce mammography sensitivity",
    "4": "ACR D (Extremely dense) - The breasts are extremely dense with more than 75% fibroglandular tissue, which significantly lowers the sensitivity of mammography and may obscure lesions",
}

BIRADS_DESCRIPTIONS = {
    "0": {
        "description": "Incomplete - Additional imaging evaluation is needed",
        "recommendation": "recommend additional imaging or prior studies for comparison."
    },
    "1": {
        "description": "Negative - No significant abnormalities detected",
        "recommendation": "continue routine screening mammography."
    },
    "2": {
        "description": "Benign - Definite benign findings present",
        "recommendation": "continue routine screening mammography."
    },
    "3": {
        "description": "Probably Benign - Very high probability of being benign (>98%)",
        "recommendation": "perform short-interval follow-up imaging in 6 months."
    },
    "4": {
        "description": "Suspicious - Reasonable suspicion of malignancy",
        "recommendation": "consider tissue diagnosis via biopsy."
    },
    "4a": {
        "description": "Suspicious (Low) - Low suspicion for malignancy (2% to <10% likelihood)",
        "recommendation": "consider tissue diagnosis via biopsy."
    },
    "4b": {
        "description": "Suspicious (Moderate) - Moderate suspicion for malignancy (10% to <50% likelihood)",
        "recommendation": "perform tissue diagnosis via biopsy."
    },
    "4c": {
        "description": "Suspicious (High) - High suspicion for malignancy (50% to <95% likelihood)",
        "recommendation": "strongly recommend tissue diagnosis via biopsy."
    },
    "5": {
        "description": "Highly Suggestive of Malignancy - Almost certainly malignant (>=95% likelihood)",
        "recommendation": "perform tissue diagnosis via biopsy and arrange an oncology consultation."
    },
    "6": {
        "description": "Known Biopsy-Proven Malignancy - Already confirmed as cancerous",
        "recommendation": "proceed with treatment planning and oncology care."
    },
}


def read_csv_data(csv_path):
    if not csv_path.exists():
        logging.error(f"CSV file not found at {csv_path}")
        return None

    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                rows.append(row)
    except Exception as e:
        logging.error(f"Failed to read CSV file: {e}")
        return None

    logging.info(f"Successfully read {len(rows)} rows from CSV")
    return rows


def validate_row(row):
    file_name = row.get("File Name", "").strip()
    if not file_name:
        return False

    findings = row.get("Findings Notes (English)", "").strip()
    if not findings:
        return False

    birads = row.get("Bi-Rads", "").strip()
    if not birads:
        return False

    return True


def find_matching_image(file_name_id, images_dir):
    if not file_name_id:
        return None

    file_name_id_clean = str(file_name_id).replace(".0", "").strip()
    if not file_name_id_clean:
        return None

    for image_file in images_dir.iterdir():
        if not image_file.is_file():
            continue

        if not image_file.name.lower().endswith(".jpg"):
            continue

        if image_file.name.startswith(file_name_id_clean + "_"):
            return image_file.name

    return None


def get_acr_description(acr_value):
    acr_str = str(acr_value).strip()
    
    if acr_str in ACR_BREAST_DENSITY:
        return ACR_BREAST_DENSITY[acr_str]
    
    return "ACR breast density not specified"


def get_birads_info(birads_value):
    birads_str = str(birads_value).strip()
    
    if birads_str in BIRADS_DESCRIPTIONS:
        return BIRADS_DESCRIPTIONS[birads_str]
    
    return {
        "description": "Unknown BI-RADS category",
        "recommendation": "consult with a radiologist for proper assessment."
    }


def create_assistant_response(findings, acr_value, birads_value):
    acr_description = get_acr_description(acr_value)
    birads_info = get_birads_info(birads_value)
    
    response = f"This image shows {findings}. "
    response += f"The breast density is {acr_description}. "
    response += f"Its BI-RADS rating is {birads_value}, meaning {birads_info['description']}. "
    response += f"The recommendation is to {birads_info['recommendation']}"
    
    return response


def create_json_entry(row, image_filename):
    lambda_image_path = f"{LAMBDA_IMAGE_BASE_PATH}/{image_filename}"
    
    findings = row.get("Findings Notes (English)", "").strip()
    acr = row.get("ACR", "").strip()
    birads = row.get("Bi-Rads", "").strip()
    
    assistant_text = create_assistant_response(findings, acr, birads)
    
    json_entry = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": lambda_image_path
                    },
                    {
                        "type": "text",
                        "text": USER_TEXT_PROMPT
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": assistant_text
                    }
                ]
            }
        ]
    }
    
    return json_entry


def process_rows(rows, images_dir):
    valid_entries = []
    skipped_count = 0
    
    for idx, row in enumerate(rows, start=1):
        if not validate_row(row):
            skipped_count += 1
            continue
        
        file_name_id = row.get("File Name", "").strip()
        image_filename = find_matching_image(file_name_id, images_dir)
        
        if not image_filename:
            logging.warning(
                f"Row {idx}: Could not find matching image for File Name ID: {file_name_id}"
            )
            skipped_count += 1
            continue
        
        json_entry = create_json_entry(row, image_filename)
        entry_with_metadata = {
            "json_entry": json_entry,
            "image_filename": image_filename,
            "csv_row": row
        }
        valid_entries.append(entry_with_metadata)
        
        if idx % 50 == 0:
            logging.info(f"Processed {idx} rows...")
    
    logging.info(f"Total valid entries: {len(valid_entries)}")
    logging.info(f"Total skipped rows: {skipped_count}")
    
    return valid_entries


def split_train_test(entries, test_size, seed):
    random.seed(seed)
    
    total_entries = len(entries)
    if total_entries < test_size:
        logging.warning(
            f"Dataset has only {total_entries} entries, less than requested test size {test_size}"
        )
        test_size = max(1, total_entries // 10)
    
    shuffled_entries = entries.copy()
    random.shuffle(shuffled_entries)
    
    test_set = shuffled_entries[:test_size]
    training_set = shuffled_entries[test_size:]
    
    logging.info(f"Training set size: {len(training_set)}")
    logging.info(f"Test set size: {len(test_set)}")
    
    return training_set, test_set


def write_jsonl_file(entries, output_path):
    if not entries:
        logging.warning(f"No entries to write to {output_path}")
        return False
    
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            for entry_data in entries:
                json_entry = entry_data["json_entry"]
                json_line = json.dumps(json_entry, ensure_ascii=False)
                file.write(json_line + "\n")
        
        logging.info(f"Successfully wrote {len(entries)} entries to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to write JSONL file {output_path}: {e}")
        return False


def write_test_csv(test_entries, output_path, original_csv_path):
    if not test_entries:
        logging.warning(f"No test entries to write to {output_path}")
        return False
    
    try:
        with open(original_csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
    except Exception as e:
        logging.error(f"Failed to read CSV headers: {e}")
        return False
    
    if not fieldnames:
        logging.error("No fieldnames found in original CSV")
        return False
    
    try:
        with open(output_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry_data in test_entries:
                csv_row = entry_data["csv_row"]
                writer.writerow(csv_row)
        
        logging.info(f"Successfully wrote {len(test_entries)} rows to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to write CSV file {output_path}: {e}")
        return False


def move_test_images(test_entries, images_dir, test_set_dir):
    if not test_entries:
        logging.warning("No test entries to move images for")
        return False
    
    test_images_dir = test_set_dir / "images"
    test_images_dir.mkdir(parents=True, exist_ok=True)
    
    moved_count = 0
    failed_count = 0
    
    for entry_data in test_entries:
        image_filename = entry_data["image_filename"]
        source_path = images_dir / image_filename
        dest_path = test_images_dir / image_filename
        
        if not source_path.exists():
            logging.warning(f"Source image not found: {source_path}")
            failed_count += 1
            continue
        
        try:
            shutil.move(str(source_path), str(dest_path))
            moved_count += 1
        except Exception as e:
            logging.error(f"Failed to move {image_filename}: {e}")
            failed_count += 1
    
    logging.info(f"Moved {moved_count} images to {test_images_dir}")
    if failed_count > 0:
        logging.warning(f"Failed to move {failed_count} images")
    
    return moved_count > 0


def main():
    logging.info("Starting dataset creation process...")
    
    csv_rows = read_csv_data(CSV_FILE_PATH)
    if csv_rows is None:
        logging.error("Failed to read CSV data. Exiting.")
        return
    
    valid_entries = process_rows(csv_rows, IMAGES_DIR)
    if not valid_entries:
        logging.error("No valid entries found. Exiting.")
        return
    
    training_set, test_set = split_train_test(
        valid_entries, TEST_SET_SIZE, RANDOM_SEED
    )
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_SET_DIR.mkdir(parents=True, exist_ok=True)
    
    training_success = write_jsonl_file(training_set, TRAINING_JSONL_FILE)
    test_csv_success = write_test_csv(test_set, TEST_SET_CSV_FILE, CSV_FILE_PATH)
    test_images_success = move_test_images(test_set, IMAGES_DIR, TEST_SET_DIR)
    
    if training_success and test_csv_success and test_images_success:
        logging.info("Dataset creation completed successfully!")
        logging.info(f"Training JSONL: {TRAINING_JSONL_FILE}")
        logging.info(f"Test CSV: {TEST_SET_CSV_FILE}")
        logging.info(f"Test images moved to: {TEST_SET_DIR / 'images'}")
    else:
        logging.error("Dataset creation completed with errors.")


if __name__ == "__main__":
    main()

