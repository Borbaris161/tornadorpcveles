#!/usr/bin/env/python

import setuptools

with open("README.md") as readme:
    long_description = readme.read()
    with open("README", "w") as pypi_readme:
        pypi_readme.write(long_description)

setuptools.setup(
    name="tornadorpcveles",
    version="0.0.1",
    packages=setuptools.find_packages(),
    author="Krutsevich Artem",
    install_requires=["jsonrpclibveles"],
    author_email="borbaris161@gmail.com",
    description="TornadoRPC-Server is a an implementation of both JSON-RPCLIB VelesPy"
        "handler for the Tornado framework.",
    long_description=long_description,
)

