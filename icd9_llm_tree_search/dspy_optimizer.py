#!/usr/bin/env python3

import dspy
from typing import List, Dict, Any
import json
import random
from simple_icd9cm.icd9cm import ICD9


class RankingSignature(dspy.Signature):
    """Rank ICD-9 codes based on clinical note relevance"""
    clinical_note = dspy.InputField(desc="Clinical note describing patient condition")
    candidate_codes = dspy.InputField(desc="List of candidate ICD-9 codes with descriptions")
    best_code = dspy.OutputField(desc="The single most relevant ICD-9 code")


class KeywordExtractionSignature(dspy.Signature):
    """Extract medical keywords from clinical notes"""
    clinical_note = dspy.InputField(desc="Clinical note to analyze")
    keywords = dspy.OutputField(desc="Comma-separated list of medical keywords")


class DSPyMedicalCoder(dspy.Module):
    """DSPy module for medical coding with optimized prompts"""
    
    def __init__(self):
        super().__init__()
        self.keyword_extractor = dspy.Predict(KeywordExtractionSignature)
        self.code_ranker = dspy.Predict(RankingSignature)
        self.icd9 = ICD9()
    
    def forward(self, clinical_note: str, candidate_codes: List[str]) -> str:
        """Forward pass through the medical coding pipeline"""
        
        # Format candidate codes with descriptions
        code_descriptions = []
        for code in candidate_codes:
            try:
                node = self.icd9.find(code)
                if node:
                    code_descriptions.append(f"{code}: {node.description}")
                else:
                    code_descriptions.append(f"{code}: Unknown description")
            except:
                code_descriptions.append(f"{code}: Unknown description")
        
        candidate_codes_str = "\n".join(code_descriptions)
        
        # Use the optimized ranker
        result = self.code_ranker(
            clinical_note=clinical_note,
            candidate_codes=candidate_codes_str
        )
        
        # Extract just the code from the result
        best_code = result.best_code.strip()
        
        # Validate the result is one of our candidate codes
        for code in candidate_codes:
            if code in best_code:
                return code
        
        # Fallback to first code if parsing fails
        return candidate_codes[0] if candidate_codes else None


class DSPyOptimizerManager:
    """Manages DSPy optimization for medical coding"""
    
    def __init__(self, lm_studio_url="http://localhost:1234/v1", model_name="medgemma"):
        self.lm_studio_url = lm_studio_url
        self.model_name = model_name
        self.icd9 = ICD9()
        self.medical_coder = None
        self.optimized_coder = None
        
        # Configure DSPy
        self._setup_dspy()
    
    def _setup_dspy(self):
        """Setup DSPy with LM Studio"""
        lm = dspy.LM(
            model=f"openai/{self.model_name}",
            base_url=self.lm_studio_url,
            api_key="not-needed",
            temperature=0.0,
            max_tokens=200
        )
        
        dspy.configure(lm=lm)
        self.medical_coder = DSPyMedicalCoder()
    
    def generate_training_examples(self, num_examples=20) -> List[dspy.Example]:
        """Generate training examples from ICD-9 codes"""
        print(f"Generating {num_examples} training examples...")
        
        # Get random leaf codes
        all_leaves = list(self.icd9.leaves)
        selected_codes = random.sample(all_leaves, min(num_examples, len(all_leaves)))
        
        examples = []
        for leaf in selected_codes:
            # Create a synthetic clinical note based on the description
            description = leaf.description
            
            # Create a more realistic clinical note
            clinical_note = self._create_clinical_note(description)
            
            # Create some similar/confusing codes as candidates
            candidates = self._get_candidate_codes(leaf.code)
            
            example = dspy.Example(
                clinical_note=clinical_note,
                candidate_codes=candidates,
                best_code=leaf.code
            ).with_inputs("clinical_note", "candidate_codes")
            
            examples.append(example)
        
        print(f"Generated {len(examples)} training examples")
        return examples
    
    def _create_clinical_note(self, description: str) -> str:
        """Create a realistic clinical note from ICD-9 description"""
        # Simple templates to make the description more clinical
        templates = [
            f"Patient presents with {description.lower()}. Assessment and plan discussed.",
            f"Clinical findings consistent with {description.lower()}. Treatment initiated.",
            f"Diagnosis: {description}. Patient counseled on condition.",
            f"History and physical examination reveals {description.lower()}.",
            f"Patient diagnosed with {description.lower()} after thorough evaluation."
        ]
        
        return random.choice(templates)
    
    def _get_candidate_codes(self, correct_code: str, num_candidates=5) -> List[str]:
        """Get candidate codes including the correct one and some similar ones"""
        candidates = [correct_code]
        
        # Add some random leaf codes as distractors
        all_leaves = list(self.icd9.leaves)
        other_codes = [leaf.code for leaf in all_leaves if leaf.code != correct_code]
        
        # Add some random distractors
        num_distractors = min(num_candidates - 1, len(other_codes))
        distractors = random.sample(other_codes, num_distractors)
        candidates.extend(distractors)
        
        # Shuffle to randomize position of correct answer
        random.shuffle(candidates)
        return candidates
    
    def optimize_with_bootstrap(self, num_examples=20, max_bootstrapped_demos=4) -> DSPyMedicalCoder:
        """Optimize the medical coder using BootstrapFewShot"""
        print("Starting DSPy optimization with BootstrapFewShot...")
        
        # Generate training examples
        trainset = self.generate_training_examples(num_examples)
        
        # Define the metric
        def accuracy_metric(example, pred, trace=None):
            """Metric to evaluate predictions"""
            try:
                predicted_code = pred.best_code.strip() if hasattr(pred, 'best_code') else str(pred).strip()
                expected_code = example.best_code.strip()
                
                # Check exact match or if expected code is in predicted result
                return (expected_code == predicted_code or 
                       expected_code in predicted_code or
                       any(expected_code == code.strip() for code in predicted_code.split() if code.strip()))
            except Exception as e:
                print(f"Metric error: {e}, pred: {pred}, example: {example}")
                return False
        
        # Configure the optimizer
        config = dict(max_bootstrapped_demos=max_bootstrapped_demos, max_labeled_demos=4)
        
        # Initialize the optimizer
        optimizer = dspy.BootstrapFewShot(
            metric=accuracy_metric,
            **config
        )
        
        print("Running optimization...")
        # Compile the optimized program
        self.optimized_coder = optimizer.compile(
            self.medical_coder,
            trainset=trainset
        )
        
        print("Optimization complete!")
        return self.optimized_coder
    
    def optimize_with_mipro(self, num_examples=20) -> DSPyMedicalCoder:
        """Optimize using MIPROv2 for better prompt optimization"""
        print("Starting DSPy optimization with MIPROv2...")
        
        # Generate training examples
        trainset = self.generate_training_examples(num_examples)
        
        # Split into train/val
        train_size = int(0.8 * len(trainset))
        train_examples = trainset[:train_size]
        val_examples = trainset[train_size:]
        
        # Define the metric
        def accuracy_metric(example, pred, trace=None):
            """Metric to evaluate predictions"""
            try:
                predicted_code = pred.best_code.strip() if hasattr(pred, 'best_code') else str(pred).strip()
                expected_code = example.best_code.strip()
                
                # Check exact match or if expected code is in predicted result
                return (expected_code == predicted_code or 
                       expected_code in predicted_code or
                       any(expected_code == code.strip() for code in predicted_code.split() if code.strip()))
            except Exception as e:
                print(f"Metric error: {e}, pred: {pred}, example: {example}")
                return False
        
        # Initialize MIPROv2 optimizer with correct parameters
        optimizer = dspy.MIPROv2(
            metric=accuracy_metric,
            auto="light",  # Use light optimization for faster results
            verbose=True
        )
        
        print("Running MIPROv2 optimization...")
        # Compile the optimized program
        self.optimized_coder = optimizer.compile(
            self.medical_coder,
            trainset=train_examples,
            valset=val_examples if val_examples else None
        )
        
        print("MIPROv2 optimization complete!")
        return self.optimized_coder
    
    def test_optimization(self, test_examples=5):
        """Test the optimized vs non-optimized performance"""
        print("Testing optimization performance...")
        
        # Generate test examples
        test_set = self.generate_training_examples(test_examples)
        
        original_correct = 0
        optimized_correct = 0
        
        for example in test_set:
            # Test original
            try:
                orig_result = self.medical_coder(
                    clinical_note=example.clinical_note,
                    candidate_codes=example.candidate_codes
                )
                orig_code = orig_result.strip() if isinstance(orig_result, str) else str(orig_result).strip()
                if example.best_code == orig_code or example.best_code in orig_code:
                    original_correct += 1
            except Exception as e:
                print(f"Original test error: {e}")
                pass
            
            # Test optimized
            if self.optimized_coder:
                try:
                    opt_result = self.optimized_coder(
                        clinical_note=example.clinical_note,
                        candidate_codes=example.candidate_codes
                    )
                    opt_code = opt_result.strip() if isinstance(opt_result, str) else str(opt_result).strip()
                    if example.best_code == opt_code or example.best_code in opt_code:
                        optimized_correct += 1
                except Exception as e:
                    print(f"Optimized test error: {e}")
                    pass
        
        print(f"Original accuracy: {original_correct}/{test_examples} = {original_correct/test_examples:.2%}")
        if self.optimized_coder:
            print(f"Optimized accuracy: {optimized_correct}/{test_examples} = {optimized_correct/test_examples:.2%}")
    
    def save_optimized_model(self, filepath="optimized_medical_coder.json"):
        """Save the optimized model"""
        if self.optimized_coder:
            self.optimized_coder.save(filepath)
            print(f"Optimized model saved to {filepath}")
    
    def load_optimized_model(self, filepath="optimized_medical_coder.json"):
        """Load a previously optimized model"""
        try:
            self.optimized_coder = DSPyMedicalCoder()
            self.optimized_coder.load(filepath)
            print(f"Optimized model loaded from {filepath}")
            return self.optimized_coder
        except Exception as e:
            print(f"Failed to load model: {e}")
            return None


def main():
    """Main function to run optimization"""
    print("Starting DSPy Medical Coding Optimization...")
    
    # Initialize the optimizer
    optimizer_manager = DSPyOptimizerManager()
    
    # Try different optimization methods
    print("\n=== Testing BootstrapFewShot ===")
    optimized_bootstrap = optimizer_manager.optimize_with_bootstrap(num_examples=15)
    optimizer_manager.test_optimization(test_examples=5)
    
    print("\n=== Testing MIPROv2 ===")
    try:
        optimized_mipro = optimizer_manager.optimize_with_mipro(num_examples=15)
        optimizer_manager.test_optimization(test_examples=5)
    except Exception as e:
        print(f"MIPROv2 failed: {e}")
    
    # Save the best model
    optimizer_manager.save_optimized_model()
    
    print("\nOptimization complete!")


if __name__ == "__main__":
    main() 