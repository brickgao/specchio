#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup
from specchio import __version__

setup(
    name="Specchio",
    version=__version__,
    url="https://github.com/brickgao/specchio",
    license="MIT",
    description="Specchio is a tool that can help you rsync your file,"
                "it use `.gitignore` in git to discern which file is ignored.",
    long_description=open("README.md").read(),
    author="Brickgao",
    author_email="brickgao@gmail.com",
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    install_requires=[
        "colorlog",
        "mock",
        "testfixtures",
        "watchdog"
    ],
    entry_points={
        "console_scripts": [
            "specchio = specchio.main:main"
        ],
    },
)
