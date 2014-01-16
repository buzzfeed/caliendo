__author__ = "andrew.kelleher@buzzfeed.com (Andrew Kelleher)"

try:
  from setuptools import setup, find_packages
except ImportError:
  import distribute_setup
  distribute_setup.use_setuptools()
  from setuptools import setup, find_packages

setup(
    name='caliendo',
    version='2.1.3',
    packages=find_packages(),
    author='Andrew Kelleher',
    author_email='andrew.kelleher@buzzfeed.com',
    description='Makes mocking services for tests simpler by caching calls to services and loading those responses as fixtures.',
    long_description='Makes mocking services for tests simpler by caching calls to services and loading those responses as fixtures.',
    test_suite='test.all_tests',
    install_requires=[
        'mock==1.0.0',
        'dill==0.2b1'
    ],
    url='http://www.github.com/buzzfeed/caliendo',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
    ],
    keywords="test testing mock mocking api service cache caching integration unit",
)
