from __future__ import annotations

import io
import textwrap
from dataclasses import dataclass
from typing import Iterable, Sequence


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 40
RIGHT_MARGIN = 40
TOP_MARGIN = 46
BOTTOM_MARGIN = 46


@dataclass(frozen=True)
class PdfLine:
    text: str
    font: str = "F1"
    size: int = 10
    gap_after: int = 2


def _safe_pdf_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ")
    text = text.encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_text(text: str, width: int) -> list[str]:
    wrapped = textwrap.wrap(
        text,
        width=width,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
    )
    return wrapped or [""]


def _prepare_lines(lines: Sequence[PdfLine]) -> list[PdfLine]:
    prepared: list[PdfLine] = []
    for line in lines:
        max_width = 92 if line.size <= 10 else 78
        wrapped = _wrap_text(line.text, max_width)
        for idx, chunk in enumerate(wrapped):
            prepared.append(
                PdfLine(
                    text=chunk,
                    font=line.font,
                    size=line.size,
                    gap_after=line.gap_after if idx == len(wrapped) - 1 else 0,
                )
            )
    return prepared


def _paginate_lines(lines: Sequence[PdfLine]) -> list[list[PdfLine]]:
    pages: list[list[PdfLine]] = []
    current: list[PdfLine] = []
    remaining = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN

    for line in lines:
        line_height = max(line.size + line.gap_after + 4, 12)
        if current and remaining < line_height:
            pages.append(current)
            current = []
            remaining = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
        current.append(line)
        remaining -= line_height

    if current:
        pages.append(current)

    return pages or [[]]


def _build_stream(page_lines: Sequence[PdfLine]) -> bytes:
    y = PAGE_HEIGHT - TOP_MARGIN
    commands: list[str] = []

    for line in page_lines:
        commands.append(f"BT /{line.font} {line.size} Tf 1 0 0 1 {LEFT_MARGIN} {int(y)} Tm ({_safe_pdf_text(line.text)}) Tj ET")
        y -= max(line.size + line.gap_after + 4, 12)

    return ("\n".join(commands) + "\n").encode("latin-1")


def build_simple_pdf(title: str, subtitle: str, sections: Sequence[tuple[str, Sequence[str]]]) -> bytes:
    lines: list[PdfLine] = [
        PdfLine(title, font="F2", size=18, gap_after=6),
    ]
    if subtitle:
        lines.append(PdfLine(subtitle, font="F1", size=10, gap_after=10))

    for section_title, body_lines in sections:
        lines.append(PdfLine(section_title, font="F2", size=13, gap_after=4))
        for body in body_lines:
            lines.append(PdfLine(body, font="F1", size=10, gap_after=2))
        lines.append(PdfLine("", font="F1", size=10, gap_after=6))

    pages = _paginate_lines(_prepare_lines(lines))

    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets: dict[int, int] = {}

    def write_obj(obj_num: int, payload: bytes) -> None:
        offsets[obj_num] = buffer.tell()
        buffer.write(f"{obj_num} 0 obj\n".encode("latin-1"))
        buffer.write(payload)
        buffer.write(b"\nendobj\n")

    total_objects = 4 + (len(pages) * 2)
    page_obj_nums = [5 + (idx * 2) for idx in range(len(pages))]
    content_obj_nums = [6 + (idx * 2) for idx in range(len(pages))]

    write_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{num} 0 R" for num in page_obj_nums)
    write_obj(2, f"<< /Type /Pages /Count {len(pages)} /Kids [{kids}] >>".encode("latin-1"))
    write_obj(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    write_obj(4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>")

    for page_idx, page_lines in enumerate(pages):
        content = _build_stream(page_lines)
        write_obj(
            content_obj_nums[page_idx],
            (
                f"<< /Length {len(content)} >>\nstream\n".encode("latin-1")
                + content
                + b"endstream"
            ),
        )
        write_obj(
            page_obj_nums[page_idx],
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_obj_nums[page_idx]} 0 R "
                "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> >>"
            ).encode("latin-1"),
        )

    xref_start = buffer.tell()
    buffer.write(f"xref\n0 {total_objects + 1}\n".encode("latin-1"))
    buffer.write(b"0000000000 65535 f \n")
    for obj_num in range(1, total_objects + 1):
        offset = offsets.get(obj_num, 0)
        buffer.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
    buffer.write(
        (
            f"trailer\n<< /Size {total_objects + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n"
        ).encode("latin-1")
    )

    return buffer.getvalue()
