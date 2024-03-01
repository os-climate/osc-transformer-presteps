import logging

from osc_transformer_presteps.api.api import run_api
from osc_transformer_presteps.settings import get_settings

_logger = logging.getLogger(__name__)

log_levels = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _specify_root_logger(log_level: str):
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

    log_level_value = log_levels[log_level.upper()]

    handler = logging.StreamHandler()
    handler.setLevel(log_level_value)
    handler.setFormatter(formatter)

    logging.root.handlers = [handler]
    logging.root.setLevel(log_level_value)


def main() -> None:
    settings = get_settings()
    _specify_root_logger(settings.log_level)
    run_api(settings.host, settings.port)


if __name__ == "__main__":
    main()
