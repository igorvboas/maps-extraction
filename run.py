import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    # Set the event loop policy to WindowsProactorEventLoopPolicy on Windows
    # This is required for Playwright to work with asyncio subprocesses
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Run Uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
