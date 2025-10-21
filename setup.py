# setup.py
# Purpose: Setup script for the Micro-Consent Pipeline package

"""
Setup script for installing the micro_consent_pipeline package.
"""

from setuptools import setup, find_packages

setup(
    name="micro_consent_pipeline",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "spacy",
        "pydantic",
        "pytest",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A lightweight privacy consent analysis pipeline.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MitPete/Micro-Consent-Pipeline",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)