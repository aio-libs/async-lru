from setuptools import setup
from mypyc.build import mypycify


setup(ext_modules=mypycify(["async_lru/__init__.py", "--strict", "--pretty", "--disable-error-code=unused-ignore"]))
