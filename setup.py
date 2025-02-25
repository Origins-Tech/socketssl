from setuptools import setup, find_packages

VERSION = '1.0.0'
DESCRIPTION = "Sockets Streamlined: A wrapper around the python socket library for easy streamlined use."
LONG_DESCRIPTION = "Simple setup to connect multiple clients to a server to send and receive messages."

setup(
    name="socketssl",
    version=VERSION,
    author="Moritz Strobel",
    author_email="moritz.strobel@outlook.de",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=['socketssl'],
    keywords=['python', 'sockets'],
)