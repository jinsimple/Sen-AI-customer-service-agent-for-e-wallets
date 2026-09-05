"""policy_documents.full_text (ADR-065 — deep-link toàn văn /policy-search)

Revision ID: f1a2b3c4d5e6
Revises: 6d36fb6e303e
Create Date: 2026-09-05

`PolicyChunk` chỉ lưu TỪNG ĐOẠN đã cắt (RecursiveCharacterTextSplitter,
chunk_size=800, overlap=150) — ghép các chunk theo chunk_index KHÔNG tái tạo
đúng văn bản gốc (overlap lặp ở mỗi ranh giới). Cột này lưu toàn văn GỐC
(đọc ngay trước khi cắt, xem src/rag/ingest.py) để trang đọc toàn văn không
phải đoán ghép lại từ chunk.

NULLABLE — 4 tài liệu đã index TRƯỚC cột này tồn tại không có toàn văn gốc
lưu sẵn; backfill (script riêng, chấp nhận ghép-tay không dedup overlap
hoàn hảo cho 4 tài liệu CŨ) là việc VẬN HÀNH một lần, không phải điều kiện
để migration này chạy được. Tài liệu MỚI từ giờ luôn có full_text sạch.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.db.crypto_types import EncryptedText


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '6d36fb6e303e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('policy_documents', sa.Column('full_text', EncryptedText(), nullable=True))


def downgrade() -> None:
    op.drop_column('policy_documents', 'full_text')
