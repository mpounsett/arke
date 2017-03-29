"""
Arke DNS Library

A native python library that provides an interface to the DNS protocol.
"""
from distutils.util import convert_path
from setuptools import setup, find_packages
from unittest import TestLoader


def get_test_suite():
    test_loader = TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite

main_ns = {}
ver_path = convert_path('arke/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name="arke",
    version=main_ns['__VERSION__'],
    description="Arke DNS Library",
    long_description=__doc__,
    keywords="library DNS",

    author="Matthew Pounsett",
    author_email="matt@conundrum.com",
    license="Apache Software License 2.0",

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Networking',
    ],

    test_suite='setup.get_test_suite',
    packages=find_packages(),
    install_requires=[
        'more_itertools>=2.6.0',
        'future>=0.16',
        'enum34;python_version<"3.4"',
    ],

)
