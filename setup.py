
from setuptools import setup, find_packages

setup(
    name='Noema',
    version='0.1.0',
    description='Description of Noema',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/Noema',
    packages=find_packages(),
    install_requires=[
        'guidance',    
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache 2.0 License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
