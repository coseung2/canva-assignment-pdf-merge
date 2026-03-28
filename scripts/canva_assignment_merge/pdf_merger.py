from __future__ import annotations

from io import BytesIO
from typing import Iterable

from pypdf import PdfReader, PdfWriter


def merge_pdf_buffers(pdf_buffers: Iterable[bytes]) -> bytes:
    writer = PdfWriter()
    count = 0
    for pdf_bytes in pdf_buffers:
        reader = PdfReader(BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
        count += 1

    if count == 0:
        raise ValueError("no PDF buffers supplied for merge")

    output = BytesIO()
    writer.write(output)
    return output.getvalue()
