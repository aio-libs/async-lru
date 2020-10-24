import io
import os
import re

from setuptools import setup


def get_version():
    regex = r"__version__\s=\s\"(?P<version>[\d\.ab]+?)\""

    path = ("async_lru.py",)

    return re.search(regex, read(*path)).group("version")


def read(*parts):
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)

    with io.open(filename, encoding="utf-8", mode="rt") as fp:
        return fp.read()


setup(
    name="async-lru",
    version=get_version(),
    author="Victor Kovtun",
    author_email="hellysmile@gmail.com",
    url="https://github.com/aio-libs/async_lru",
    description="Simple lru_cache for asyncio",
    long_description=read("README.rst"),
    py_modules=["async_lru"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords=["asyncio", "lru", "lru_cache"],
)
