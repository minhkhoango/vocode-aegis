#!/usr/bin/env python3
"""
Demonstration script for testing the enhanced health check functionality.
This script shows how to inject errors into Redis to test the severity weighting.
"""

import asyncio
import redis.asyncio as redis
from typing import Dict, List, Tuple, cast

# Type aliases for Redis operations
RedisXReadResult = List[Tuple[str, List[Tuple[str, Dict[str, str]]]]]

async def inject_test_errors():
    """Inject test errors into Redis to demonstrate the enhanced health check."""
    
    print("🚀 Demonstrating Enhanced Health Check with Severity Weighting")
    print("=" * 60)
    
    # Connect to Redis
    try:
        redis_client = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )
        
        # Test Redis connection
        await redis_client.ping()  # type: ignore
        print("✅ Connected to Redis successfully")
        
        # Test 1: Inject a high severity error
        print("\n📋 Test 1: Injecting HIGH severity error")
        high_error_data = {
            'error_type': 'LLM_CRITICAL_FAILURE',
            'message': 'LLM service completely down - all calls failing',
            'severity': 'high',
            'conversation_id': 'test-conv-001'
        }
        
        # Use xadd with proper field format
        msg_id: str = cast(str, await redis_client.xadd('vocode:errors', high_error_data))  # type: ignore
        print(f"✅ Injected HIGH severity error: {high_error_data['error_type']} (ID: {msg_id})")
        print("   Expected: Dashboard should turn RED with 'RED ALERT' message")
        
        print("⏳ Waiting 5 seconds to observe UI changes...")
        await asyncio.sleep(5)
        
        # Test 2: Inject a critical severity error
        print("\n📋 Test 2: Injecting CRITICAL severity error")
        critical_error_data = {
            'error_type': 'SYSTEM_CRASH',
            'message': 'System completely crashed - immediate attention required',
            'severity': 'critical',
            'conversation_id': 'test-conv-002'
        }
        
        msg_id = cast(str, await redis_client.xadd('vocode:errors', critical_error_data))  # type: ignore
        print(f"✅ Injected CRITICAL severity error: {critical_error_data['error_type']} (ID: {msg_id})")
        print("   Expected: Dashboard should turn RED with 'CRITICAL' message")
        
        print("⏳ Waiting 5 seconds to observe UI changes...")
        await asyncio.sleep(5)
        
        # Test 3: Inject multiple medium severity errors
        print("\n📋 Test 3: Injecting multiple MEDIUM severity errors")
        medium_errors = [
            {
                'error_type': 'AUDIO_PROCESSING_FAILURE',
                'message': 'Audio processing failed for conversation',
                'severity': 'medium',
                'conversation_id': 'test-conv-003'
            },
            {
                'error_type': 'DATABASE_CONNECTION_ERROR',
                'message': 'Database connection timeout',
                'severity': 'medium',
                'conversation_id': 'test-conv-004'
            },
            {
                'error_type': 'LLM_TIMEOUT',
                'message': 'LLM response timeout after 30s',
                'severity': 'medium',
                'conversation_id': 'test-conv-005'
            }
        ]
        
        for error in medium_errors:
            msg_id = cast(str, await redis_client.xadd('vocode:errors', error))  # type: ignore
            print(f"✅ Injected MEDIUM severity error: {error['error_type']} (ID: {msg_id})")
        
        print("   Expected: Dashboard should turn YELLOW with 'WARNING' message")
        print("⏳ Waiting 5 seconds to observe UI changes...")
        await asyncio.sleep(5)
        
        # Test 4: Inject low severity errors
        print("\n📋 Test 4: Injecting LOW severity errors")
        low_errors = [
            {
                'error_type': 'RATE_LIMIT_EXCEEDED',
                'message': 'Rate limit exceeded for API calls',
                'severity': 'low',
                'conversation_id': 'test-conv-006'
            },
            {
                'error_type': 'CONNECTION_TIMEOUT',
                'message': 'Connection timeout - retrying',
                'severity': 'low',
                'conversation_id': 'test-conv-007'
            }
        ]
        
        for error in low_errors:
            msg_id = cast(str, await redis_client.xadd('vocode:errors', error))  # type: ignore
            print(f"✅ Injected LOW severity error: {error['error_type']} (ID: {msg_id})")
        
        print("   Expected: Dashboard should remain GREEN with info message")
        print("⏳ Waiting 5 seconds to observe UI changes...")
        await asyncio.sleep(5)
        
        # Verify errors were added to Redis
        print("\n🔍 Verifying errors in Redis...")
        try:
            # Get the last 10 messages from the stream
            messages: RedisXReadResult = cast(RedisXReadResult, await redis_client.xread({'vocode:errors': '0'}, count=10))  # type: ignore
            if messages:
                print(f"✅ Found {len(messages[0][1])} messages in vocode:errors stream")
                for msg_id, fields in messages[0][1]:
                    print(f"   - {msg_id}: {fields}")
            else:
                print("❌ No messages found in vocode:errors stream")
        except Exception as e:
            print(f"❌ Error reading from Redis stream: {e}")
        
        print("\n🎯 Testing Instructions:")
        print("1. Start the Vocode application: docker-compose up")
        print("2. Open the dashboard at http://localhost:3001")
        print("3. Watch the 'System Status' indicator change based on error severity")
        print("4. Check the health endpoint: curl http://localhost:8000/health")
        print("5. The health endpoint should now include 'live_status' with detailed info")
        
        print("\n📊 Expected Behavior:")
        print("- HIGH/CRITICAL errors → RED status with alarming messages")
        print("- MEDIUM errors → YELLOW status with warning messages") 
        print("- LOW errors → GREEN status with info messages")
        print("- Health endpoint prioritizes LiveStatus over Redis connectivity")
        
    except Exception as e:
        print(f"❌ Error connecting to Redis: {e}")
        print("Make sure Redis is running: docker-compose up redis")

if __name__ == "__main__":
    asyncio.run(inject_test_errors()) 