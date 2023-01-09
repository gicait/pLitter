import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# packages=setuptools.find_packages(),


setuptools.setup(
    name="plitter",
    version="0.1.0",
    author="GIC@AIT",
    author_email="sriram@ait.ac.th",
    description="plastic litter detection tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gicait/pLitter",
    packages=["plitter"],
    install_requires=[
        "opencv-python",
        'pandas',
        "exif",
        "gpxpy",
        'torch',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: ",
        "Operating System :: Linux",
    ],
)