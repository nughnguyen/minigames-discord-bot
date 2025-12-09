"""
Test script để kiểm tra Dictionary API
Run: python test_api.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.dictionary_api import init_dictionary_service, close_dictionary_service


async def test_english_words():
    """Test từ tiếng Anh"""
    print("\n" + "="*60)
    print("🇬🇧 Testing English Words")
    print("="*60)
    
    test_words = [
        ("hello", True),
        ("world", True),
        ("python", True),
        ("xyzabc123", False),  # Invalid
        ("beautiful", True),
        ("asdfghjkl", False),  # Invalid
    ]
    
    from utils.dictionary_api import dictionary_service
    
    for word, expected in test_words:
        result = await dictionary_service.is_valid_word(word, 'en')
        status = "✅" if result == expected else "❌"
        print(f"{status} '{word}': {result} (expected: {expected})")


async def test_vietnamese_words():
    """Test từ tiếng Việt"""
    print("\n" + "="*60)
    print("🇻🇳 Testing Vietnamese Words")
    print("="*60)
    
    test_words = [
        ("xin chào", True),
        ("cảm ơn", True),
        ("tạm biệt", True),
        ("asdfxyz", False),  # Invalid
        ("chào buổi sáng", True),
    ]
    
    from utils.dictionary_api import dictionary_service
    
    for word, expected in test_words:
        result = await dictionary_service.is_valid_word(word, 'vi')
        status = "✅" if result == expected else "❌"
        print(f"{status} '{word}': {result} (expected: {expected})")


async def test_cache():
    """Test cache performance"""
    print("\n" + "="*60)
    print("💾 Testing Cache Performance")
    print("="*60)
    
    from utils.dictionary_api import dictionary_service
    import time
    
    word = "hello"
    
    # First call (no cache)
    start = time.time()
    await dictionary_service.is_valid_word(word, 'en')
    first_call = (time.time() - start) * 1000
    
    # Second call (from cache)
    start = time.time()
    await dictionary_service.is_valid_word(word, 'en')
    second_call = (time.time() - start) * 1000
    
    print(f"First call (API):   {first_call:.2f}ms")
    print(f"Second call (Cache): {second_call:.2f}ms")
    print(f"Speedup: {first_call/second_call:.1f}x faster! ⚡")
    
    # Cache stats
    stats = dictionary_service.get_cache_stats()
    print(f"\nCache Stats: {stats}")


async def test_fallback():
    """Test fallback khi API fail"""
    print("\n" + "="*60)
    print("🔄 Testing Fallback Strategy")
    print("="*60)
    
    print("Initializing service with API disabled...")
    
    # Close current service
    await close_dictionary_service()
    
    # Reinitialize without API
    fallback = {'en': {'hello', 'world', 'test'}, 'vi': {'xin chào', 'cảm ơn'}}
    await init_dictionary_service(use_api=False, fallback_words=fallback)
    
    from utils.dictionary_api import dictionary_service
    
    print("\n📝 Testing with local fallback only:")
    
    # Should be in fallback
    result = await dictionary_service.is_valid_word('hello', 'en')
    print(f"✅ 'hello' (in fallback): {result}")
    
    # Should NOT be in fallback
    result = await dictionary_service.is_valid_word('python', 'en')
    print(f"❌ 'python' (NOT in fallback): {result}")


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("🧪 Dictionary API Test Suite")
    print("="*60)
    
    try:
        # Initialize service
        print("\nInitializing Dictionary Service...")
        
        # Load some fallback words
        fallback = {
            'en': {'hello', 'world', 'test', 'python'},
            'vi': {'xin chào', 'cảm ơn', 'tạm biệt'}
        }
        
        await init_dictionary_service(use_api=True, fallback_words=fallback)
        print("✅ Service initialized!")
        
        # Run tests
        await test_english_words()
        await test_vietnamese_words()
        await test_cache()
        await test_fallback()
        
        print("\n" + "="*60)
        print("✨ All tests completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await close_dictionary_service()


if __name__ == "__main__":
    print("\n🚀 Starting tests...\n")
    asyncio.run(main())
