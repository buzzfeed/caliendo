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
    version='v0.1.2',
    packages=find_packages(),
    author='Andrew Kelleher',
    author_email='andrew.kelleher@buzzfeed.com',
    description='A facade for wrapping API methods for logging i/o',
    long_description='A facade for wrapping API methods for logging i/o',
    test_suite='test.caliendo_test',
    install_requires=[
        'MySQL-python==1.2.4c1',
        'paramiko==1.9.0',
        'pycrypto==2.6',
        'pysqlite==2.6.3',
        'wsgiref==0.1.2'
    ],
)
