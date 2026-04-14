"""Logging setup for Trialix."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(output_dir, debug=False):
    """
    Configure logging to both console (stdout) and log file.

    Creates OUTPUT_DIR/logs/ directory with timestamped log files.

    Parameters
    ----------
    output_dir : str or Path
        Output directory where logs/ will be created.
    debug : bool
        If True, set console log level to DEBUG. Otherwise INFO.

    Returns
    -------
    logger : logging.Logger
        Configured logger instance.
    """
    log_dir = Path(output_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"trialix_{timestamp}.log"

    log_level = logging.DEBUG if debug else logging.INFO

    # Root trialix logger
    logger = logging.getLogger("trialix")
    logger.setLevel(logging.DEBUG)
    # Clear any existing handlers (avoid duplicates on re-init)
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # File handler (always DEBUG level for full trace)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    logger.info(f"Trialix log file: {log_file}")
    return logger
