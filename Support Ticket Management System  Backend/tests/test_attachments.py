from io import BytesIO

import pytest
from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from app.services.attachment_service import read_upload


def test_attachment_signature_is_validated():
	file = UploadFile(filename="document.pdf", file=BytesIO(b"not a pdf"), headers={"content-type": "application/pdf"})
	with pytest.raises(HTTPException) as error:
		read_upload(file, 1024)
	assert error.value.status_code == 400
