"""Run the FastAPI service locally."""
import uvicorn
if __name__ == "__main__":
    # Intentional: bind all interfaces for local/container deployment.
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
