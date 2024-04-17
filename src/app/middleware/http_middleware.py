from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CustomMiddleware(BaseHTTPMiddleware):
    """
    Give access to Error type and details in HttpResponse.body
    with customm structure.
    """
    def __init__(self, app) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Custom middleware for global error handling
        """
        try:
            return await call_next(request)
        except HTTPException as e:
            error_detail = "Internal server error."
            status_code = 500
            if hasattr(e, "status_code"):
                status_code = e.status_code
            if hasattr(e,"detail"):
                error_detail = e.detail
            return Response(status_code=status_code,content=error_detail)
        except Exception as e:
            error_detail = "Internal server error."
            status_code = 500
            error_errors = []
            if hasattr(e, "status_code"):
                status_code = e.status_code
            if hasattr(e,"detail"):
                error_detail = e.detail
            return Response(status_code=status_code,content=[error_detail,e])