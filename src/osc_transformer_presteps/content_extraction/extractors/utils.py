"""Python Script for public utility functions."""

import json
from pathlib import Path


def dict_to_json(json_path: Path, dictionary: dict) -> None:
    """Convert a dictionary to JSON and write it to a file.

    Args:
    ----
        json_path (Path): The path to the JSON file to be written.
        dictionary (dict): The dictionary to be converted to JSON.

    Returns:
    -------
        None: This function does not return anything.

    Raises:
    ------
        OSError: If there is an error writing the JSON file.

    Note:
    ----
        This function uses the `json.dump()` method from the built-in `json` module to convert the dictionary to JSON
        and write it to the specified file. The function opens the file in write mode and overwrites any existing
        content.

    Example:
    -------
        json_path = Path("output.json")
        data = {"name": "John Doe", "age": 30, "city": "New York"}

        dict_to_json(json_path, data)

    """
    with open(str(json_path), "w") as f:
        json.dump(dictionary, f)
