try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="mailmerge",
    description = "A simple, command line mail merge tool",
    version="0.15",
    author="Andrew DeOrio",
    author_email="awdeorio@umich.edu",
    url="https://github.com/awdeorio/mailmerge/",
    download_url = "https://github.com/awdeorio/mailmerge/tarball/0.15",
    license="MIT",
    packages = ["mailmerge"],
    scripts=["bin/mailmerge"],
    keywords=["mail merge", "mailmerge", "email"],
    install_requires=[
        "click>=6.2",
        "Jinja2>=2.8",
        "future==0.15.2",
        ],
    test_suite='nose2.collector.collector',
)
