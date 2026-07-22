from setuptools import setup, find_packages

# Lire le contenu du README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='Noema',
    version='1.1.3',
    description='A declarative way to control LLMs.',
    long_description=long_description,  
    long_description_content_type='text/markdown',  
    author='Alban Perli',
    author_email='alban.perli@gmail.com',
    url='https://github.com/AlbanPerli/Noema-Declarative-AI',
    packages=find_packages(),
    install_requires=[
        'guidance>=0.3.1,<0.4',
        'llama-cpp-python @ git+https://github.com/abetlen/llama-cpp-python.git@629bd1b333f60d24a01886c5f99019f4c7c3ea6c',
        'varname>=0.13,<0.15',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
