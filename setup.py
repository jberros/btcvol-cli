"""
btcvol-cli - Command-line tool for submitting models to BTC DVOL competitions
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="btcvol-cli",
    version="1.1.0",
    author="Jeremy Berros",
    author_email="jberrospellenc@gmail.com",
    description="CLI tool for submitting Bitcoin volatility prediction models to CrunchDAO competitions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jberros/btcvol-cli",
    py_modules=["btcvol_submit"],
    install_requires=[
        "pyyaml>=6.0",
    ],
    extras_require={
        "notebook": ["crunch-convert>=0.1.0"],
    },
    entry_points={
        "console_scripts": [
            "btcvol-submit=btcvol_submit:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    keywords="bitcoin volatility prediction competition cli crunchdao",
    project_urls={
        "Bug Reports": "https://github.com/jberros/btcvol-cli/issues",
        "Source": "https://github.com/jberros/btcvol-cli",
        "Package": "https://pypi.org/project/btcvol/",
        "Competition": "https://www.crunchdao.com/",
    },
)
