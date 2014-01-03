"""Setup script for the Caliendo Facade"""

__author__ = "andrew.kelleher@buzzfeed.com (Andrew Kelleher)"

try:
  from setuptools import setup, find_packages
except ImportError:
  import distribute_setup
  distribute_setup.use_setuptools()
  from setuptools import setup, find_packages

setup(
    name='caliendo',
    version='2.0.8',
    packages=find_packages(),
    author='Andrew Kelleher',
    author_email='andrew.kelleher@buzzfeed.com',
    description='Makes mocking services for tests simpler.',
    long_description='Allows patching and caching of target methods with VERY little effort.',
    test_suite='test.caliendo_test',
    install_requires=[
        'mock==1.0.0',
        'dill==0.2b1'
    ],
    url='http://www.github.com/buzzfeed/caliendo',
    download_url='https://github.com/buzzfeed/caliendo/archive/2.0.8.tar.gz'
)
