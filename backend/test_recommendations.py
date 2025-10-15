"""
Quick test script to verify recommendation logic
"""
from app.utils.recommendations import get_file_recommendation

def test_recommendations():
    """Test the recommendation logic with different scenarios"""
    
    # Test minimal (≤50 pages, <2MB)
    print("\n=== Test 1: Minimal Setup ===")
    result = get_file_recommendation(pages_count=30, file_size_bytes=1_500_000)  # 1.5 MB
    print(f"Type: {result['type']}")
    print(f"Title: {result['title']}")
    print(f"Files: {result['files']}")
    print(f"Reason: {result['reason']}")
    assert result['type'] == 'minimal', "Should be minimal"
    
    # Test standard (50-500 pages, <10MB)
    print("\n=== Test 2: Standard Setup ===")
    result = get_file_recommendation(pages_count=200, file_size_bytes=5_000_000)  # 5 MB
    print(f"Type: {result['type']}")
    print(f"Title: {result['title']}")
    print(f"Files: {result['files']}")
    print(f"Reason: {result['reason']}")
    assert result['type'] == 'standard', "Should be standard"
    
    # Test complete (>500 pages or ≥10MB)
    print("\n=== Test 3: Complete Setup (many pages) ===")
    result = get_file_recommendation(pages_count=600, file_size_bytes=8_000_000)  # 8 MB
    print(f"Type: {result['type']}")
    print(f"Title: {result['title']}")
    print(f"Files: {result['files']}")
    print(f"Reason: {result['reason']}")
    assert result['type'] == 'complete', "Should be complete"
    
    # Test complete (large file)
    print("\n=== Test 4: Complete Setup (large file) ===")
    result = get_file_recommendation(pages_count=100, file_size_bytes=12_000_000)  # 12 MB
    print(f"Type: {result['type']}")
    print(f"Title: {result['title']}")
    print(f"Files: {result['files']}")
    print(f"Reason: {result['reason']}")
    assert result['type'] == 'complete', "Should be complete"
    
    # Edge case: exactly 50 pages and 2MB
    print("\n=== Test 5: Edge Case (50 pages, 2MB) ===")
    result = get_file_recommendation(pages_count=50, file_size_bytes=2_097_152)  # Exactly 2 MB
    print(f"Type: {result['type']}")
    print(f"Title: {result['title']}")
    print(f"Files: {result['files']}")
    print(f"Reason: {result['reason']}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_recommendations()