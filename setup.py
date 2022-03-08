import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# packages=setuptools.find_packages(),


setuptools.setup(
    name="plitterstreet",
    version="1.0",
    author="GIC@AIT",
    author_email="sriram@ait.ac.th",
    description="A tool identify and map the plastic litter in the streets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gicait/pLitter",
    packages=["plitterstreet"],
    install_requires=[
        "opencv-python",
        "exif",
        "piexif",
        "folium==0.8.2",
        "tensorflow",
        "tqdm",
        "Pillow",
        "geopy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: ",
        "Operating System :: Linux",
    ],
)
