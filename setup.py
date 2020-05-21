from setuptools import find_packages, setup

with open('README.md', 'r') as f:
    readme = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='reqbench',
    version='0.0.1',
    author='Ivan Gorbachev',
    author_email='ip0000h@gmail.com',
    description='Reqbench is a tool for load testing web apps.',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/ip0000h/reqbench',
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=required,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
    ],
)
