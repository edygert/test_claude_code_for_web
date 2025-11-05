# Implementation Prompt: Server-Side OpenCC Conversion

## Task
Add server-side Simplified to Traditional Chinese character conversion using OpenCC

## Context
- We have a FastAPI backend server (main.py) handling AI chat requests
- Frontend uses browser's Speech Recognition API with lang='zh-TW'
- Sometimes the browser outputs Simplified Chinese characters instead of Traditional
- Need to add an API endpoint that converts Simplified → Traditional using OpenCC library

---

## Requirements

### 1. Install Dependencies

Add opencc-python-reimplemented to your Python environment:

```bash
pip install opencc-python-reimplemented
```

This library provides industry-standard Chinese character conversion.

---

### 2. Create New File: `conversion_service.py`

**Location:** `/home/user/test_claude_code_for_web/conversion_service.py`

**Content should include:**
- Import OpenCC library
- Create a singleton converter instance (from='cn', to='tw' for Taiwan Traditional)
- Define a function: `convert_to_traditional(text: str) -> str`
- Add error handling for conversion failures
- Add optional caching for frequently converted phrases (use functools.lru_cache)

**Example structure:**
```python
from opencc import OpenCC
from functools import lru_cache

# Initialize converter once (expensive operation)
_converter = OpenCC('s2tw')  # Simplified to Taiwan Traditional

@lru_cache(maxsize=1000)
def convert_to_traditional(text: str) -> str:
    """Convert Simplified Chinese to Traditional Chinese (Taiwan standard)."""
    # Implementation here
    pass
```

---

### 3. Add New Endpoint to `main.py`

**Location:** After the existing `/v1/chat/completions` endpoint

**Endpoint specification:**
- Method: `POST`
- Path: `/v1/convert/traditional`
- Request body: `{ "text": "simplified chinese text" }`
- Response: `{ "text": "traditional chinese text", "original": "original text" }`
- Handle empty strings gracefully
- Return 400 if text is missing
- Return 500 if conversion fails with error details

**Example structure:**
```python
from pydantic import BaseModel
from conversion_service import convert_to_traditional

class ConversionRequest(BaseModel):
    text: str

class ConversionResponse(BaseModel):
    text: str
    original: str

@app.post("/v1/convert/traditional")
async def convert_to_traditional_chinese(request: ConversionRequest):
    # Implementation here
    pass
```

---

### 4. Update Frontend: `streaming-chat.html`

**Modify the speech recognition onresult handler**

**Current flow:**
```
Speech → finalTranscriptRef.current += transcript
```

**New flow:**
```
Speech → Send to /v1/convert/traditional → Use converted result
```

**Implementation points:**
- After getting final transcript, call the conversion endpoint
- Use `fetch()` to POST text to `/v1/convert/traditional`
- Replace the transcript with converted result
- Add loading state or keep original if conversion fails
- Only convert final transcripts (not interim for performance)

**Location to modify:** Around line 101-103 where `finalTranscriptRef.current` is updated

**Example flow:**
```javascript
if (event.results[i].isFinal) {
    const transcript = event.results[i][0].transcript;

    // Call conversion API
    try {
        const response = await fetch('http://localhost:8000/v1/convert/traditional', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: transcript })
        });

        const result = await response.json();
        finalTranscriptRef.current += result.text;
    } catch (error) {
        // Fallback to original if conversion fails
        console.error('Conversion failed:', error);
        finalTranscriptRef.current += transcript;
    }
}
```

---

### 5. Error Handling

- If conversion endpoint fails, fall back to original text
- Log conversion errors to console for debugging
- Add timeout (5 seconds max) for conversion request
- Show user-friendly error if conversion service is down

---

### 6. Performance Optimization

- Use `lru_cache` in `conversion_service.py` for repeated phrases
- Consider batching if multiple transcripts come quickly
- Conversion should complete in <50ms for typical sentences

---

### 7. Testing Checklist

- [ ] Test with pure Simplified text (should convert)
- [ ] Test with pure Traditional text (should pass through unchanged)
- [ ] Test with mixed text (should convert Simplified parts only)
- [ ] Test with empty string (should handle gracefully)
- [ ] Test with very long text (>1000 characters)
- [ ] Test server restart (cache should rebuild)
- [ ] Verify common conversions: 只→隻, 个→個, 说→說

---

### 8. OpenCC Conversion Standards

**Available OpenCC conversion types:**
- `s2t`: Simplified to Traditional
- `s2tw`: Simplified to Taiwan Traditional **(RECOMMENDED)**
- `s2twp`: Simplified to Taiwan Traditional with phrases
- `s2hk`: Simplified to Hong Kong Traditional

**Use `s2tw` for Taiwan users** (most accurate for zh-TW)

---

### 9. Optional Enhancements (Not Required)

- Add `GET /v1/convert/status` endpoint to check if service is available
- Add conversion statistics (how many chars converted)
- Add batch endpoint: `POST /v1/convert/traditional/batch`
- Add caching with Redis for production

---

### 10. Integration Points

**Backend:**
- `main.py` (add endpoint)
- `conversion_service.py` (new file)

**Frontend:**
- `streaming-chat.html` (modify onresult handler)

**Dependencies:**
- `requirements.txt` (add opencc-python-reimplemented)

---

## Validation

After implementation, test by speaking: **"我是一只狗"**

**Expected output:** "我是一隻狗" (只 should convert to 隻)

**Verify:**
- Browser console shows API is called
- Check server logs for conversion activity
- No errors in console or server logs

---

## Expected File Changes

1. **NEW FILE:** `conversion_service.py` (~30-40 lines)
2. **MODIFIED:** `main.py` (~30-40 lines added for endpoint)
3. **MODIFIED:** `streaming-chat.html` (~20-30 lines modified in onresult handler)
4. **MODIFIED:** `requirements.txt` (add 1 line)

---

## Estimated Time
**30-45 minutes**

---

## Success Criteria

- ✅ Conversion endpoint returns correct Traditional characters
- ✅ Speech recognition automatically converts Simplified → Traditional
- ✅ Fallback to original text if conversion fails
- ✅ No performance degradation in speech recognition
- ✅ Server logs show successful conversions

---

## Example Test Cases

### Test Case 1: Common Measure Words
**Input:** "我有一只狗和两个猫"
**Expected:** "我有一隻狗和兩個貓"

### Test Case 2: Common Verbs
**Input:** "我听不懂你说的话"
**Expected:** "我聽不懂你說的話"

### Test Case 3: Already Traditional
**Input:** "我是一隻貓"
**Expected:** "我是一隻貓" (unchanged)

### Test Case 4: Mixed Content
**Input:** "今天天气很好" (Simplified)
**Expected:** "今天天氣很好" (Traditional)

---

## Resources

- **OpenCC Documentation:** https://github.com/BYVoid/OpenCC
- **opencc-python-reimplemented:** https://pypi.org/project/opencc-python-reimplemented/
- **OpenCC Conversion Standards:** https://github.com/BYVoid/OpenCC/wiki/Conversion-標準

---

## Notes

- OpenCC is the industry-standard library used by major Chinese text applications
- It handles context-aware conversions (e.g., 发 → 髮 vs 發 depending on context)
- Covers all Unicode CJK character mappings
- Conversion is deterministic and fast (<50ms for typical sentences)
- The `s2tw` configuration follows Taiwan Ministry of Education standards

---

## Troubleshooting

### Issue: "Module 'opencc' not found"
**Solution:** Run `pip install opencc-python-reimplemented`

### Issue: Conversion is slow (>100ms)
**Solution:** Ensure converter is initialized once as singleton, not per request

### Issue: Some characters not converting
**Solution:** Check OpenCC version, ensure using 's2tw' not 's2t'

### Issue: Frontend timeout errors
**Solution:** Increase fetch timeout, add better error handling

---

## Maintenance

- Update OpenCC library periodically: `pip install --upgrade opencc-python-reimplemented`
- Monitor conversion success rate in logs
- Add more test cases as edge cases are discovered
- Consider adding conversion metrics dashboard for production
