"""
worker.py

Cloudflare Workers entry point for the FastAPI application.
Bridges the ASGI application to the Cloudflare Workers runtime.
"""

from workers import WorkerEntrypoint
import asgi

from main import app
from security.settings import reload_settings_from_env


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Dynamically inject environment variables and bindings from self.env
        # into Pydantic Settings and os.environ
        reload_settings_from_env(self.env)
        
        # Dispatch the request to the FastAPI app using the ASGI adapter
        # request.js_object is used to interface with Pyodide's JS request
        return await asgi.fetch(app, request.js_object, self.env)
