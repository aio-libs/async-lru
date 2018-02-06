import io
import os
import re
import sys

from setuptools import setup

needs_pytest = 'pytest' in set(sys.argv)


def get_version():
    regex = r"__version__\s=\s\'(?P<version>[\d\.ab]+?)\'"

    path = ('async_lru.py',)

    return re.search(regex, read(*path)).group('version')


def read(*parts):
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)

    with io.open(filename, encoding='utf-8', mode='rt') as fp:
        return fp.read()


setup(
    name='async_lru',
    version=get_version(),
    author='Victor Kovtun',
    author_email='hellysmile@gmail.com',
    url='https://github.com/wikibusiness/async_lru',
    description='Simple lru_cache for asyncio',
    long_description=read('README.rst'),
    extras_require={
        ':python_version=="3.3"': ['asyncio'],
    },
    setup_requires=['pytest-runner'] if needs_pytest else [],
    tests_require=['pytest', 'pytest-asyncio', 'pytest-cov'],
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
