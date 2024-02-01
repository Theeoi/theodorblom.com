#!/usr/bin/env python
import logging
from pathlib import Path

from app import create_app


def configure_logging():
    logs_dir = Path(__file__).parent.parent / "logs"

    if not logs_dir.exists():
        logs_dir.mkdir(parents=True)

    logging.basicConfig(
        level=logging.DEBUG,
        filename=f"{logs_dir.absolute()}/default.log",
        format="%(asctime)s %(message)s",
    )


configure_logging()

application = create_app()
