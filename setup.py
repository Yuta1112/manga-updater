from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="manga-updater",
    version="1.0.0",
    author="Yuta1112",
    author_email="",
    description="A manga update monitoring system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Yuta1112/manga-updater",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "requests>=2.25.1",
        "beautifulsoup4>=4.9.3",
        "lxml>=4.6.3",
    ],
    entry_points={
        'console_scripts': [
            'manga-updater=src.main:main',
        ],
    },
)