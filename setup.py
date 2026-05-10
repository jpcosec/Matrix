from setuptools import setup, find_packages

setup(
    name="matrix-engine",
    version="0.1.0",
    description="Boolean sense matrices for natural language logic",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jpcosec/Matrix",
    author="jpcosec",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=["pyyaml"],
)
