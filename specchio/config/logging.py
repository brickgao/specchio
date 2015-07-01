#!/usr/bin/env python
# -*- coding: utf-8 -*-


LOGGING_CONFIG = {
    "version": 1,
    "loggers": {
        "specchio": {
            "level": "DEBUG",
            "handlers": ["specchio"],
            "qualname": "specchio"
        }
    },
    "handlers": {
        "specchio": {
            "class": "logging.StreamHandler",
            "formatter": "specchio",
            "stream": "ext://sys.stdout"
        }},
    "formatters": {
        "specchio": {
            "format": "%(log_color)s[%(levelname)s]%(reset)s"
                      " %(asctime)s %(name)s  %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "()": "colorlog.ColoredFormatter",
        }
    }
}
