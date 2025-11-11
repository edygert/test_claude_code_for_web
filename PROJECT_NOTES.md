# Project Notes: Chinese Speech Recognition Chat with TTS

## Project Overview
AI-powered chat application with Chinese (Traditional, zh-TW) speech recognition and text-to-speech capabilities. Built with FastAPI backend streaming to a React-based frontend.

## Current Branch
`claude/chinese-dog-recognition-011CUpmETreATbPZnSRYHRSL`

---

## Architecture

### Backend (Python/FastAPI)
- **File:** `main.py`
- **Framework:** FastAPI with async/await
- **AI Provider:** AWS Bedrock (configurable)
- **Streaming:** Server-Sent Events (SSE) format
- **Endpoints:**
  - `GET /` - Health check
  - `GET /health` - Health status
  - `POST /v1/chat/completions` - AI chat with streaming
  - `POST /v1/provider/configure` - Configure AI provider
  - `GET /v1/providers` - List available providers

### Frontend (HTML/React)
- **File:** `streaming-chat.html`
- **Framework:** React 18 (via CDN)
- **APIs Used:**
  - Web Speech Recognition API (speech-to-text)
  - Web Speech Synthesis API (text-to-speech)
  - Fetch API (streaming responses)

---

## Implemented Features

### 1. Speech Recognition (Speech-to-Text)
**Language:** Traditional Chinese (zh-TW)

**Key Implementation Details:**
- **Continuous recognition** with interim results
- **Repetition bug fix:** Critical fix - only process NEW results starting from `event.resultIndex` to avoid text duplication
  - Bug was: Processing all results from index 0 on every event
  - Fix: `for (let i = event.resultIndex; i < event.results.length; i++)`
- **State management:** Uses `finalTranscriptRef` (useRef) to accumulate final transcripts
- **Auto-pause detection:** Transfers text to input field after 1 second of silence
  - Implemented with `pauseTimeoutRef` and setTimeout
  - Timeout resets on each new speech event
- **Visual feedback:** Input field highlights during recording (yellow background)

**Location in code:** `streaming-chat.html` lines 80-156

### 2. Text-to-Speech (TTS)
**Language:** Traditional Chinese (zh-TW)

**Key Implementation Details:**
- **Toggle button:** Enable/disable TTS (🔊 TTS On / 🔇 TTS Off)
- **Voice selection fallback chain:**
  1. zh-TW (preferred)
  2. zh-CN (fallback)
  3. Any zh-* (fallback)
  4. System default (last resort)
- **Text chunking:** Splits responses into 200-character chunks
  - Reason: Some speech engines have length limits and fail silently on long text
  - Chunks are spoken sequentially
- **Timing fix:** 100ms delay after `cancel()` before starting new speech
  - Required for proper cleanup of speech queue
- **Stop Speaking button:** Appears while speech is active (red button)
- **Auto-stop:** Cancels ongoing speech when submitting new message
- **State management:**
  - `ttsEnabled` - Toggle state
  - `isSpeaking` - Currently speaking state

**Important TTS Debugging Note:**
If TTS doesn't work, check console for "TTS skipped - enabled: false". User must click the TTS toggle button to enable it.

**Location in code:** `streaming-chat.html` lines 193-247

### 3. AI Response Streaming
**Format:** Server-Sent Events (SSE)

**Key Implementation Details:**
- **Incremental display:** Word-by-word streaming (not all at once)
- **React 18 batching issue fix:**
  - Problem: React 18 automatic batching prevented incremental renders
  - Solution: `await new Promise(resolve => setTimeout(resolve, 10))` to yield control to browser
  - Also uses `responseVersion` state with changing key to force re-renders
- **TTFC timing:** Measures Time To First Chunk
  - Logs: "TTFC: X ms | Total: Y ms"
  - AWS Bedrock On-Demand typically shows ~4 second TTFC (normal for model processing)
- **TTS integration:** Accumulates full response text during streaming, then speaks it when `[DONE]` received

**Location in code:** `streaming-chat.html` lines 205-318

---

## Critical Bugs Fixed

### Bug 1: Speech Recognition Text Repetition
**Symptom:** "我我是我是一我是一只我是一只狗"

**Root Cause:** Loop was processing ALL results from index 0 on every `onresult` event, repeatedly appending to state.

**Fix:** Changed loop to `for (let i = event.resultIndex; i < event.results.length; i++)` to only process NEW results.

**Commit:** Early in the conversation history

---

### Bug 2: Streaming Display Not Incremental
**Symptom:** AI responses appeared all at once instead of word-by-word.

**Root Cause:** JavaScript thread was blocked by `while(true)` loop, browser couldn't paint between state updates.

**Fix:** Added `await new Promise(resolve => setTimeout(resolve, 10))` to yield control to browser paint cycle.

**Commit:** Multiple attempts - final solution involved setTimeout yielding

---

### Bug 3: TTS Not Playing Sound
**Symptom:** "Speech ended" logged but not "Speech started", no audio output.

**Root Causes:**
1. User hadn't enabled TTS toggle button
2. Calling `speak()` immediately after `cancel()` caused race condition
3. Long text exceeded speech engine limits

**Fixes:**
1. Added debug logging to show TTS state
2. Added 100ms delay after `cancel()`
3. Split text into 200-char chunks with sequential playback

**Commits:** `114a203`, `94c5a6f`, `c02064a`

---

## Design Decisions

### Why Traditional Chinese (zh-TW) not Simplified (zh-CN)?
**Decision:** User explicitly required Traditional Chinese for Taiwan usage.

**Impact:** Browser speech recognition sometimes outputs Simplified characters even when set to zh-TW. This is why OpenCC conversion feature is planned.

---

### Why Not Use Warmup for Bedrock?
**Decision:** Removed warmup background task after testing showed no effect.

**Reason:** AWS Bedrock On-Demand uses multi-tenant containers with no container affinity. Warmup requests hit different containers than user requests, so they don't help with cold starts.

**Alternative:** Would need Provisioned Throughput (~$360-720/month) for guaranteed low latency.

**Commits:** Warmup removed in conversation after user testing

---

### Why Text Chunking for TTS?
**Decision:** Split responses into 200-character chunks instead of speaking entire response at once.

**Reason:** Some browser speech engines have undocumented length limits and fail silently on long text. Chunking ensures reliability across browsers.

**Performance:** No noticeable delay between chunks.

---

### Why 10ms Yield in Streaming?
**Decision:** Add `setTimeout(resolve, 10)` delay between state updates during streaming.

**Reason:** React 18 automatic batching and JavaScript event loop blocking prevented incremental rendering. Yielding control allows browser to paint between updates.

**Alternatives Tried:**
1. `flushSync()` from ReactDOM - didn't work
2. `responseVersion` state with changing key - not sufficient alone
3. Final solution: Both version-based re-renders + setTimeout yielding

---

## Known Issues

### 1. TTFC (Time To First Chunk) is ~4 seconds
**Status:** Expected behavior, not a bug

**Reason:** AWS Bedrock On-Demand model processing time. First chunk is slow, subsequent chunks are fast.

**Not fixable without:** Provisioned Throughput (expensive)

---

### 2. Speech Recognition Sometimes Outputs Simplified Characters
**Status:** Planned fix with OpenCC

**Reason:** Browser's zh-TW speech recognition isn't perfect and sometimes returns Simplified Chinese characters.

**Planned Solution:** Server-side OpenCC conversion (see `IMPLEMENTATION_PROMPT_OPENCC.md`)

---

### 3. TTS State Doesn't Persist
**Status:** By design

**Reason:** TTS toggle state resets on page refresh. User must click toggle button each session.

**Possible Enhancement:** Use localStorage to persist TTS preference

---

## Performance Notes

### Bedrock On-Demand Architecture
- **Multi-tenant containers** shared across all AWS customers
- **No container affinity** - requests hit different containers
- **~4 second TTFC** is normal for model processing
- **Subsequent chunks** are very fast (~50-200ms between chunks)
- **Warmup doesn't help** - warms containers used by other customers

### Browser Performance
- **Speech Recognition:** ~50-200ms latency for recognition results
- **TTS:** Immediate playback start after 100ms delay
- **Streaming Display:** 10ms yield between chunks allows smooth rendering

---

## File Structure

```
/home/user/test_claude_code_for_web/
├── main.py                              # FastAPI backend server
├── streaming-chat.html                  # React frontend with speech features
├── requirements.txt                     # Python dependencies
├── bedrock_timing_diagnostic.py         # Diagnostic tool for Bedrock latency
├── IMPLEMENTATION_PROMPT_OPENCC.md      # Guide for OpenCC conversion feature
├── PROJECT_NOTES.md                     # This file
└── README.md                            # User-facing documentation
```

---

## Testing Notes

### Test Case: "我是一只狗" (I am a dog)
**Expected Recognition:** "我是一隻狗" (with correct measure word 隻)

**Current Behavior:**
- Recognition works correctly without repetition
- Correct character for dog (狗)
- Measure word may be Simplified (只) instead of Traditional (隻)

**After OpenCC Implementation:** Should always show Traditional characters

---

## Git Workflow

### Branch Naming Convention
`claude/[descriptive-name]-[session-id]`

Example: `claude/chinese-dog-recognition-011CUpmETreATbPZnSRYHRSL`

### Commit Message Style
- Concise imperative mood ("Add feature" not "Added feature")
- Detailed body explaining what and why
- Example: "Improve TTS with voice detection and fallback logic"

### Push Requirements
- Always use: `git push -u origin <branch-name>`
- Branch must start with `claude/` and end with matching session ID
- Retry up to 4 times with exponential backoff on network errors

---

## Future Enhancements (Not Yet Implemented)

### 1. OpenCC Conversion (Highest Priority)
See `IMPLEMENTATION_PROMPT_OPENCC.md` for detailed implementation guide.

**Endpoints to add:**
- `POST /v1/convert/traditional` - Convert Simplified to Traditional

**Files to create:**
- `conversion_service.py` - OpenCC wrapper service

**Files to modify:**
- `main.py` - Add conversion endpoint
- `streaming-chat.html` - Call conversion API on final transcripts
- `requirements.txt` - Add `opencc-python-reimplemented`

---

### 2. Persist TTS Preference
Use `localStorage` to remember TTS toggle state across page refreshes.

---

### 3. Voice Settings UI
Allow users to:
- Select specific voice from dropdown
- Adjust speech rate, pitch, volume
- Preview voices

---

### 4. Batch Transcript Conversion
If multiple final transcripts arrive quickly, batch them into single conversion request for better performance.

---

## Debugging Tips

### Speech Recognition Issues
1. Check browser console for "Speech recognition error: [error]"
2. Verify microphone permissions granted
3. Test with simple phrases first
4. Look for repetition - if present, check that `event.resultIndex` is being used

### TTS Issues
1. Check if TTS is enabled: Look for "TTS skipped - enabled: false" in console
2. Verify browser has Chinese voices: Check browser's speech settings
3. Test with short text first
4. Check for "Speech started" log - if missing, speech engine failed

### Streaming Issues
1. Check TTFC timing in console
2. Verify response updates incrementally (not all at once)
3. Look for chunk-related errors in backend logs
4. Monitor network tab for SSE events

### Backend Issues
1. Check server logs for errors
2. Verify Bedrock credentials configured
3. Test `/health` endpoint
4. Monitor streaming response format

---

## Dependencies

### Backend
```
fastapi
uvicorn
boto3  # AWS Bedrock
python-dotenv
```

### Frontend
- React 18 (CDN)
- Babel standalone (CDN)
- Web Speech API (browser native)

### Planned
- `opencc-python-reimplemented` (for character conversion)

---

## Environment Variables
Check `main.py` for AWS Bedrock configuration requirements.

---

## Useful Commands

### Start Backend
```bash
python main.py
```

### Test Backend
```bash
curl http://localhost:8000/health
```

### Docker Build (if needed)
User mentioned Docker setup - check for Dockerfile.

---

## References

- **OpenCC Documentation:** https://github.com/BYVoid/OpenCC
- **Web Speech API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
- **FastAPI Streaming:** https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- **AWS Bedrock:** https://docs.aws.amazon.com/bedrock/

---

## Maintenance Notes

### When Adding New Features
1. Update this PROJECT_NOTES.md
2. Update IMPLEMENTATION_PROMPT_OPENCC.md if relevant
3. Add comments in code for complex logic
4. Write clear commit messages

### When Fixing Bugs
1. Document root cause here
2. Document fix approach
3. Add to "Critical Bugs Fixed" section
4. Consider adding test case

---

## Session Continuity

**For Claude Code CLI:**
When starting a new CLI session, provide this context:
```
"Read PROJECT_NOTES.md and README.md to understand the project state.
This is a Chinese speech recognition chat app with TTS. [Your specific task]"
```

**For Claude Code for Web:**
Reference this file when context is lost or session continues.

---

Last Updated: 2025-11-11
Branch: claude/chinese-dog-recognition-011CUpmETreATbPZnSRYHRSL
