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
    version='v0.0.15',
    packages=find_packages(),
    author='Andrew Kelleher',
    author_email='andrew.kelleher@buzzfeed.com',
    description='A facade for wrapping API methods for logging i/o',
    long_description='A facade for wrapping API methods for logging i/o',
)
