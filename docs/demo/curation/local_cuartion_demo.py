"""Python Script for locally running curation for testing."""
from pathlib import Path

from pydantic import BaseModel, FilePath, ValidationError

from src.osc_transformer_presteps.dataset_creation_curation.curator import Curator


class AnnotationData(BaseModel):
    """Pydantic model for annotation data."""

    annotation_folder: FilePath
    extract_json: FilePath
    kpi_mapping_path: FilePath


if __name__ == "__main__":
    # Define input and output folders
    input_folder = Path(__file__).resolve().parent / "input"
    output_folder = Path(__file__).resolve().parent / "output"
    json_folder = Path(__file__).resolve().parent.parent / "extraction"

    # Define file paths
    annotation_folder = input_folder / "test_annotations.xlsx"
    extract_json_path = json_folder / "output" / "Test.json"
    kpi_mapping_path = input_folder / "kpi_mapping.csv"
    output_file_path_main = output_folder / extract_json_path.with_suffix(".csv").name

    # Create AnnotationData instance
    annotation_data = AnnotationData(
        annotation_folder=annotation_folder,
        extract_json=extract_json_path,
        kpi_mapping_path=kpi_mapping_path,
        output_path=output_file_path_main,
    )

    try:
        # Validate AnnotationData instance
        annotation_data = AnnotationData(**annotation_data.dict())
    except ValidationError as e:
        print(f"Validation error: {e}")
    else:
        # Create Curator instance
        curator = Curator(
            annotation_folder=annotation_data.annotation_folder,
            extract_json=annotation_data.extract_json,
            kpi_mapping_path=annotation_data.kpi_mapping_path,
            create_neg_samples=True,
            neg_pos_ratio=1
        ).create_curator_df()

        curator.to_csv(output_file_path_main, index=False)
