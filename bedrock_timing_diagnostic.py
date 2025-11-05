"""
Diagnostic script to measure Bedrock latency breakdown.
Add this to your BedrockProvider to identify bottlenecks.
"""

import time
import json
import boto3
from botocore.config import Config

def diagnose_bedrock_latency(region='us-east-1', model_id='us.anthropic.claude-haiku-4-5-20250910-v1:0'):
    """
    Measure latency breakdown for Bedrock API calls.
    """
    print(f"\n{'='*60}")
    print(f"Testing Bedrock Latency in region: {region}")
    print(f"Model: {model_id}")
    print(f"{'='*60}\n")

    # Test 1: Client initialization time
    start = time.time()
    boto_config = Config(
        region_name=region,
        retries={'max_attempts': 2, 'mode': 'standard'},
        max_pool_connections=50,
        connect_timeout=5,
        read_timeout=60
    )
    client = boto3.client('bedrock-runtime', config=boto_config)
    init_time = (time.time() - start) * 1000
    print(f"✅ Client initialization: {init_time:.2f}ms")

    # Test 2: Simple streaming request
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Hi"}]
    }

    print(f"\n📤 Sending test request...")
    request_start = time.time()

    try:
        # Measure invoke_model_with_response_stream call
        invoke_start = time.time()
        response = client.invoke_model_with_response_stream(
            modelId=model_id,
            body=json.dumps(body)
        )
        invoke_time = (time.time() - invoke_start) * 1000
        print(f"✅ invoke_model_with_response_stream call: {invoke_time:.2f}ms")

        # Measure time to first chunk
        stream = response.get('body')
        first_chunk_time = None
        chunk_count = 0

        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    chunk_count += 1
                    chunk_data = json.loads(chunk.get('bytes').decode())

                    if first_chunk_time is None and chunk_data.get('type') == 'content_block_delta':
                        first_chunk_time = (time.time() - request_start) * 1000
                        print(f"🚀 Time to first content chunk (TTFC): {first_chunk_time:.2f}ms")
                        print(f"   └─ First chunk content: {chunk_data.get('delta', {}).get('text', '')[:50]}")

                    if chunk_data.get('type') == 'message_stop':
                        break

        total_time = (time.time() - request_start) * 1000
        print(f"✅ Total streaming time: {total_time:.2f}ms")
        print(f"✅ Total chunks received: {chunk_count}")

        # Breakdown analysis
        print(f"\n{'='*60}")
        print(f"LATENCY BREAKDOWN:")
        print(f"{'='*60}")
        print(f"Client init:           {init_time:.2f}ms")
        print(f"API call overhead:     {invoke_time:.2f}ms")
        if first_chunk_time:
            print(f"TTFC (Time to First):  {first_chunk_time:.2f}ms  ⚠️ TARGET METRIC")
            print(f"Streaming completion:  {(total_time - first_chunk_time):.2f}ms")
        print(f"Total:                 {total_time:.2f}ms")

        # Recommendations
        print(f"\n{'='*60}")
        print(f"RECOMMENDATIONS:")
        print(f"{'='*60}")
        if first_chunk_time and first_chunk_time > 2000:
            print(f"⚠️  TTFC is high ({first_chunk_time:.0f}ms > 2000ms)")
            print(f"    Likely causes:")
            print(f"    1. High network latency to {region}")
            print(f"       → Try regions closer to you: us-west-2, eu-west-1, ap-northeast-1")
            print(f"    2. Model cold start")
            print(f"       → Consider using Provisioned Throughput for consistent performance")
            print(f"    3. Region-specific model")
            print(f"       → Try cross-region model (remove 'us.' prefix from model_id)")
        else:
            print(f"✅ TTFC is acceptable ({first_chunk_time:.0f}ms)")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import sys

    # Allow region and model to be specified
    region = sys.argv[1] if len(sys.argv) > 1 else 'us-east-1'
    model_id = sys.argv[2] if len(sys.argv) > 2 else 'us.anthropic.claude-haiku-4-5-20250910-v1:0'

    print("Running Bedrock Latency Diagnostic...")
    print("Usage: python bedrock_timing_diagnostic.py [region] [model_id]")

    diagnose_bedrock_latency(region, model_id)

    # Test multiple regions for comparison
    if len(sys.argv) == 1:
        print("\n\nTesting other regions for comparison...")
        for test_region in ['us-west-2', 'eu-west-1', 'ap-northeast-1']:
            try:
                diagnose_bedrock_latency(test_region, model_id)
            except Exception as e:
                print(f"❌ Failed to test {test_region}: {str(e)}")
