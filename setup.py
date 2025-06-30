#!/usr/bin/env python3
"""Setup script for the JSP CLI tool."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="jsp",
    version="1.0.0",
    author="Jared Rummler",
    author_email="jared@jaredrummler.com",
    description="CLI tool for downloading and scraping content from Joseph Smith Papers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaredrummler/jsp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Religion",
        "Topic :: Religion",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "Pillow>=9.0.0",
        "lxml>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "jsp=src.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
