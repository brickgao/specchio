#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time

from watchdog.observers import Observer

from specchio.handlers import SpecchioEventHandler
from specchio.utils import logger


def main():
    """Main function for specchio

    Example: specchio test/ user@host:test/

    :return: None
    """
    if len(sys.argv) == 2:
        src_path = sys.argv[0].strip()
        dst_ssh, dst_path = sys.argv[1].strip().split(":")
        event_handler = SpecchioEventHandler(
            src_path=src_path, dst_ssh=dst_path, dst_path=dst_path
        )
        logger.info("Initialize Specchio")
        observer = Observer()
        observer.schedule(event_handler, src_path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        print """Specchio is a tool that can help you rsync your file
it use `.gitignore` in git to mark which file is ignored.

Usage: specchio src/ user@host:dst"""
