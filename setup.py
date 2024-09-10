from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="py835",  # Your package name
    version="0.1.1",  # Version of the package
    packages=find_packages(),  # Automatically find and include your packages
    install_requires=requirements, # Install dependencies from requirements.txt
    author="DHR Health - Data Team",
    author_email="samuel.cavazos@dhr-rgv.com",
    description="py835 is a wrapper for pyx12 used by DHR Health for parsing .835 files.",
    url="https://github.com/DHR-Health/py835",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',  # Specify Python versions
)
