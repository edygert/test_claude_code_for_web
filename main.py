"""
FastAPI application for AI streaming service with model warmup.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from ai_streaming import StreamingRequest, ProviderConfig, Message
from ai_streaming.factory import ProviderFactory
from ai_streaming.providers.base import BaseAIProvider


# Global provider instance and warmup task
_provider: Optional[BaseAIProvider] = None
_warmup_task: Optional[asyncio.Task] = None


async def warmup_model():
    """
    Background task to keep the model warm by sending periodic requests.
    This reduces Time To First Token (TTFT) by preventing cold starts.
    """
    # Wait a bit before starting warmup to let the app initialize
    await asyncio.sleep(30)

    warmup_interval = 120  # Send warmup request every 2 minutes

    print(f"🔥 Model warmup task started (interval: {warmup_interval}s)")

    while True:
        try:
            await asyncio.sleep(warmup_interval)

            if _provider is None:
                print("⚠️ Warmup: Provider not initialized, skipping")
                continue

            # Create a minimal warmup request
            warmup_request = StreamingRequest(
                messages=[Message(role="user", content="Hi")],
                max_tokens=10,
                temperature=0.7
            )

            print("🔥 Sending warmup request to keep model warm...")
            warmup_start = asyncio.get_event_loop().time()

            # Consume just the first chunk to trigger model loading
            chunk_count = 0
            async for chunk in _provider.stream_completion(warmup_request):
                chunk_count += 1
                if chunk_count >= 2:  # Get first content chunk
                    break

            warmup_time = (asyncio.get_event_loop().time() - warmup_start) * 1000
            print(f"✅ Warmup complete in {warmup_time:.0f}ms (model should stay warm for ~5-10 min)")

        except asyncio.CancelledError:
            print("🛑 Model warmup task cancelled")
            break
        except Exception as e:
            print(f"⚠️ Warmup request failed: {str(e)}")
            # Continue anyway - don't let warmup failures break the task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global _provider, _warmup_task

    # Initialize default provider (Bedrock)
    provider_name = os.getenv("AI_PROVIDER", "bedrock")
    model_id = os.getenv("AI_MODEL_ID", "us.anthropic.claude-haiku-4-5-20250910-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")
    api_key = os.getenv("AI_API_KEY")

    config = ProviderConfig(
        provider_name=provider_name,
        model_id=model_id,
        region=region,
        api_key=api_key
    )

    _provider = ProviderFactory.create_provider(config)
    print(f"✅ Provider initialized: {provider_name} ({model_id})")

    # Start warmup background task
    _warmup_task = asyncio.create_task(warmup_model())

    yield

    # Cleanup
    if _warmup_task:
        _warmup_task.cancel()
        try:
            await _warmup_task
        except asyncio.CancelledError:
            pass

    _provider = None
    print("🛑 Application shutdown complete")


app = FastAPI(
    title="AI Streaming API",
    description="FastAPI service for streaming AI completions from multiple providers",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_provider() -> BaseAIProvider:
    """Dependency to get the current provider."""
    if _provider is None:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    return _provider


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Streaming API",
        "version": "0.1.0",
        "provider": _provider.config.provider_name if _provider else "none",
        "warmup_active": _warmup_task is not None and not _warmup_task.done()
    }


@app.get("/health")
async def health_check(provider: BaseAIProvider = Depends(get_provider)):
    """Health check endpoint."""
    is_healthy = await provider.validate_connection()

    if not is_healthy:
        raise HTTPException(status_code=503, detail="Provider connection failed")

    return {
        "status": "healthy",
        "provider": provider.config.provider_name,
        "model": provider.config.model_id,
        "warmup_active": _warmup_task is not None and not _warmup_task.done()
    }


@app.post("/v1/chat/completions")
async def create_completion(
    request: StreamingRequest,
    provider: BaseAIProvider = Depends(get_provider)
):
    """
    Create a streaming chat completion.

    Args:
        request: Streaming request with messages and parameters

    Returns:
        Streaming response with AI-generated content
    """
    async def generate():
        """Generator function for streaming response."""
        try:
            async for chunk in provider.stream_completion(request):
                # Send as server-sent events
                if chunk.content:
                    yield f"data: {chunk.model_dump_json()}\n\n"

                if chunk.is_final:
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    yield "data: [DONE]\n\n"
                    break

        except Exception as e:
            error_chunk = {
                "error": str(e),
                "is_final": True
            }
            yield f"data: {error_chunk}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/v1/provider/configure")
async def configure_provider(config: ProviderConfig):
    """
    Reconfigure the AI provider at runtime.

    Args:
        config: New provider configuration

    Returns:
        Success message
    """
    global _provider

    try:
        _provider = ProviderFactory.create_provider(config)

        # Validate the new provider
        is_valid = await _provider.validate_connection()

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Failed to validate new provider configuration"
            )

        return {
            "message": "Provider configured successfully",
            "provider": config.provider_name,
            "model": config.model_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")


@app.get("/v1/providers")
async def list_providers():
    """
    List all available providers.

    Returns:
        List of provider names
    """
    return {
        "providers": ProviderFactory.list_providers()
    }


@app.get("/v1/warmup/status")
async def warmup_status():
    """
    Get warmup task status.

    Returns:
        Warmup task information
    """
    return {
        "warmup_active": _warmup_task is not None and not _warmup_task.done(),
        "warmup_running": _warmup_task is not None,
        "warmup_done": _warmup_task.done() if _warmup_task else False,
        "info": "Warmup requests keep the model container warm to reduce Time To First Token (TTFT)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
