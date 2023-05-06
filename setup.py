commit 83da9758e8de1a11e8a6e7a631a86b3be7115acd
Author: sriramreddyM <srirammandhati@gmail.com>
Date:   Mon Jan 16 10:41:24 2023 +0700

    --

diff --git a/setup.py b/setup.py
deleted file mode 100644
index 82d1ba6..0000000
--- a/setup.py
+++ /dev/null
@@ -1,31 +0,0 @@
-import setuptools
-
-with open("README.md", "r") as fh:
-    long_description = fh.read()
-
-# packages=setuptools.find_packages(),
-
-
-setuptools.setup(
-    name="plitter",
-    version="0.1.0",
-    author="GIC@AIT",
-    author_email="sriram@ait.ac.th",
-    description="plastic litter detection tool",
-    long_description=long_description,
-    long_description_content_type="text/markdown",
-    url="https://github.com/gicait/pLitter",
-    packages=["plitter"],
-    install_requires=[
-        "opencv-python",
-        'pandas',
-        "exif",
-        "gpxpy",
-        'torch',
-    ],
-    classifiers=[
-        "Programming Language :: Python :: 3",
-        "License :: ",
-        "Operating System :: Linux",
-    ],
-)
\ No newline at end of file
