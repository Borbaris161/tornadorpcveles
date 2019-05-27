# -*- coding: utf-8

import os
import setuptools

long_description = "Placeholder in case of missing README.md."

if os.path.exists("README.md"):
    with open("README.md") as readme_fp:
        long_description = readme_fp.read()

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

