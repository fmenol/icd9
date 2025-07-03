# icd9_llm_tree_search

A Python package for LLM-guided ICD-9 code prediction using tree search, inspired by the tree search approach in clinical coding LLM research.

## Install

```sh
pip install .
```

## Usage

```python
from icd9_llm_tree_search.tree_search import ICD9LLMTreeSearch

# For LM Studio or OpenAI-compatible endpoints:
searcher = ICD9LLMTreeSearch(model_name="gpt-3.5-turbo", api_key="sk-...", base_url="http://localhost:1234/v1")

note = "Patient presents with symptoms of cholera."
predicted_codes = searcher.run_tree_search(note)
print(predicted_codes)
```

- `model_name`: The model to use (e.g., "gpt-3.5-turbo", "llama").
- `api_key`: Your OpenAI or LM Studio API key.
- `base_url`: The endpoint for LM Studio or other OpenAI-compatible servers.

## Requirements
- `openai` Python package
- `simple_icd9cm` (this repo) 