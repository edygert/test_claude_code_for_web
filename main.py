"""
FastAPI application for AI streaming service.
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from ai_streaming import StreamingRequest, ProviderConfig
from ai_streaming.factory import ProviderFactory
from ai_streaming.providers.base import BaseAIProvider


# Global provider instance
_provider: Optional[BaseAIProvider] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global _provider

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

    yield

    # Cleanup if needed
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
        "provider": _provider.config.provider_name if _provider else "none"
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
        "model": provider.config.model_id
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
