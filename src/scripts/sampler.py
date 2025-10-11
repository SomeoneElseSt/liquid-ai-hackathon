"""
This script samples 1000 random entries from the breast-level_annotations.csv
and creates a file `image_list.txt` containing the paths to the corresponding DICOM images.
"""
from pathlib import Path
import pandas as pd

# --- Constants ---
# Use Path(__file__) to make paths relative to the script's location
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
CSV_PATH = SRC_DIR / "data/physionet.org/files/vindr-mammo/1.0.0/breast-level_annotations.csv"
OUTPUT_FILE_PATH = SCRIPT_DIR / "image_list.txt"
SAMPLE_SIZE = 1000
RANDOM_STATE = 42

def create_image_list_from_csv(csv_path, output_path, sample_size, random_state):
    """
    Reads a CSV, samples it, and writes image paths to a text file.
    """
    if not csv_path.is_file():
        print(f"Error: Annotation file not found at {csv_path}")
        return

    print(f"Reading annotations from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except (OSError, ValueError) as e:
        print(f"An error occurred while reading the CSV: {e}")
        return

    print(f"Sampling {sample_size} entries...")
    sample_df = df.sample(n=sample_size, random_state=random_state)

    print(f"Writing image list to {output_path}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in sample_df.iterrows():
                path = f"images/{row['study_id']}/{row['image_id']}.dicom"
                f.write(f"{path}\n")
    except IOError as e:
        print(f"Error writing to output file {output_path}: {e}")
        return

    print(f"Successfully wrote {sample_size} image paths to {output_path}")

def main():
    """Main function to run the script."""
    create_image_list_from_csv(CSV_PATH, OUTPUT_FILE_PATH, SAMPLE_SIZE, RANDOM_STATE)

if __name__ == "__main__":
    main()
