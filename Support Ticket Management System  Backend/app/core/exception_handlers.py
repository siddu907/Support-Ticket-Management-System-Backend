from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_payload(code: str, message: str) -> dict:
	return {"success": False, "error": {"code": code, "message": message}}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
	message = str(exc.detail)
	code_by_status = {400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 409: "CONFLICT", 413: "PAYLOAD_TOO_LARGE", 422: "VALIDATION_ERROR"}
	message_codes = {
		"Invalid status transition": "INVALID_STATUS_TRANSITION",
		"Task is already assigned": "ALREADY_ASSIGNED",
		"Unassigned tickets must be assigned": "INVALID_ASSIGNMENT_ENDPOINT",
		"Assigned tickets must be reassigned": "INVALID_REASSIGNMENT_ENDPOINT",
	}
	code = next((value for key, value in message_codes.items() if key in message), code_by_status.get(exc.status_code, "HTTP_ERROR"))
	return JSONResponse(status_code=exc.status_code, content=error_payload(code, message))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
	return JSONResponse(status_code=422, content=error_payload("VALIDATION_ERROR", "Request validation failed"))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
	return JSONResponse(status_code=500, content=error_payload("INTERNAL_SERVER_ERROR", "An unexpected internal server error occurred"))
