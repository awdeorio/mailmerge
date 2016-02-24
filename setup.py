try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="mailmerge",
    version="0.1",
    author="Andrew DeOrio",
    author_email="awdeorio@umich.edu",
    url="https://github.com/awdeorio/mailmerge/",
    license="MIT",
    packages = ["mailmerge"],
    scripts=["bin/mailmerge"],
    install_requires=[
        "click>=6.2",
        "Jinja2>=2.8",
        ],
)
