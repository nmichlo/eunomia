import setuptools


with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()

with open('requirements.txt', 'r') as f:
    install_requires = (req[0] for req in map(lambda x: x.split('#'), f.readlines()))
    install_requires = [req for req in map(str.strip, install_requires) if req]


setuptools.setup(
    name="eunomia",
    author="Nathan Juraj Michlo",
    author_email="NathanJMichlo@gmail.com",

    version="0.0.1.dev8",
    python_requires=">=3.6",
    packages=setuptools.find_packages(),

    install_requires=install_requires,

    url="https://github.com/nmichlo/eunomia",
    description="Simple configuration framework with custom backends, based on hydra config.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Science/Research",
    ],
)
