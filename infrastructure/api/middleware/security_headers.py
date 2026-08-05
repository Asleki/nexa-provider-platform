from starlette.middleware.base import BaseHTTPMiddleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response=await call_next(request)
        response.headers.setdefault("x-content-type-options","nosniff")
        response.headers.setdefault("x-frame-options","DENY")
        response.headers.setdefault("referrer-policy","no-referrer")
        response.headers.setdefault("permissions-policy","geolocation=(), microphone=(), camera=()")
        return response
