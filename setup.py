"""
Setup script for SciPlotGUI.

For development install:
    pip install -e .

For building distribution:
    python -m build
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="sciplotgui",
    version="1.0.0",
    author="SciPlotGUI Contributors",
    author_email="",
    description="A GUI application for creating publication-ready scientific figures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pzm539874931/sciplotting",
    project_urls={
        "Bug Tracker": "https://github.com/pzm539874931/sciplotting/issues",
        "Documentation": "https://github.com/pzm539874931/sciplotting#readme",
        "Source Code": "https://github.com/pzm539874931/sciplotting",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.9",
    install_requires=[
        "PyQt6>=6.4.0",
        "matplotlib>=3.6.0",
        "numpy>=1.21.0",
        "scipy>=1.9.0",
        "pandas>=1.5.0",
        "openpyxl>=3.0.0",
        "lmfit>=1.1.0",
    ],
    extras_require={
        "full": [
            "SciencePlots>=2.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.0.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sciplotgui=main:main",
        ],
        "gui_scripts": [
            "sciplotgui-gui=main:main",
        ],
    },
    include_package_data=True,
    keywords=[
        "scientific",
        "plotting",
        "visualization",
        "graphpad",
        "prism",
        "matplotlib",
        "statistics",
        "curve-fitting",
    ],
)
