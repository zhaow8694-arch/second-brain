from setuptools import setup, find_packages

setup(
    name="trading_system",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "pytest>=6.0",
        "pytest-asyncio>=0.15.0",
        "pytest-cov>=2.12.0",
    ],
    python_requires=">=3.8",
) 