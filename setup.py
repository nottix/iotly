# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='iotly',
    version='0.1.0',
    description='IOT node based on Raspberry Pi GPIO',
    long_description=readme,
    author='Simone Notargiacomo',
    author_email='notargicomo.s@gmail.com',
    url='https://github.com/nottix/iotly',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
