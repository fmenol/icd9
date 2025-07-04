import openai
from simple_icd9cm.icd9cm import ICD9
from .prompt_templates import prompt_template_dict
import re
import dspy
from typing import Optional

class RankingSignature(dspy.Signature):
    """Rank ICD-9 codes based on clinical note relevance"""
    clinical_note = dspy.InputField(desc="Clinical note describing patient condition")
    candidate_codes = dspy.InputField(desc="List of candidate ICD-9 codes with descriptions")
    best_code = dspy.OutputField(desc="The single most relevant ICD-9 code")


class ICD9LLMTreeSearch:
    def __init__(self, model_name="gpt-3.5-turbo", api_key=None, base_url=None, use_dspy_optimization=True):
        self.model_name = model_name
        self.icd9 = ICD9()
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url) if base_url else openai.OpenAI(api_key=api_key)
        self.prompt_template = prompt_template_dict["keyword_extraction"]
        self.all_leaves = self.icd9.leaves  # Cache leaves for efficiency
        self.use_dspy_optimization = use_dspy_optimization
        self.dspy_ranker = None
        
        # Setup DSPy if optimization is enabled
        if self.use_dspy_optimization and base_url:
            self._setup_dspy(base_url, api_key or "not-needed")
    
    def _setup_dspy(self, base_url: str, api_key: str):
        """Setup DSPy for optimized ranking"""
        try:
            lm = dspy.LM(
                model=f"openai/{self.model_name}",
                base_url=base_url,
                api_key=api_key,
                temperature=0.0,
                max_tokens=50
            )
            dspy.configure(lm=lm)
            self.dspy_ranker = dspy.Predict(RankingSignature)
            print("DSPy optimization enabled for ranking")
        except Exception as e:
            print(f"Failed to setup DSPy: {e}. Falling back to manual ranking.")
            self.use_dspy_optimization = False
    
    def load_optimized_dspy_model(self, model_path: str = "optimized_medical_coder.json"):
        """Load a pre-optimized DSPy model"""
        if not self.use_dspy_optimization:
            print("DSPy optimization not enabled")
            return False
        
        try:
            # Create a DSPy medical coder instance
            from .dspy_optimizer import DSPyMedicalCoder
            optimized_coder = DSPyMedicalCoder()
            optimized_coder.load(model_path)
            
            # Replace the basic ranker with the optimized one  
            self.dspy_ranker = optimized_coder.code_ranker
            print(f"Loaded optimized DSPy model from {model_path}")
            return True
            
        except Exception as e:
            print(f"Failed to load optimized model: {e}")
            return False

    def _extract_keywords(self, note: str) -> list[str]:
        """
        Pass 1: Use LLM to extract keywords from the clinical note.
        """
        prompt = self.prompt_template.format(note=note)
        messages = [
            {"role": "system", "content": "You are a medical coding assistant that extracts keywords from a clinical note."},
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

    def _rank_codes_with_llm(self, note: str, codes: list[str]) -> str:
        """
        Pass 2: Use LLM to rank the retrieved codes and return the best one.
        Uses DSPy optimization if available, otherwise falls back to manual prompting.
        """
        if not codes:
            return None
        if len(codes) == 1:
            return codes[0]

        # Format candidate codes with descriptions
        code_descriptions = []
        for code in codes:
            try:
                node = self.icd9.find(code)
                if node:
                    code_descriptions.append(f"{code}: {node.description}")
                else:
                    code_descriptions.append(f"{code}: Unknown description")
            except:
                code_descriptions.append(f"{code}: Unknown description")
        
        code_list_str = "\n".join(code_descriptions)

        # Use DSPy optimization if available
        if self.use_dspy_optimization and self.dspy_ranker:
            try:
                result = self.dspy_ranker(
                    clinical_note=note,
                    candidate_codes=code_list_str
                )
                best_code = result.best_code.strip()
                print(f"DEBUG: Best code selected by DSPy: {best_code}")
                
                # Validate the result is one of our candidate codes
                for code in codes:
                    if code in best_code:
                        return code
                
                # Fallback to first code if parsing fails
                return codes[0]
                
            except Exception as e:
                print(f"DSPy ranking failed: {e}, falling back to manual ranking")
                self.use_dspy_optimization = False

        # Manual ranking as fallback
        ranking_prompt = (
            f"Given the following clinical note, please rank the following ICD-9 codes by how likely they are to be the correct code for the note.\n\n"
            f"Clinical Note:\n{note}\n\n"
            f"ICD-9 Codes:\n{code_list_str}\n\n"
            f"Please return only the single best code, with no other text."
        )

        messages = [
            {"role": "system", "content": "You are a medical coding assistant that ranks ICD-9 codes."},
            {"role": "user", "content": ranking_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.0,
            max_tokens=10
        )
        best_code = response.choices[0].message.content.strip()
        print(f"DEBUG: Best code selected by manual LLM: {best_code}")
        
        # Basic validation to ensure the returned code is one of the options
        if best_code in codes:
            return best_code
        else:
            # Fallback to the first code if the LLM returns something unexpected
            return codes[0]

    def run_search(self, note: str) -> str:
        """
        Runs the new two-pass search:
        1. Extract keywords from the note using an LLM.
        2. Search for those keywords in the descriptions of all terminal ICD-9 codes.
        3. Rank the results with an LLM and return the best code.
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
        
        # Pass 3: Rank the found codes
        ranked_code = self._rank_codes_with_llm(note, list(found_codes))

        return ranked_code 