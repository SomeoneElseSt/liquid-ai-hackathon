"""
Copies subdirs containing at least one .dicom file into a new directory with the suffix _processed. 

"""

import argparse
import shutil
from pathlib import Path

# The project's 'src' directory, which is the parent of the 'scripts' directory.
# This makes the default path work regardless of where the script is run from.
SRC_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = SRC_ROOT / "data/physionet.org/files/vindr-mammo/1.0.0/images"
PROCESSED_SUFFIX = "_processed"

def get_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Process a directory to filter subdirectories containing DICOM files."
    )
    parser.add_argument(
        "--source_dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help=f"The source directory to process. Defaults to {DEFAULT_SOURCE_DIR}",
    )
    return parser.parse_args()

def has_dicom_files(directory: Path):
    """Checks if a directory contains any .dicom files."""
    if not directory.is_dir():
        return False
    for _ in directory.glob("*.dicom"):
        # Found at least one .dicom file, no need to check further
        return True

    return False

def create_destination_directory(source_dir: Path):
    """Creates the destination directory, handling existing directories interactively."""
    destination_dir_name = source_dir.name + PROCESSED_SUFFIX
    destination_dir = source_dir.with_name(destination_dir_name)

    while destination_dir.exists():
        print(f"Destination directory {destination_dir} already exists.")
        choice = input(
            "Would you like to (r)eplace it, choose a (n)ew name, or (a)bort? "
        ).lower()

        if choice in ('r', 'replace'):
            print("Replacing existing directory.")
            shutil.rmtree(destination_dir)
            break
        elif choice in ('n', 'new'):
            new_name = input("Enter the new directory name: ")
            if not new_name:
                print("Name cannot be empty.")
                continue
            destination_dir = source_dir.with_name(new_name)
        elif choice in ('a', 'abort'):
            print("Operation aborted by user.")
            return None
        else:
            print("Invalid choice. Please enter 'r', 'n', or 'a'.")

    destination_dir.mkdir(parents=True)
    print(f"Using destination directory: {destination_dir}")
    return destination_dir


def process_subdirectories(source_dir: Path, destination_dir: Path):
    """
    Copies subdirectories containing .dicom files from source to destination.
    """
    print(f"Processing subdirectories in {source_dir}...")
    copied_count = 0
    for item in source_dir.iterdir():
        if not item.is_dir():
            continue

        if not has_dicom_files(item):
            print(f"  - Skipping {item.name}: No .dicom files found.")
            continue
        destination_path = destination_dir / item.name
        try:
            shutil.copytree(item, destination_path)
            print(f"  + Copied {item.name} to {destination_dir.name}")
            copied_count += 1
        except (shutil.Error, OSError) as e:
            print(f"  ! Error copying {item.name}: {e}")
    print(f"\nProcessing complete. Copied {copied_count} subdirectories.")

def main():
    """Main function to run the script."""
    args = get_arguments()
    source_dir = args.source_dir

    if not source_dir.is_dir():
        print(f"Error: Source directory not found at {source_dir}")
        return

    destination_dir = create_destination_directory(source_dir)
    if not destination_dir:
        return

    process_subdirectories(source_dir, destination_dir)

if __name__ == "__main__":
    main()
