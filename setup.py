import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


version = '0.1'

setup(
    name='insta_browser',
    packages=['insta_browser'],
    version=version,
    description='easy parsing/automation instagram.com',
    long_description=read('README.md'),
    author='Aleksej Krichevsky',
    author_email='krich.al.vl@gmail.com',
    url='https://github.com/aLkRicha/insta_browser',
    download_url='https://github.com/aLkRicha/insta_browser/archive{}.tar.gz'.format(version),
    keywords=['parsing', 'bot', 'instabot', 'automation', 'likes'],
    license='MIT',
    classifiers=[ # look here https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Browsers',
    ],
    install_requires=[
        'selenium'
    ],
)