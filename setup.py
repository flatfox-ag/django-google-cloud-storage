"""
Setup script for django-google-cloud-storage
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-google-cloud-storage',
    version='0.0.1',
    description='A django storage backend for google cloud storage',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/flatfox-ag/django-google-cloud-storage',

    # Author details
    author='Bernhard Maeder',
    author_email='bernhard.maeder@flatfox.ch',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='google cloud storage django backend',
    packages=find_packages(),
    install_requires=[
        "google-api-python-client>=1.5.0",
        "google-cloud-storage>=0.22.0",
    ],
)
