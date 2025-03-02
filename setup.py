import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PromptizeThis",
    version="0.0.1",
    author="Chester Wang",
    author_email="freeaigo2012@gmail.com",
    description="Interactive GUI to generate prompts from codebase files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ChesterAiGo/PromptizeThis",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # or your chosen license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        
    ],
    entry_points={
        "console_scripts": [
            "PromptizeThis=src.cli:main",
        ],
    },
)
