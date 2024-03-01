from pathlib import Path
from pprint import pprint
from typing import Any, Dict, Optional, Union

from src.osc_transformer_presteps.content_extraction.extraction_factory import (
    get_extractor,
)


def extract_main(
    input_file_path: Path,
    output_file_path: Optional[Path] = None,
    settings: Optional[Dict[str, Union[str, bool]]] = None,
) -> Dict[str, Any]:
    """
    Extract information from an input file using a specified extractor and save the extraction results to a file.

    Args:
        input_file_path (Path): The path of the input file.
        output_file_path (Path): The path of the output file to save the extraction results.
        settings (Dict[str, Union[str, bool]]): A dictionary containing the settings for the extractor.
    """
    extractor = get_extractor(input_file_path.suffix, settings)
    if isinstance(output_file_path, Path):
        output_folder_path = output_file_path.parent
    else:
        output_folder_path = None

    if not extractor.check_for_skip_files(input_file_path=input_file_path, output_folder_path=output_folder_path):
        extraction_response = extractor.extract(input_file_path=input_file_path)

    if extractor.get_settings()["store_to_file"] and output_file_path is not None:
        extractor.save_extraction_to_file(output_file_path=output_file_path)

    return extraction_response.dict()


if __name__ == "__main__":
    input_folder = Path(__file__).resolve().parent / "input"
    output_folder = Path(__file__).resolve().parent / "output"

    file_name = "test.pdf"

    input_file_path_main = input_folder / file_name
    output_file_path_main = output_folder / input_file_path_main.with_suffix(".json").name
    settings_main: Optional[Dict[str, Union[str, bool]]] = {"skip_extracted_files": True, "store_to_file": True}

    print(f"Input file path is :\n {input_file_path_main}.")

    extraction_dict = extract_main(
        input_file_path=input_file_path_main, output_file_path=output_file_path_main, settings=settings_main
    )

    pprint(extraction_dict)
