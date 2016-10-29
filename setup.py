try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="mailmerge",
    description = "A simple, command line mail merge tool",
    version="1.6.1",
    author="Andrew DeOrio",
    author_email="awdeorio@umich.edu",
    url="https://github.com/awdeorio/mailmerge/",
    download_url = "https://github.com/awdeorio/mailmerge/tarball/1.6.1",
    license="MIT",
    packages = ["mailmerge"],
    scripts=["bin/mailmerge"],
    keywords=["mail merge", "mailmerge", "email"],
    install_requires=[
    "click>=6.6",
    "configparser>=3.5.0",
    "Jinja2>=2.8",
    "nose2>=0.6.5",
    "sh>=1.11",
    ],
    test_suite='nose2.collector.collector',
)
