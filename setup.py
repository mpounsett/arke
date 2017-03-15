"""
Arke DNS Library

A native python library that provides an interface to the DNS protocol.
"""
from distutils.util import convert_path
from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup, find_packages

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
    license="NONE",

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

    packages=find_packages(),
    install_requires=[
        str(x.req) for x in parse_requirements('requirements.txt',
                                               session=PipSession())
    ],

)
