"""
Setup configuration for py-isa-xform
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Core dependencies only (not dev dependencies)
core_requirements = [
    "jsonschema>=4.0.0",
    "pydantic>=2.0.0", 
    "click>=8.0.0",
    "rich>=13.0.0",
]

setup(
    name="py-isa-xform",
    version="1.0.0",
    description="A comprehensive ISA transformation toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Group 6 Team", 
    author_email="",
    url="https://github.com/yomnahisham/py-isa-xform",
    license="Apache-2.0",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    include_package_data=True,
    package_data={
        "isa_xform.isa_definitions": ["*.json"],
        "isa_xform": ["*.md"],
    },
    
    python_requires=">=3.8",
    install_requires=core_requirements,
    
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "parsing": [
            "pyparsing>=3.0.0",
            "lark>=1.0.0",
        ],
        "build": [
            "build>=0.10.0",
            "wheel>=0.40.0",
            "setuptools>=65.0.0",
        ],
    },
    
    entry_points={
        "console_scripts": [
            "xform=isa_xform.cli:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Assemblers",
        "Topic :: Software Development :: Compilers",
        "Topic :: System :: Hardware",
        "Topic :: Education",
    ],
    
    keywords="assembler disassembler ISA instruction-set-architecture compiler",
    
    project_urls={
        "Bug Reports": "https://github.com/yomnahisham/py-isa-xform/issues",
        "Source": "https://github.com/yomnahisham/py-isa-xform",
    },
) 