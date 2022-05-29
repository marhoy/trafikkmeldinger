from __future__ import annotations

import logging
import sys
import types
from typing import Union

import loguru
from loguru import logger

# Configure package-wide Loguru logging. You can specify different levels for each
# package.
log_filter: loguru.FilterDict = {
    "": "WARNING",
    # "requests": "DEBUG",
    "trafikkmeldinger": "DEBUG",
}
logger.remove()
logger.add(sys.stderr, filter=log_filter)
logger.add(
    "logs/trafikkmeldinger.log", filter=log_filter, rotation="1 day", retention="1 week"
)


##
#  Logging from other packages that uses standard builting logging.
##


class InterceptHandler(logging.Handler):
    """Intercept standard logging and send to loguru.

    If other packages (e.g. luigi) uses standard logging, we want to intercept that and
    log it via loguru instead. This code is copied from logurus README:
    https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level: Union[str, int] = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame: Union[None, types.FrameType] = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Intercept logging from standard library and log via loguru instead
logging.basicConfig(handlers=[InterceptHandler()], level=0)
