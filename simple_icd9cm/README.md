# simple_icd9cm

A simple Python package for querying ICD-9-CM codes, inspired by icd9.py.

## Install

```sh
pip install .
```

## Usage

```python
from simple_icd9cm.icd9cm import ICD9
icd9 = ICD9()  # uses codes.json by default
cholera = icd9.find('001.0')
print(cholera.description)
```

## Data
This package expects a `codes.json` file in the package directory, formatted as in the original icd9.py.

## Extending
You can load your own data by passing a path to ICD9(codesfname=...). 