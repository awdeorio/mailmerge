try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="mailmerge",
    description = "A simple, command line mail merge tool",
    version="1.7.0",
    author="Andrew DeOrio",
    author_email="awdeorio@umich.edu",
    url="https://github.com/awdeorio/mailmerge/",
    download_url = "https://github.com/awdeorio/mailmerge/tarball/1.6.2",
    license="MIT",
    packages = ["mailmerge"],
    keywords=["mail merge", "mailmerge", "email"],
    install_requires=[
    "click",
    "configparser",
    "jinja2",
    "nose2",
    "sh",
    ],
    test_suite='nose2.collector.collector',
    entry_points="""
    [console_scripts]
    mailmerge=mailmerge.main:main
    """
)
