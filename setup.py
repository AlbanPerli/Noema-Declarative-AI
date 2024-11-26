from setuptools import setup, find_packages

# Lire le contenu du README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='Noema',
    version='1.0.3',
    description='Description of Noema',
    long_description=long_description,  # Inclure la description longue
    long_description_content_type='text/markdown',  # Spécifiez le format de la description (markdown ou rst)
    author='Alban Perli',
    author_email='alban.perli@gmail.com',
    url='https://github.com/AlbanPerli/Noema-Declarative-AI',
    packages=find_packages(),
    install_requires=[
        'guidance',
        'chromadb',
        'sentence_transformers',
        'numpy',
        'autopep8',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
