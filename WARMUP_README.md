# Model Warmup Feature

## Overview

The FastAPI server now includes automatic model warmup to reduce Time To First Token (TTFT) by preventing cold starts.

## How It Works

### Background Task
- A background task starts 30 seconds after server startup
- Every **2 minutes**, it sends a minimal request to Bedrock
- This keeps the model container "warm" in AWS
- Prevents cold starts for subsequent real requests

### Benefits
- **Before warmup:** TTFT ~4000ms (cold start)
- **After warmup:** TTFT ~500-1500ms (warm model)
- **Works best for:** Apps with regular traffic (requests within 5-10 min of each other)

## Configuration

### Adjust Warmup Interval

Edit `main.py`:
```python
warmup_interval = 120  # Seconds between warmup requests (default: 2 minutes)
```

**Recommendations:**
- **High traffic app:** 120s (2 min) - keeps model very warm
- **Medium traffic:** 180s (3 min) - good balance
- **Low traffic:** 300s (5 min) - reduces costs, model may cool slightly

### Disable Warmup

Set environment variable:
```bash
export DISABLE_WARMUP=true
```

Or comment out in `lifespan()`:
```python
# _warmup_task = asyncio.create_task(warmup_model())
```

## Monitoring

### Check Warmup Status

```bash
curl http://localhost:8000/v1/warmup/status
```

Response:
```json
{
  "warmup_active": true,
  "warmup_running": true,
  "warmup_done": false,
  "info": "Warmup requests keep the model container warm..."
}
```

### View Logs

The server logs warmup activity:
```
🔥 Model warmup task started (interval: 120s)
🔥 Sending warmup request to keep model warm...
✅ Warmup complete in 850ms (model should stay warm for ~5-10 min)
```

### Health Check Includes Warmup

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "provider": "bedrock",
  "model": "us.anthropic.claude-haiku-4-5-20250910-v1:0",
  "warmup_active": true
}
```

## Cost Impact

### AWS Bedrock Pricing
- Each warmup request uses ~10 tokens
- At 120s interval: ~30 requests/hour = ~300 tokens/hour
- At $0.00025/1K input tokens (Haiku): ~$0.000075/hour
- **Daily cost:** ~$0.0018/day (~5 cents/month)

**Conclusion:** Warmup is essentially free compared to the latency improvement.

## Troubleshooting

### Warmup Requests Failing

Check logs for:
```
⚠️ Warmup request failed: [error message]
```

**Common causes:**
- AWS credentials expired
- Region/model not available
- Network issues

The warmup task continues running even if some requests fail.

### Model Still Cold

If TTFT is still high despite warmup:
1. **Check warmup interval** - May be too long (>5 min)
2. **Verify warmup is active** - Check `/v1/warmup/status`
3. **Check AWS region** - Try region closer to you
4. **Consider Provisioned Throughput** - For guaranteed low latency

### High Memory Usage

If warmup causes issues:
- Increase warmup interval to 300s (5 min)
- Or disable warmup entirely

## Production Recommendations

### For Production Apps

1. **Keep warmup enabled** with 120-180s interval
2. **Monitor TTFT** in your application logs
3. **Set alerts** if warmup task fails repeatedly
4. **Consider Provisioned Throughput** if you need guaranteed <500ms TTFT

### For Development

- Warmup is safe to use in development
- May want to disable to save API calls
- Set interval to 300s if only testing occasionally

## Advanced: Multiple Instances

If running multiple FastAPI instances (load balanced):

### Option 1: All Instances Warmup
- Each instance runs its own warmup
- More AWS costs but better coverage
- Recommended for production

### Option 2: Dedicated Warmup Instance
- Run one instance just for warmup
- Other instances handle real traffic
- More complex but most cost-effective

## Metrics to Track

Monitor these to evaluate warmup effectiveness:

```python
# Add to your application logging
import time

request_start = time.time()
# ... make request ...
first_chunk_time = time.time()
ttft = (first_chunk_time - request_start) * 1000

# Log this metric
print(f"TTFT: {ttft:.0f}ms")
```

**Target metrics:**
- **With warmup:** 500-1500ms
- **Without warmup:** 2000-5000ms

If warmup is working, you should see consistent low TTFT during business hours.
