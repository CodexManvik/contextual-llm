#!/usr/bin/env python3
"""
Test script for Cache and Search Manager functionality
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_cache_manager():
    """Test CacheManager functionality"""
    print("🧪 Testing Cache Manager")
    print("=" * 40)
    
    try:
        from src.core.cache_manager import CacheManager
        
        cache_manager = CacheManager()
        
        # Test adding vectors
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        test_metadata = {"text": "test document", "category": "test"}
        
        cache_manager.add_vector(test_vector, test_metadata)
        print("✅ Vector added successfully")
        
        # Test querying
        results = cache_manager.query_vector(test_vector, n_results=1)
        print(f"✅ Query results: {len(results['ids'][0])} results found")
        
        # Test getting stats
        stats = cache_manager.get_stats()
        print(f"✅ Cache stats: {stats}")
        
        # Test clearing
        cache_manager.clear()
        print("✅ Cache cleared successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache Manager test failed: {e}")
        return False

def test_search_manager():
    """Test SearchManager functionality"""
    print("\n🧪 Testing Search Manager")
    print("=" * 40)
    
    try:
        from src.core.search_manager import SearchManager
        
        search_manager = SearchManager()
        
        # Test adding documents
        test_documents = [
            "The quick brown fox jumps over the lazy dog",
            "Artificial intelligence is transforming the world",
            "Machine learning algorithms can learn from data",
            "Natural language processing helps computers understand human language"
        ]
        
        for doc in test_documents:
            search_manager.add_to_search_index(doc)
        print("✅ Documents indexed successfully")
        
        # Test semantic search
        query = "AI and machine learning"
        results = search_manager.semantic_search(query, n_results=2)
        print(f"✅ Semantic search for '{query}': {len(results)} results")
        for result in results:
            print(f"   - {result['text'][:50]}... (distance: {result['distance']:.3f})")
        
        # Test finding similar
        similar = search_manager.find_similar("artificial intelligence", threshold=0.8)
        print(f"✅ Similar documents found: {len(similar)}")
        
        # Test batch indexing
        more_docs = [
            "Deep learning uses neural networks with many layers",
            "Computer vision enables machines to see and interpret images"
        ]
        search_manager.batch_index(more_docs)
        print("✅ Batch indexing completed")
        
        # Test stats
        stats = search_manager.get_index_stats()
        print(f"✅ Search index stats: {stats}")
        
        # Test clearing
        search_manager.clear_index()
        print("✅ Search index cleared")
        
        return True
        
    except Exception as e:
        print(f"❌ Search Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🤖 Cache and Search Manager Test Suite")
    print("=" * 50)
    
    cache_success = test_cache_manager()
    search_success = test_search_manager()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Cache Manager: {'✅ PASS' if cache_success else '❌ FAIL'}")
    print(f"Search Manager: {'✅ PASS' if search_success else '❌ FAIL'}")
    
    if cache_success and search_success:
        print("\n🎉 All tests passed! Cache and Search systems are working correctly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
