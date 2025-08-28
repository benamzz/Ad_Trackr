"""
Setup script pour MyFlow
"""

from setuptools import setup, find_packages
import os

# Lire le README
def read_readme():
    with open("README_NEW.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Lire les requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="myflow",
    version="0.2.0",
    author="MyFlow Team",
    author_email="team@myflow.dev",
    description="Mini-librairie d'orchestration de workflows avec design patterns",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/myflow/myflow",
    packages=find_packages(include=["myflow_lib*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "pytest-mock>=3.6.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "myflow=myflow_lib.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="workflow orchestration dag airflow design-patterns",
    project_urls={
        "Bug Reports": "https://github.com/myflow/myflow/issues",
        "Source": "https://github.com/myflow/myflow",
        "Documentation": "https://myflow.readthedocs.io/",
    },
)
