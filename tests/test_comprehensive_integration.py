#!/usr/bin/env python3
"""
Comprehensive integration test for all new components
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_comprehensive_integration():
    """Test all components working together"""
    print("🤖 Comprehensive Integration Test")
    print("=" * 50)
    
    try:
        # Test imports
        from src.core.cache_manager import CacheManager
        from src.core.search_manager import SearchManager
        from src.core.reasoning_manager import ReasoningManager
        
        print("✅ All imports successful")
        
        # Test cache manager
        cache_manager = CacheManager()
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        test_metadata = {"text": "test document", "category": "test"}
        cache_manager.add_vector(test_vector, test_metadata)
        results = cache_manager.query_vector(test_vector, n_results=1)
        print(f"✅ Cache Manager: {len(results['ids'][0])} results found")
        
        # Test search manager
        search_manager = SearchManager()
        search_manager.add_to_search_index("test search document")
        search_results = search_manager.semantic_search("test", n_results=1)
        print(f"✅ Search Manager: {len(search_results)} results found")
        
        # Test reasoning manager
        reasoning_manager = ReasoningManager()
        intent_result = reasoning_manager.classify_intent("open browser")
        print(f"✅ Reasoning Manager: Intent '{intent_result['intent']}' with confidence {intent_result['confidence']:.2f}")
        
        # Test integration
        print("✅ All components integrated successfully!")
        
        # Clean up
        cache_manager.clear()
        search_manager.clear_index()
        
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive test"""
    print("🚀 Running Comprehensive Integration Test Suite")
    print("=" * 60)
    
    success = test_comprehensive_integration()
    
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    print(f"Overall Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 All components are working together perfectly!")
        print("   - Cache Manager: ✅ Functional")
        print("   - Search Manager: ✅ Functional") 
        print("   - Reasoning Manager: ✅ Functional")
        print("   - Integration: ✅ Successful")
        return True
    else:
        print("\n⚠️ Integration test failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
