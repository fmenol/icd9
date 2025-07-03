import openai
from simple_icd9cm.icd9cm import ICD9
from .prompt_templates import prompt_template_dict
import re

class ICD9LLMTreeSearch:
    def __init__(self, model_name="gpt-3.5-turbo", api_key=None, base_url=None):
        self.model_name = model_name
        self.icd9 = ICD9()
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url) if base_url else openai.OpenAI(api_key=api_key)
        self.prompt_template = prompt_template_dict["keyword_extraction"]
        self.all_leaves = self.icd9.leaves  # Cache leaves for efficiency

    def _extract_keywords(self, note: str) -> list[str]:
        """
        Pass 1: Use LLM to extract keywords from the clinical note.
        """
        prompt = self.prompt_template.format(note=note)
        messages = [
            {"role": "system", "content": "You are a medical coding assistant that extracts keywords."},
            {"role": "user", "content": prompt}
        ]
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=100
        )
        llm_output = response.choices[0].message.content
        # Clean up the output and split into a list of keywords
        keywords = [k.strip().lower() for k in llm_output.replace('"', '').split(',')]
        print(f"DEBUG: Extracted Keywords: {keywords}")
        return keywords

    def run_search(self, note: str) -> list[str]:
        """
        Runs the new two-pass search:
        1. Extract keywords from the note using an LLM.
        2. Search for those keywords in the descriptions of all terminal ICD-9 codes.
        """
        # Pass 1: Extract Keywords
        keywords = self._extract_keywords(note)

        # Pass 2: Targeted Search in leaf nodes
        found_codes = set()
        for leaf in self.all_leaves:
            description = leaf.description.lower()
            for keyword in keywords:
                if not keyword:
                    continue
                # Use a general substring search, removing word boundaries for robustness
                if re.search(re.escape(keyword), description):
                    found_codes.add(leaf.code)
        
        return list(found_codes) 