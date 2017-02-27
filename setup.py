import io
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


# if sys.version_info < (3, 3):
#     raise RuntimeError('async_lru doesn\'t suppport Python earllier than 3.3')


def get_version():
    regex = r"""__version__\s+=\s+(?P<quote>['"])(?P<version>.+?)(?P=quote)"""
    fp = io.open('async_lru.py', mode='rt', encoding='utf-8')
    try:
        return re.search(regex, fp.read()).group('version')
    finally:
        fp.close()


def get_long_description():
    fp = io.open('README.rst', mode='rt', encoding='utf-8')
    try:
        return fp.read()
    finally:
        fp.close()


setup(
    name='async_lru',
    version=get_version(),
    author='wikibusiness',
    author_email='osf@wikibusiness.org',
    url='https://github.com/wikibusiness/async_lru',
    description='Simple lru_cache for asyncio',
    long_description=get_long_description(),
    extras_require={
        ':python_version=="3.3"': ['asyncio'],
    },
    py_modules=['async_lru'],
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
