from setuptools import setup, find_packages

setup(
    name='icd9_llm_tree_search',
    version='0.1.0',
    description='LLM-guided ICD-9 code prediction using tree search',
    author='Your Name',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'openai',
        'simple_icd9cm',
    ],
    include_package_data=True,
) 