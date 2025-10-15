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

SYSTEM_PROMPT = """You are an expert radiologist assistant analyzing mammography images. Provide clear, professional assessments including findings, breast density, BI-RADS classification, and clinical recommendations."""

USER_TEXT_PROMPT = "Please provide a complete radiological assessment of this mammogram. Include the BI-RADS category, finding notes, your diagnosis, and any recommended next steps."


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


def find_matching_image(file_name_id, primary_images_dir, secondary_images_dir):
    if not file_name_id:
        return None

    file_name_id_clean = str(file_name_id).replace(".0", "").strip()
    if not file_name_id_clean:
        return None

    search_dirs = [primary_images_dir]
    if secondary_images_dir and secondary_images_dir.exists():
        search_dirs.append(secondary_images_dir)

    for images_dir in search_dirs:
        for image_file in images_dir.iterdir():
            if not image_file.is_file():
                continue

            if not image_file.name.lower().endswith(".jpg"):
                continue

            if image_file.name.startswith(file_name_id_clean + "_"):
                return image_file.name

    return None


def get_clinical_action(birads_value):
    """Returns a concise, action-oriented recommendation based on the BI-RADS value."""
    birads_str = str(birads_value).strip()
    actions = {
        "0": "Recommend additional imaging or prior studies for comparison.",
        "1": "Recommend routine screening mammography.",
        "2": "Recommend routine screening mammography.",
        "3": "Recommend 6-month follow-up imaging.",
        "4": "Recommend tissue biopsy for histological diagnosis.",
        "4a": "Consider biopsy given low suspicion findings.",
        "4b": "Biopsy indicated for moderate suspicion lesion.",
        "4c": "Strongly recommend biopsy given high suspicion.",
        "5": "Biopsy required; arrange oncology consultation.",
        "6": "Proceed with treatment planning and oncology care.",
    }
    return actions.get(birads_str, "Recommend radiologist review.")


def create_assistant_response(findings, acr_value, birads_value):
    clinical_action = get_clinical_action(birads_value)

    responses = [
        f"Assessment: {findings}. Breast density is ACR {acr_value}. This is classified as BI-RADS {birads_value}. {clinical_action}",
        f"The mammogram shows {findings}, with ACR {acr_value} density. I would classify this as BI-RADS {birads_value}. {clinical_action}",
        f"My assessment reveals {findings}. The breast composition is ACR {acr_value}. This warrants a BI-RADS {birads_value} classification. {clinical_action}",
        f"Findings include {findings}. Breast density is ACR {acr_value}. Based on these findings, I recommend BI-RADS {birads_value}. {clinical_action}",
    ]
    
    return random.choice(responses)


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


def process_rows(rows, images_dir, test_images_dir):
    valid_entries = []
    skipped_count = 0
    
    for idx, row in enumerate(rows, start=1):
        if not validate_row(row):
            skipped_count += 1
            continue
        
        file_name_id = row.get("File Name", "").strip()
        image_filename = find_matching_image(file_name_id, images_dir, test_images_dir)
        
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


def split_train_test(entries, test_set_dir, fallback_test_size, seed):
    test_images_dir = test_set_dir / "images"
    existing_test_filenames = set()

    if test_images_dir.exists():
        existing_test_filenames = {f.name for f in test_images_dir.iterdir() if f.is_file()}

    if existing_test_filenames:
        logging.info(f"Found {len(existing_test_filenames)} existing images in {test_images_dir}. Using them for the test set.")
        test_set = []
        training_set = []
        
        for entry in entries:
            if entry["image_filename"] in existing_test_filenames:
                test_set.append(entry)
            else:
                training_set.append(entry)

        found_test_filenames = {entry['image_filename'] for entry in test_set}
        missing_from_csv = existing_test_filenames - found_test_filenames
        if missing_from_csv:
            logging.warning(f"The following images from the test set directory were not found in the CSV and will be ignored: {', '.join(missing_from_csv)}")
    else:
        logging.info("No existing test set images found. Performing random split.")
        random.seed(seed)
        
        total_entries = len(entries)
        if total_entries < fallback_test_size:
            logging.warning(
                f"Dataset has only {total_entries} entries, less than requested test size {fallback_test_size}"
            )
            fallback_test_size = max(1, total_entries // 10)
        
        shuffled_entries = entries.copy()
        random.shuffle(shuffled_entries)
        
        test_set = shuffled_entries[:fallback_test_size]
        training_set = shuffled_entries[fallback_test_size:]

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
    already_present_count = 0
    
    for entry_data in test_entries:
        image_filename = entry_data["image_filename"]
        source_path = images_dir / image_filename
        dest_path = test_images_dir / image_filename
        
        if dest_path.exists():
            already_present_count += 1
            continue
            
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
    
    logging.info(f"Moved {moved_count} new images to {test_images_dir}")
    if already_present_count > 0:
        logging.info(f"{already_present_count} images were already in the test set directory.")
    if failed_count > 0:
        logging.warning(f"Failed to move {failed_count} images")
    
    return moved_count > 0 or already_present_count > 0


def main():
    logging.info("Starting dataset creation process...")
    
    csv_rows = read_csv_data(CSV_FILE_PATH)
    if csv_rows is None:
        logging.error("Failed to read CSV data. Exiting.")
        return
    
    test_images_dir = TEST_SET_DIR / "images"
    valid_entries = process_rows(csv_rows, IMAGES_DIR, test_images_dir)
    if not valid_entries:
        logging.error("No valid entries found. Exiting.")
        return
    
    training_set, test_set = split_train_test(
        valid_entries, TEST_SET_DIR, TEST_SET_SIZE, RANDOM_SEED
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

