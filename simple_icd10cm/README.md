# simple_icd10cm

A simple Python package for querying ICD-10-CM codes, inspired by stefanotrv-simple_icd_10_cm.

## Install

```sh
pip install .
```

## Usage

```python
from simple_icd10cm.icd10cm import ICD10CM
cm = ICD10CM()
print(cm.is_valid_item('A00'))  # True
print(cm.get_description('A00.0'))  # Cholera due to Vibrio cholerae 01, biovar cholerae
print(cm.get_parent('A00.0'))  # A00
print(cm.get_children('A00'))  # ['A00.0', 'A00.1']
print(cm.get_all_codes())
```

## Extending
You can load your own data by passing a list of dicts to ICD10CM(data=...). 