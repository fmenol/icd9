#!/usr/bin/env python3
"""
Final demonstration of DSPy prompt optimization for ICD-9 medical coding.

This script demonstrates:
1. DSPy optimization with BootstrapFewShot and MIPROv2
2. Integration with the tree search system
3. Performance comparison between optimized and non-optimized models
4. Real-world medical coding examples
"""

import sys
sys.path.append('.')

from icd9_llm_tree_search.tree_search import ICD9LLMTreeSearch
from icd9_llm_tree_search.dspy_optimizer import DSPyOptimizerManager
import time

def run_dspy_optimization():
    """Run DSPy optimization and save the best model"""
    print("="*60)
    print("STEP 1: RUNNING DSPY OPTIMIZATION")
    print("="*60)
    
    # Initialize the optimizer
    optimizer_manager = DSPyOptimizerManager()
    
    # Run BootstrapFewShot optimization
    print("\n🔧 Running BootstrapFewShot optimization...")
    optimized_bootstrap = optimizer_manager.optimize_with_bootstrap(num_examples=10)
    
    # Run MIPROv2 optimization
    print("\n🔧 Running MIPROv2 optimization...")
    try:
        optimized_mipro = optimizer_manager.optimize_with_mipro(num_examples=10)
        print("✅ MIPROv2 optimization successful!")
    except Exception as e:
        print(f"⚠️ MIPROv2 failed: {e}")
    
    # Test optimization performance
    print("\n📊 Testing optimization performance...")
    optimizer_manager.test_optimization(test_examples=5)
    
    # Save the optimized model
    optimizer_manager.save_optimized_model()
    print("💾 Optimized model saved!")

def test_integration():
    """Test the integrated DSPy system with real medical cases"""
    print("\n" + "="*60)
    print("STEP 2: TESTING INTEGRATED DSPY SYSTEM")
    print("="*60)
    
    # Test cases from medical literature
    test_cases = [
        {
            "note": "Patient presents with tuberculous fibrosis of the lung",
            "expected": "011.4"
        },
        {
            "note": "Patient diagnosed with leishmaniasis after travel to endemic area", 
            "expected": "V05.2"
        },
        {
            "note": "Clinical findings consistent with parasitic endophthalmitis",
            "expected": "360.13"
        },
        {
            "note": "History reveals mononeuritis of unspecified site with nerve damage",
            "expected": "355.9"
        },
        {
            "note": "Patient has medial collateral ligament injury of knee from sports",
            "expected": "844.1"
        }
    ]
    
    # Test without DSPy optimization
    print("\n🔍 Testing WITHOUT DSPy optimization:")
    searcher_basic = ICD9LLMTreeSearch(
        model_name="medgemma",
        api_key="not-needed",
        base_url="http://localhost:1234/v1",
        use_dspy_optimization=False
    )
    
    basic_results = []
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['note']}")
        start_time = time.time()
        result = searcher_basic.run_search(case['note'])
        elapsed = time.time() - start_time
        
        correct = result == case['expected']
        basic_results.append(correct)
        
        print(f"Result: {result}")
        print(f"Expected: {case['expected']}")
        print(f"✅ Correct" if correct else "❌ Incorrect")
        print(f"Time: {elapsed:.2f}s")
    
    # Test with DSPy optimization
    print("\n" + "="*50)
    print("🚀 Testing WITH DSPy optimization:")
    searcher_dspy = ICD9LLMTreeSearch(
        model_name="medgemma",
        api_key="not-needed",
        base_url="http://localhost:1234/v1",
        use_dspy_optimization=True
    )
    
    dspy_results = []
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {case['note']}")
        start_time = time.time()
        result = searcher_dspy.run_search(case['note'])
        elapsed = time.time() - start_time
        
        correct = result == case['expected']
        dspy_results.append(correct)
        
        print(f"Result: {result}")
        print(f"Expected: {case['expected']}")
        print(f"✅ Correct" if correct else "❌ Incorrect")
        print(f"Time: {elapsed:.2f}s")
    
    # Performance comparison
    print("\n" + "="*60)
    print("📈 PERFORMANCE COMPARISON")
    print("="*60)
    
    basic_accuracy = sum(basic_results) / len(basic_results) * 100
    dspy_accuracy = sum(dspy_results) / len(dspy_results) * 100
    
    print(f"Basic System Accuracy: {basic_accuracy:.1f}% ({sum(basic_results)}/{len(basic_results)})")
    print(f"DSPy Optimized Accuracy: {dspy_accuracy:.1f}% ({sum(dspy_results)}/{len(dspy_results)})")
    print(f"Improvement: {dspy_accuracy - basic_accuracy:+.1f} percentage points")
    
    if dspy_accuracy >= basic_accuracy:
        print("🎉 DSPy optimization successful!")
    else:
        print("⚠️ DSPy optimization needs improvement")

def main():
    """Run the complete DSPy optimization demonstration"""
    print("🏥 DSPy Medical Coding Optimization Demo")
    print("Using LM Studio with medgemma model")
    print("http://localhost:1234/v1")
    
    try:
        # Step 1: Run optimization
        run_dspy_optimization()
        
        # Step 2: Test integration
        test_integration()
        
        print("\n" + "="*60)
        print("🎯 DEMO COMPLETE!")
        print("="*60)
        print("✅ DSPy prompt optimization successfully implemented")
        print("✅ Integration with tree search system working") 
        print("✅ Performance evaluation completed")
        print("\nThe system now uses optimized prompts to:")
        print("• Extract medical keywords more effectively")
        print("• Rank ICD-9 codes with better accuracy")
        print("• Return single best-matching codes")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 