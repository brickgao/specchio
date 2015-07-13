#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup
from specchio import __version__

tests_requirements = [
    "mock >= 1.0.1, < 2.0.0",
    "testfixtures >= 4.1.2, < 5.0.0"
]

setup(
    name="Specchio",
    version=__version__,
    url="https://github.com/brickgao/specchio",
    license="MIT",
    description="Specchio is a tool that can help you to rsync your file "
                "automatically, it uses `.gitignore` in git to discern which"
                " file is ignored.",
    long_description=open("README.md").read(),
    author="Xiongzhi Gao",
    author_email="brickgao@gmail.com",
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    install_requires=[
        "colorlog >= 2.6.0, < 3.0.0",
        "watchdog >= 0.8.3, < 1.0.0"
    ] + tests_requirements,
    tests_require=tests_requirements,
    test_suite="nose.collector",
    entry_points={
        "console_scripts": [
            "specchio = specchio.main:main"
        ],
    },
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
