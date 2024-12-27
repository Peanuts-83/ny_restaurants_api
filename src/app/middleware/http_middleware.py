import json
from typing import Any
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
            response = await call_next(request)
            return response
        except HTTPException as e:
            status_code = 500
            error_detail = "Internal server error."
            error_content = {"detail": error_detail}
            if hasattr(e, "status_code"):
                status_code = e.status_code
            if hasattr(e, "detail"):
                error_detail = e.detail
            if hasattr(e, "obj"):
                error_content["obj"] = e.obj
            if hasattr(e, "args"):
                error_content["args"] = e.args
            if hasattr(e, "_errors"):
                error_content["errors"] = e._errors
            return Response(
                status_code=status_code,
                content=json.dumps(error_content),
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            status_code = 500
            error_detail = "Internal server error."
            error_content = {"detail": error_detail}
            if hasattr(e, "status_code"):
                status_code = e.status_code
            if hasattr(e, "detail"):
                error_detail = e.detail
            if hasattr(e, "obj"):
                error_content["obj"] = e.obj
            if hasattr(e, "args"):
                error_content["args"] = e.args
            if hasattr(e, "_errors"):
                error_content["errors"] = e._errors
            return Response(
                status_code=status_code,
                content=json.dumps(error_content, default=self.safe_serializer),
                headers={"Content-Type": "application/json"},
            )

    def safe_serializer(self, obj):
        return str(obj)


class HttpResponse(BaseModel):
    statusText: str|None
    status: int
    body: Any
    headers: Any
    url: str
