import setuptools
from eunomia import __version__

with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()

setuptools.setup(
    name="eunomia",
    author="Nathan Juraj Michlo",
    author_email="NathanJMichlo@gmail.com",

    version=__version__,
    python_requires='>=3.6',
    packages=setuptools.find_packages(),

    url="https://github.com/nmichlo/eunomia",
    description="Simple configuration framework with custom backends, based on hydra config.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)