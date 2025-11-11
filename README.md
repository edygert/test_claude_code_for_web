# AI Streaming Chat with Chinese Speech Recognition & TTS

An AI-powered chat application with Traditional Chinese (zh-TW) speech recognition and text-to-speech capabilities. Built with FastAPI backend and React frontend.

## Features

### 🎤 Speech Recognition (Speech-to-Text)
- **Language:** Traditional Chinese (zh-TW)
- **Continuous recognition** with real-time interim results
- **Auto-pause detection:** Automatically transfers text after 1 second of silence
- **Visual feedback:** Input field highlights during recording
- **High accuracy:** Uses browser's native Web Speech Recognition API

### 🔊 Text-to-Speech (TTS)
- **Language:** Traditional Chinese (zh-TW)
- **Toggle button:** Easy enable/disable control
- **Smart voice selection:** Automatically finds best Chinese voice on your system
- **Reliable playback:** Handles long responses by splitting into chunks
- **Stop control:** Interrupt speech at any time
- **Auto-stop:** Cancels previous speech when sending new message

### 💬 AI Chat with Streaming
- **Real-time streaming:** See responses appear word-by-word
- **AWS Bedrock integration:** Powered by advanced language models
- **Low latency:** Optimized for fast response display
- **Performance metrics:** Logs Time To First Chunk (TTFC)

## Prerequisites

- Python 3.8+
- Modern web browser with Web Speech API support:
  - Google Chrome (recommended)
  - Microsoft Edge
  - Safari (macOS)
- AWS account with Bedrock access (if using AWS Bedrock provider)
- Microphone for speech recognition
- System with Chinese TTS voices installed (usually available on macOS, Windows 10+, Linux with language packs)

## Installation

### 1. Clone the Repository

```bash
cd /home/user/test_claude_code_for_web
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `boto3` - AWS SDK (if using Bedrock)
- `python-dotenv` - Environment variable management

### 3. Configure Environment (if using AWS Bedrock)

Create a `.env` file or set environment variables for AWS credentials:

```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 4. Install Chinese TTS Voices (if needed)

**macOS:** Chinese voices are pre-installed

**Windows 10/11:**
1. Settings → Time & Language → Language
2. Add Chinese (Traditional, Taiwan)
3. Download language pack

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install speech-dispatcher espeak-ng
sudo apt-get install espeak-ng-data
```

## Usage

### 1. Start the Backend Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

### 2. Open the Frontend

Open `streaming-chat.html` in your web browser:

```bash
# macOS
open streaming-chat.html

# Linux
xdg-open streaming-chat.html

# Windows
start streaming-chat.html
```

Or simply drag `streaming-chat.html` into your browser window.

### 3. Use Speech Recognition

1. Click the **🎤 Record** button
2. Speak in Traditional Chinese
3. Watch your words appear in the preview box
4. Pause for 1 second to auto-transfer text to input field
5. Click **⏹ Stop** to manually stop recording

### 4. Enable Text-to-Speech

1. Click the **🔇 TTS Off** button to toggle to **🔊 TTS On** (button turns blue)
2. Send a message to the AI
3. When the response completes, it will be spoken aloud
4. Click **⏹ Stop Speaking** to interrupt playback if needed

### 5. Chat with AI

1. Type or use speech recognition to input your message
2. Click **Send** or press Enter
3. Watch the response stream in word-by-word
4. If TTS is enabled, listen to the response

## API Endpoints

### Health Check
```bash
GET http://localhost:8000/
GET http://localhost:8000/health
```

### Chat Completion (Streaming)
```bash
POST http://localhost:8000/v1/chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

Response format: Server-Sent Events (SSE)

### Configure AI Provider
```bash
POST http://localhost:8000/v1/provider/configure
Content-Type: application/json

{
  "provider": "bedrock",
  "config": {
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "region": "us-east-1"
  }
}
```

### List Available Providers
```bash
GET http://localhost:8000/v1/providers
```

## Configuration

### Backend Configuration

Edit `main.py` to customize:
- AI provider (Bedrock, OpenAI, etc.)
- Model selection
- Temperature and other generation parameters
- CORS settings
- Port number

### Frontend Configuration

Edit `streaming-chat.html` to customize:
- Speech recognition language (`recognitionInstance.lang = 'zh-TW'`)
- TTS language (`utterance.lang = 'zh-TW'`)
- TTS speech rate, pitch, volume
- Chunk size for TTS (default: 200 characters)
- Auto-pause timeout (default: 1000ms)
- Backend API URL (default: `http://localhost:8000`)

## Troubleshooting

### Speech Recognition Not Working

**Issue:** Browser doesn't recognize speech

**Solutions:**
1. Grant microphone permissions when prompted
2. Use Chrome or Edge (best support)
3. Check microphone is working in system settings
4. Try speaking more clearly or closer to microphone
5. Check browser console for error messages

---

**Issue:** Text appears repeated "我我是我是一..."

**Solution:** This bug was fixed. Update to latest version from branch `claude/chinese-dog-recognition-011CUpmETreATbPZnSRYHRSL`

---

### Text-to-Speech Not Working

**Issue:** No sound when response completes

**Solutions:**
1. **Check TTS is enabled:** Click the TTS toggle button until it shows "🔊 TTS On" (blue background)
2. Verify system volume is not muted
3. Check browser console for errors
4. Verify Chinese TTS voices are installed (see Installation section)
5. Try shorter test message first

---

**Issue:** "Speech ended" logged but no sound

**Solution:** This was fixed with timing and chunking improvements. Update to latest version.

---

### Streaming Display Issues

**Issue:** Response appears all at once instead of word-by-word

**Solution:** This bug was fixed. Update to latest version. The fix involves yielding control to browser between chunks.

---

**Issue:** Slow first response (~4 seconds)

**Explanation:** This is normal for AWS Bedrock On-Demand. The Time To First Chunk (TTFC) is typically 4 seconds due to model processing time. Subsequent chunks are fast (~50-200ms).

**Not a bug:** This is inherent to the Bedrock On-Demand architecture. To reduce latency, you would need Provisioned Throughput (expensive).

---

### Backend Issues

**Issue:** Server won't start

**Solutions:**
1. Check Python version: `python --version` (need 3.8+)
2. Install dependencies: `pip install -r requirements.txt`
3. Check port 8000 is not in use: `lsof -i :8000`
4. Check AWS credentials if using Bedrock

---

**Issue:** AWS Bedrock errors

**Solutions:**
1. Verify AWS credentials are set
2. Check Bedrock is available in your region
3. Verify model ID is correct
4. Check you have Bedrock API access enabled

---

### Browser Compatibility

**Supported Browsers:**
- ✅ Google Chrome (recommended)
- ✅ Microsoft Edge
- ✅ Safari (macOS)
- ❌ Firefox (limited Web Speech API support)

---

## Performance

### Metrics

- **Speech Recognition Latency:** ~50-200ms
- **TTS Playback Start:** ~100ms after response completes
- **Time To First Chunk (TTFC):** ~4 seconds (AWS Bedrock On-Demand)
- **Subsequent Chunks:** ~50-200ms between chunks
- **Streaming Display Update:** 10ms per chunk

### Optimization Tips

1. **Use Chrome** for best Web Speech API support
2. **Enable TTS only when needed** to save resources
3. **Shorter messages** have lower latency
4. **Stable internet connection** important for Bedrock streaming

---

## Architecture

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- Uvicorn (ASGI server)
- AWS Bedrock (AI provider)

**Frontend:**
- React 18 (UI framework)
- Web Speech Recognition API (speech-to-text)
- Web Speech Synthesis API (text-to-speech)
- Fetch API (streaming responses)

### Data Flow

```
User speaks → Browser Speech Recognition (zh-TW) → Text in input field
                                                      ↓
User submits → FastAPI backend → AWS Bedrock → Streaming SSE response
                                                      ↓
Frontend receives chunks → Display word-by-word → Accumulate full response
                                                      ↓
Response complete → TTS speaks response (if enabled)
```

---

## Development

### Project Structure

```
.
├── main.py                          # FastAPI backend server
├── streaming-chat.html              # React frontend application
├── requirements.txt                 # Python dependencies
├── bedrock_timing_diagnostic.py     # Bedrock latency diagnostic tool
├── IMPLEMENTATION_PROMPT_OPENCC.md  # OpenCC conversion implementation guide
├── PROJECT_NOTES.md                 # Technical notes and design decisions
└── README.md                        # This file
```

### Key Files

- **`main.py`**: Backend server with streaming chat endpoint
- **`streaming-chat.html`**: Complete frontend application (self-contained HTML file)
- **`PROJECT_NOTES.md`**: Detailed technical documentation, bug fixes, design decisions

### Git Workflow

Current development branch:
```
claude/chinese-dog-recognition-011CUpmETreATbPZnSRYHRSL
```

See `PROJECT_NOTES.md` for detailed git workflow and branch naming conventions.

---

## Planned Features

### 🔤 OpenCC Character Conversion (High Priority)

**Goal:** Convert Simplified Chinese characters to Traditional Chinese

**Why:** Browser speech recognition sometimes outputs Simplified characters even when set to zh-TW

**Implementation:** See detailed guide in `IMPLEMENTATION_PROMPT_OPENCC.md`

**Endpoints to add:**
- `POST /v1/convert/traditional` - Server-side conversion using OpenCC library

---

### 💾 Persist TTS Preference

Save TTS toggle state in browser's localStorage so it persists across page refreshes.

---

### 🎛️ Voice Settings UI

Allow users to:
- Select specific TTS voice from dropdown
- Adjust speech rate, pitch, volume
- Preview voices before selecting

---

### 📊 Usage Statistics

Track and display:
- Number of messages sent
- Total speech recognition time
- Total TTS playback time
- Average response times

---

## Testing

### Manual Test Cases

**Test Case 1: Basic Speech Recognition**
1. Click Record button
2. Say: "我是一隻狗" (I am a dog)
3. Expected: Text appears without repetition
4. Expected: Correct Traditional Chinese characters

**Test Case 2: Auto-Pause Transfer**
1. Click Record button
2. Say: "你好"
3. Wait 1 second without speaking
4. Expected: Text automatically transfers to input field

**Test Case 3: Text-to-Speech**
1. Enable TTS toggle (blue)
2. Type: "你好嗎" and send
3. Expected: Response is spoken in Chinese after streaming completes
4. Expected: Stop Speaking button appears during playback

**Test Case 4: Streaming Display**
1. Send a message requesting a long response
2. Expected: Response appears word-by-word, not all at once
3. Expected: Console shows TTFC timing

---

## Contributing

### Before Making Changes

1. Read `PROJECT_NOTES.md` for technical context
2. Check existing issues and planned features
3. Test your changes thoroughly
4. Follow existing code style

### Commit Message Format

Use imperative mood:
- ✅ "Add TTS feature"
- ✅ "Fix speech recognition repetition bug"
- ❌ "Added TTS feature"
- ❌ "Fixed bug"

---

## License

[Add your license here]

---

## Support

For issues or questions:
- Check `PROJECT_NOTES.md` for detailed technical information
- Check browser console for error messages
- Verify all prerequisites are installed
- Test with simple cases first

---

## Credits

Built with:
- FastAPI by Sebastián Ramírez
- React by Meta
- AWS Bedrock by Amazon Web Services
- Web Speech API by W3C

---

## Changelog

### Latest (Branch: claude/chinese-dog-recognition-011CUpmETreATbPZnSRYHRSL)

**Added:**
- ✨ Text-to-Speech (TTS) with zh-TW voice support
- ✨ TTS toggle button and stop controls
- ✨ Smart voice selection with fallback chain
- ✨ Text chunking for reliable long-response playback
- ✨ Auto-pause detection for speech recognition (1 second)
- ✨ TTFC timing measurements

**Fixed:**
- 🐛 Speech recognition text repetition bug
- 🐛 Streaming display showing all at once instead of incremental
- 🐛 TTS timing issues with cancel/speak race condition
- 🐛 TTS failing on long text (added chunking)

**Improved:**
- ⚡ Streaming display performance with 10ms yielding
- ⚡ TTS reliability with 100ms delay after cancel
- 📝 Comprehensive documentation (PROJECT_NOTES.md, README.md)

---

Last Updated: 2025-11-11
Version: In Development
Branch: claude/chinese-dog-recognition-011CUpmETreATbPZnSRYHRSL
