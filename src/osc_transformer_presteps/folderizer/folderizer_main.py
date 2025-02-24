"""Folderizer-MAIN file."""

import os


def create_osc_folder_structure(base_path: str):
    """Create a predefined folder structure inside an 'OSC' directory at the given base path.

    Args:
    base_path (str): The base directory where the 'OSC' folder will be created.

    The function creates the following subdirectories inside 'OSC':
    - inputs/pdfs_training
    - inputs/pdfs_inference
    - logs
    - outputs/jsons_training
    - outputs/jsons_inference
    - outputs/curated_data_rel
    - outputs/curated_data_kpi
    - model
    - outputs/inference_rel

    """
    osc_path = os.path.join(base_path, "OSC")
    folders = [
        "inputs/pdfs_training",
        "inputs/pdfs_inference",
        "inputs/kpi_mapping",
        "inputs/annotation_files",
        "logs",
        "outputs/jsons_training",
        "outputs/jsons_inference",
        "outputs/curated_data_rel",
        "outputs/curated_data_kpi",
        "outputs/inference_rel",
        "outputs/inference_kpi",
        "models/relevance",
        "models/kpi_detection",
    ]

    for folder in folders:
        os.makedirs(os.path.join(osc_path, folder), exist_ok=True)

    print(f"Folder structure created successfully under: {osc_path}")


create_osc_folder_structure(
    r"C:\Users\Tanishq\Desktop\IDS_WORK\presteps\osc-transformer-presteps"
)
