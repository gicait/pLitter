import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pLitterStreet",
    version="0.0.1",
    author="GIC@AIT",
    author_email="sriram@ait.ac.th",
    description="A tool identify and map the plastic litter in the streets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gicait/pLitter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)