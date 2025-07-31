#!/usr/bin/env python3
"""
Simple performance test for the Research Brief Generator API
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime

async def test_api_performance():
    """Test API performance with multiple concurrent requests."""
    
    # Test configuration
    base_url = "http://localhost:8000"
    test_topics = [
        "artificial intelligence",
        "machine learning",
        "blockchain technology",
        "quantum computing",
        "cybersecurity"
    ]
    
    async def make_request(session, topic, user_id):
        """Make a single API request."""
        start_time = time.time()
        
        payload = {
            "topic": topic,
            "depth": 2,  # Use depth 2 for faster testing
            "user_id": user_id,
            "follow_up": False
        }
        
        try:
            async with session.post(
                f"{base_url}/brief",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            ) as response:
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "topic": topic,
                        "duration": duration,
                        "brief_id": data.get("brief", {}).get("brief_id"),
                        "status_code": response.status
                    }
                else:
                    return {
                        "success": False,
                        "topic": topic,
                        "duration": duration,
                        "error": f"HTTP {response.status}",
                        "status_code": response.status
                    }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "topic": topic,
                "duration": time.time() - start_time,
                "error": str(e),
                "status_code": None
            }
    
    # Test health endpoint first
    print("🔍 Testing API health...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    print("✅ API is healthy")
                else:
                    print(f"❌ API health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return
    
    # Run performance tests
    print(f"\n🚀 Starting performance test with {len(test_topics)} topics...")
    print("=" * 60)
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Sequential test
        print("📊 Sequential Requests:")
        sequential_results = []
        for i, topic in enumerate(test_topics, 1):
            print(f"  {i}. Testing: {topic}")
            result = await make_request(session, topic, f"perf_user_{i}")
            sequential_results.append(result)
            
            if result["success"]:
                print(f"     ✅ Success in {result['duration']:.2f}s")
            else:
                print(f"     ❌ Failed: {result['error']}")
        
        # Concurrent test
        print(f"\n⚡ Concurrent Requests:")
        concurrent_tasks = []
        for i, topic in enumerate(test_topics, 1):
            task = make_request(session, topic, f"concurrent_user_{i}")
            concurrent_tasks.append(task)
        
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        for i, result in enumerate(concurrent_results, 1):
            if isinstance(result, dict) and result["success"]:
                print(f"  {i}. {result['topic']}: ✅ {result['duration']:.2f}s")
            else:
                print(f"  {i}. Failed: {result}")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful_sequential = [r for r in sequential_results if r["success"]]
    successful_concurrent = [r for r in concurrent_results if isinstance(r, dict) and r["success"]]
    
    print("\n" + "=" * 60)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Total test time: {total_time:.2f}s")
    print(f"Sequential requests: {len(successful_sequential)}/{len(test_topics)} successful")
    print(f"Concurrent requests: {len(successful_concurrent)}/{len(test_topics)} successful")
    
    if successful_sequential:
        avg_sequential = sum(r["duration"] for r in successful_sequential) / len(successful_sequential)
        print(f"Average sequential time: {avg_sequential:.2f}s")
    
    if successful_concurrent:
        avg_concurrent = sum(r["duration"] for r in successful_concurrent) / len(successful_concurrent)
        print(f"Average concurrent time: {avg_concurrent:.2f}s")
    
    print(f"Total throughput: {len(successful_sequential + successful_concurrent)} requests in {total_time:.2f}s")
    
    # Save results
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_time": total_time,
        "sequential_results": sequential_results,
        "concurrent_results": concurrent_results,
        "summary": {
            "sequential_success": len(successful_sequential),
            "concurrent_success": len(successful_concurrent),
            "total_requests": len(test_topics) * 2
        }
    }
    
    with open("performance_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to performance_results.json")

if __name__ == "__main__":
    asyncio.run(test_api_performance()) 