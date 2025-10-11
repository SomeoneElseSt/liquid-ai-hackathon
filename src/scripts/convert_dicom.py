import os
import pydicom
import numpy as np
from PIL import Image
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

WORKSPACE_ROOT = (
    "/Users/steve/Documents/Files/Minerva/Internships & Hackathons/Hackathons/liquid-ai-hackathon"
)
INPUT_DIR = os.path.join(WORKSPACE_ROOT, "src/data/images")
OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, "src/data/images_jpg")
VALID_EXTENSIONS = (".dcm", ".dcim")


def apply_windowing(image, center, width):
    image_min = center - width // 2
    image_max = center + width // 2
    windowed_image = np.clip(image, image_min, image_max)
    
    if width == 0:
        return np.zeros_like(windowed_image, dtype=np.uint8)

    windowed_image = ((windowed_image - image_min) / width) * 255.0
    return windowed_image.astype(np.uint8)


def convert_dicom_to_jpg(dicom_path, jpg_path):
    try:
        ds = pydicom.dcmread(dicom_path)
    except Exception as e:
        logging.error(f"Could not read DICOM file {dicom_path}: {e}")
        return False

    try:
        pixel_array = ds.pixel_array.astype(float)
    except Exception as e:
        logging.error(f"Could not get pixel array from {dicom_path}: {e}")
        return False

    if "WindowCenter" in ds and "WindowWidth" in ds:
        center = ds.WindowCenter
        width = ds.WindowWidth

        if isinstance(center, pydicom.multival.MultiValue):
            center = center[0]
        if isinstance(width, pydicom.multival.MultiValue):
            width = width[0]

        pixel_array = apply_windowing(pixel_array, center, width)
    else:
        if pixel_array.max() > 0:
            pixel_array = (pixel_array / pixel_array.max()) * 255.0
        pixel_array = pixel_array.astype(np.uint8)

    if "PhotometricInterpretation" in ds and ds.PhotometricInterpretation == "MONOCHROME1":
        pixel_array = np.invert(pixel_array)

    try:
        img = Image.fromarray(pixel_array)
        img.save(jpg_path)
        logging.info(f"Successfully converted {os.path.basename(dicom_path)} to JPG.")
        return True
    except Exception as e:
        logging.error(f"Could not convert or save image for {dicom_path}: {e}")
        return False


def main():
    logging.info("Starting DICOM to JPG conversion.")
    logging.info(f"Input directory: {INPUT_DIR}")
    logging.info(f"Output directory: {OUTPUT_DIR}")

    if not os.path.exists(INPUT_DIR):
        logging.error(f"Input directory not found: {INPUT_DIR}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.info(f"Ensured output directory exists: {OUTPUT_DIR}")

    converted_count = 0
    failed_count = 0

    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            if not file.lower().endswith(VALID_EXTENSIONS):
                continue

            dicom_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, INPUT_DIR)
            output_subdir = os.path.join(OUTPUT_DIR, relative_path)
            os.makedirs(output_subdir, exist_ok=True)

            file_name_without_ext = os.path.splitext(file)[0]
            jpg_path = os.path.join(output_subdir, f"{file_name_without_ext}.jpg")

            if convert_dicom_to_jpg(dicom_path, jpg_path):
                converted_count += 1
            else:
                failed_count += 1

    logging.info("Conversion process finished.")
    logging.info(f"Total files converted: {converted_count}")
    logging.info(f"Total files failed: {failed_count}")


if __name__ == "__main__":
    main()
