from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()
setup(
    name="FF8GameData",
    version="1.0.0",
    author="HobbitDur",
    description="Lots of data about FF8",
    url="https://www.patreon.com/c/HobbitMods",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
    install_requires=requirements,
    project_urls={
        "Donate": "https://www.patreon.com/c/HobbitMods",
    },
)