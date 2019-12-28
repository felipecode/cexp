import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
     name='cexp',
     version='0.1`',
     scripts=[],
     author="felipecode",
     author_email="felipe.alcm@gmail.com",
     description="The cexp package",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/felipecode/cexp",
     packages=setuptools.find_packages(),
     install_requires=[
        'numpy>=1.16'
     ],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )