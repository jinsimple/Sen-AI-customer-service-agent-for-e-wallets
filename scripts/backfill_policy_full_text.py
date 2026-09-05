#!/usr/bin/env python3
"""ADR-065 (05/09) — backfill `PolicyDocument.full_text` cho tài liệu đã
index TRƯỚC khi cột này tồn tại (migration f1a2b3c4d5e6).

Vì sao cần ghép-tay thay vì đọc lại file gốc: dự án KHÔNG lưu file đã upload
(chỉ lưu chunk đã cắt), nên không có "văn bản gốc" nào khác để đọc lại.
Ghép các PolicyChunk theo `chunk_index`, khử overlap bằng cách tìm hậu tố
DÀI NHẤT của đoạn trước trùng khớp tiền tố của đoạn sau (tham số tìm kiếm
RAG_CHUNK_OVERLAP + biên độ dự phòng, vì `RecursiveCharacterTextSplitter`
snap theo ranh giới câu/đoạn nên overlap thật không LUÔN đúng bằng tham số
cấu hình). CHẤP NHẬN không hoàn hảo 100% cho dữ liệu CŨ — tài liệu upload
MỚI từ giờ luôn có full_text sạch (lưu tại lúc ingest, xem src/rag/ingest.py).

Chạy MỘT LẦN, idempotent (bỏ qua tài liệu đã có full_text)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import RAG_CHUNK_OVERLAP
from src.db.models import PolicyChunk, PolicyDocument
from src.db.session import get_engine

_BIEN_DO_DU_PHONG = 50


def _ghep_khu_overlap(pieces: list[str]) -> str:
    if not pieces:
        return ""
    ket_qua = pieces[0]
    for tiep in pieces[1:]:
        max_overlap = min(len(ket_qua), len(tiep), RAG_CHUNK_OVERLAP + _BIEN_DO_DU_PHONG)
        do_dai_overlap = 0
        for k in range(max_overlap, 0, -1):
            if ket_qua[-k:] == tiep[:k]:
                do_dai_overlap = k
                break
        ket_qua += tiep[do_dai_overlap:]
    return ket_qua


def backfill(session: Session) -> list[str]:
    docs = session.scalars(
        select(PolicyDocument).where(PolicyDocument.full_text.is_(None), PolicyDocument.status == "indexed")
    ).all()
    da_vá: list[str] = []
    for doc in docs:
        chunks = session.scalars(
            select(PolicyChunk).where(PolicyChunk.doc_id == doc.doc_id).order_by(PolicyChunk.chunk_index)
        ).all()
        if not chunks:
            continue
        doc.full_text = _ghep_khu_overlap([c.text for c in chunks])
        da_vá.append(doc.doc_id)
    session.commit()
    return da_vá


if __name__ == "__main__":
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=get_engine())
    s = Session()
    ids = backfill(s)
    print(f"Đã backfill full_text cho {len(ids)} tài liệu: {ids}")
