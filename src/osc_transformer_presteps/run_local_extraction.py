import json
import logging
from pathlib import Path

# External modules
import typer

# Internal modules
from osc_transformer_presteps.api.api import run_api
from osc_transformer_presteps.content_extraction.extraction_factory import get_extractor
from osc_transformer_presteps.settings import (
    ExtractionServerSettings,
    ExtractionSettings,
    LogType,
)

_logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)


def _specify_root_logger(log_level: LogType):
    """
    Configures the root logger with a specific formatting and log level.

    This function sets up the root logger, which is the top-level logger in the logging hierarchy, with a specific
    configuration. It creates a StreamHandler that logs messages to stdout, sets the log level to DEBUG for all
    messages, and applies a specific formatter to format the log messages.

    Args:
        log_level (str): The log_level to use for the logging.

    Usage:
    Call this function at the beginning of your code to configure the root logger
    with the desired formatting and log level.
    """
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logging.root.handlers = [handler]
    logging.root.setLevel(log_level)


@app.command()
def run_local_server(
    port: int = typer.Option(
        8000,
        "--port",
        show_default=True,
        help="The port which will be use as the default.",
    ),
    host: str = typer.Option(
        "localhost",
        "--host",
        show_default=True,
        help="The host name which will be use as the default.",
    ),
    log_level: str = typer.Option(
        "info",
        "--log_level",
        show_default=True,
        help="The log level to be used, see the different log levels from the logging package documentation."
        " Examples are info, debug and warning.",
    ),
) -> None:
    """This subcommand will start a local server."""
    settings = ExtractionServerSettings(log_level=log_level, port=port, host=host)
    _specify_root_logger(settings.log_level)
    run_api(host, port)


@app.command()
def run_local_extraction(
    file_name: str = typer.Argument(
        help="This is the name of the file you want to extract" " data from. This should be in the current folder.",
    ),
    skip_extracted_files: bool = typer.Option(
        False,
        "--skip_extracted_files",
        show_default=True,
        help="Declares if you want to skip files which have already been extracted in the past.",
    ),
    store_to_file: bool = typer.Option(
        True,
        "--store_to_file",
        show_default=True,
        help="Boolean to declare if you want to have the output as a file or not. Note that the output will"
        " be stored next to your input file with the name <input_file_name>_output.json.",
    ),
) -> None:
    """This command will start the extraction of text to json on your local machine. Check help for details."""
    cwd = Path.cwd()
    file_path_temp = cwd / file_name
    extraction_settings = ExtractionSettings(store_to_file=store_to_file, skip_extracted_files=skip_extracted_files)
    extractor = get_extractor(file_path_temp.suffix, extraction_settings.model_dump())
    extraction_response = extractor.extract(input_file_path=file_path_temp)
    output_file_name = file_name + "_output.json"
    output_file_path = cwd / output_file_name
    with open(str(output_file_path), "w") as file:
        json.dump(extraction_response.dictionary, file, indent=4)


if __name__ == "__main__":
    app()
