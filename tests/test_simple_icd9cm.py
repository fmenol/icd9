import os
import pytest
from simple_icd9cm.icd9cm import ICD9

def test_icd9_find_and_description():
    icd9 = ICD9()
    node = icd9.find('001.0')
    assert node is not None
    assert 'cholera' in node.description.lower()

def test_icd9_search():
    icd9 = ICD9()
    results = icd9.search('001')
    assert any(n.code == '001.0' for n in results)

def test_icd9_children():
    icd9 = ICD9()
    node = icd9.find('001')
    children_codes = [child.code for child in node.children]
    assert '001-009' in children_codes

def test_icd9_parents():
    icd9 = ICD9()
    node = icd9.find('001.0')
    parent_codes = [n.code for n in node.parents]
    assert '001' in parent_codes

def test_icd9_leaves():
    icd9 = ICD9()
    leaves = icd9.leaves
    assert any(n.code == '001.0' for n in leaves)

def test_find_codes_for_note():
    icd9 = ICD9()
    note = "Patient diagnosed with cholera."
    results = icd9.find_codes_for_note(note)
    codes = [code for code, desc in results]
    assert '001.0' in codes
    assert any('cholera' in desc.lower() for code, desc in results) 