from setuptools import setup

PROJECT_NAME = 'pywrf'
PROJECT_VERSION = __import__(PROJECT_NAME).__version__

with open('README.md') as f:
    PROJECT_README = f.read()

setup(
    name=PROJECT_NAME,
    version=PROJECT_VERSION,
    description='Launch and process WRF simulations',
    long_description=PROJECT_README,
    author='Marc Honnorat',
    author_email='marc@honnorat.fr',
    url='http://github.com/honnorat/pywrf',
    packages=['pywrf'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
    ]
)
