import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from icd9_llm_tree_search.tree_search import ICD9LLMTreeSearch
from simple_icd9cm.icd9cm import ICD9

class DummyLLMTreeSearch(ICD9LLMTreeSearch):
    def __init__(self):
        super().__init__(api_key="dummy-key")
    def _llm_decide(self, note, nodes):
        # Always say Yes to the first child, No to others
        lines = []
        for i, n in enumerate(nodes):
            if i == 0:
                lines.append(f"{n.code}: Yes")
            else:
                lines.append(f"{n.code}: No")
        return "\n".join(lines)

class KeywordLLMTreeSearch(ICD9LLMTreeSearch):
    def __init__(self, keyword):
        super().__init__(api_key="dummy-key")
        self.keyword = keyword
    def _llm_decide(self, note, nodes):
        # Say Yes to the first child if keyword is in note, else No to all
        lines = []
        for i, n in enumerate(nodes):
            if i == 0 and self.keyword.lower() in note.lower():
                lines.append(f"{n.code}: Yes")
            else:
                lines.append(f"{n.code}: No")
        return "\n".join(lines)

class TuberculosisLLMTreeSearch(ICD9LLMTreeSearch):
    def __init__(self):
        super().__init__(api_key="dummy-key")
    def _llm_decide(self, note, nodes):
        # Simulate the correct path to 011.43 for the test note
        # Find the node for '011.43' or its ancestors and say Yes for them
        yes_codes = set([
            '001-139',  # Infectious and Parasitic Diseases
            '010-018',  # Tuberculosis
            '011',      # Pulmonary tuberculosis
            '011.4',    # Tuberculosis of lung, tuberculous fibrosis
            '011.43'    # Tuberculous fibrosis of lung, tubercle bacilli found by microscopy
        ])
        print("\n[DEBUG] LLM deciding for children:")
        for n in nodes:
            print(f"  {n.code}: {n.description}")
        lines = []
        for n in nodes:
            if n.code in yes_codes:
                lines.append(f"{n.code}: Yes")
            else:
                lines.append(f"{n.code}: No")
        return "\n".join(lines)

def test_tree_search_selects_first_child():
    searcher = DummyLLMTreeSearch()
    note = "Test note."
    codes = searcher.run_tree_search(note, max_depth=2)
    # Should return at least one code (the first child at each level)
    assert len(codes) > 0
    # All codes should be valid ICD-9 codes
    icd9 = ICD9()
    for code in codes:
        assert icd9.find(code) is not None 

def test_tree_search_with_keyword():
    searcher = KeywordLLMTreeSearch(keyword="cholera")
    note = "Patient presents with symptoms of cholera."
    codes = searcher.run_tree_search(note, max_depth=2)
    assert len(codes) > 0
    icd9 = ICD9()
    for code in codes:
        assert icd9.find(code) is not None 

def test_tree_search_tuberculosis():
    searcher = TuberculosisLLMTreeSearch()
    note = "Patient with tuberculous fibrosis of lung, tubercle bacilli found in sputum by microscopy"
    codes = searcher.run_tree_search(note, max_depth=7)
    assert '011.4' in codes 

@pytest.mark.integration
def test_tree_search_for_erythema_nodosum():
    """
    Tests the full LLM tree search for a specific clinical note.
    
    This is an integration test and requires a running LM Studio instance
    with a model loaded, accessible at http://localhost:1234/v1.
    """
    note = "Patient showing erythema nodosum with hypersensitivity reaction in tuberculosis"
    expected_code = '017.1'

    # Ensure the package is installed in editable mode for this to work
    # and that LM Studio is running.
    searcher = ICD9LLMTreeSearch(
        model_name="local-model", # The model name doesn't matter for LM Studio
        api_key="lm-studio",
        base_url="http://localhost:1234/v1"
    )

    results = searcher.run_tree_search(note, max_depth=5)
    
    # After the search, you can get the description like this:
    # description = searcher.icd9.find(expected_code).description
    # print(f"Found description for {expected_code}: {description}")

    assert expected_code in results, f"Expected code {expected_code} not found in results: {results}" 