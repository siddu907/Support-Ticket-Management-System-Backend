from pathlib import Path

from fastapi import HTTPException, UploadFile


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf", "text/plain", "application/zip"}


def read_upload(file: UploadFile, max_size: int) -> bytes:
	if file.content_type not in ALLOWED_MIME_TYPES:
		raise HTTPException(400, "Unsupported file type")
	data = file.file.read()
	if len(data) > max_size:
		raise HTTPException(413, "File exceeds maximum size")
	signatures = {
		"image/jpeg": (b"\xff\xd8\xff",),
		"image/png": (b"\x89PNG\r\n\x1a\n",),
		"application/pdf": (b"%PDF-",),
		"application/zip": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
	}
	expected = signatures.get(file.content_type)
	if expected and not any(data.startswith(signature) for signature in expected):
		raise HTTPException(400, "File content does not match its MIME type")
	if file.content_type == "text/plain":
		try:
			data.decode("utf-8")
		except UnicodeDecodeError as error:
			raise HTTPException(400, "File content does not match its MIME type") from error
	return data
