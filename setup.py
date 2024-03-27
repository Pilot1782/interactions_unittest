from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read().splitlines()

setup(
    name="interactions_unittest",
    version="1.0",
    description="Unofficial unittest extension for discord-py-interactions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pilot1782/interactions_unittest",
    author="Pilot1782",
    author_email="",
    license="GNU",
    packages=["interactions_unittest"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=install_requires,
)
