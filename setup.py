import io
import os
import re

from setuptools import setup


def get_version():
    regex = r"__version__\s=\s\'(?P<version>[\d\.]+?)\'"

    path = ('async_lru.py',)

    return re.search(regex, read(*path)).group('version')


def read(*parts):
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)

    with io.open(filename, encoding='utf-8', mode='rt') as fp:
        return fp.read()


setup(
    name='async_lru',
    version=get_version(),
    author='wikibusiness',
    author_email='osf@wikibusiness.org',
    url='https://github.com/wikibusiness/async_lru',
    description='Simple lru_cache for asyncio',
    long_description=read('README.rst'),
    extras_require={
        ':python_version=="3.3"': ['asyncio'],
    },
    py_modules=['async_lru'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords=['asyncio', 'lru', 'lru_cache'],
)
