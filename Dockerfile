# Backend FastAPI — xem docs/DEPLOY.md cho bối cảnh triển khai (Docker Compose
# trên Oracle Cloud Always Free, ARM64/aarch64).
#
# ---- Stage 1: Build ----
FROM python:3.12-slim AS builder

WORKDIR /app

# build-essential: một số dependency của chromadb (onnxruntime/hnswlib) có thể
# thiếu sẵn wheel arm64 trên PyPI tuỳ phiên bản — nếu vậy pip tự build từ
# source, cần compiler có sẵn thay vì lỗi build giữa chừng.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Cài vào /install (không phải mặc định /root/.local) — /root thường mode 700,
# user không phải root (appuser ở stage sau) không traverse vào được dù đã
# chown nội dung bên trong, gây lỗi "Permission denied" khi chạy alembic/uvicorn.
ENV PYTHONUSERBASE=/install
# requirements.lock.txt, KHÔNG requirements.txt — [ĐO 20/08] hai ảnh build
# CÙNG NGÀY, CÙNG MÁY, cách nhau vài phút, CÙNG mã nguồn (băm nguồn khớp
# tuyệt đối) vẫn cho ra 6/168 gói KHÁC NHAU khi cài từ requirements.txt
# (27/37 gói ở đó dùng >=/~=, không ghim) — cây phụ thuộc trôi ngay trong
# một ngày, không phải rủi ro lý thuyết. requirements.txt là NGUỒN Ý ĐỊNH
# (khoảng phiên bản chấp nhận được), requirements.lock.txt là VẬT ĐÃ ĐO
# (đúng bộ đã kiểm) — xem đầu file lock để biết lý do sâu hơn (langchain-core
# 1.5.3 vs 1.5.4 đổi mô tả tool ~12% trên CÙNG mã nguồn).
#
# 🔴 CÁI GIÁ, đừng giấu: ghim lock nghĩa là CŨNG ghim luôn bản vá bảo mật của
# 168 gói đó — đổi "luôn mới nhất, không biết đang chạy gì" lấy "biết chính
# xác đang chạy gì, phải TỰ đi cập nhật". Đây là NỢ CÓ LỊCH TRẢ, không phải
# việc đã xong — ai cập nhật requirements.txt (thêm/nâng gói) PHẢI sinh lại
# lock, không sinh lại thì file này hoá thạch và mất tác dụng.
#
# Sinh lại lock (chạy sau khi đổi requirements.txt, TRƯỚC khi commit):
#   docker compose exec backend python3 -m pip freeze > requirements.lock.txt
# rồi sửa 3 dòng đầu file: ngày + image build (`docker images fin05-backend --format '{{.ID}}'`).
COPY requirements.lock.txt requirements.txt
# `--retries 5 --timeout 60` — MỞ RỘNG che chắn lúc tải gói, KHÔNG PHẢI bản vá
# cho một lỗi cụ thể. Đọc kỹ vế này trước khi tin nó:
#
# [ĐO 25/08] một lần `docker compose build --no-cache` từ cây SẠCH đỏ ngay tại
# dòng dưới: `json.decoder.JSONDecodeError: Expecting ',' … char 5980170`.
# Chạy lại đúng bước ấy: XANH, không sửa một dòng nào ⟹ lỗi tải gói NHẤT THỜI.
#
# 🔴 KHÔNG hứa rằng hai cờ này cứu được ĐÚNG ca đó. `--retries` bắt ở tầng KẾT
# NỐI, còn `JSONDecodeError` xảy ra khi phản hồi đã về đủ về mặt giao thức
# nhưng NỘI DUNG bị cắt — pip có thể không coi đó là lỗi đáng thử lại. Chúng
# rẻ gần bằng 0 và phủ RỘNG hơn, thế thôi. Đừng viết "đã vá lỗi mạng lúc build".
#
# 🔴 VÌ SAO KHÔNG dùng `scripts/ci_pip_install_retry.sh` như CI — đã cân, và
# bác, 25/08 (đừng đề xuất lại mà chưa đọc ba dòng này):
#   ① script:44 gọi `pip install` KHÔNG kèm `--user` ⟹ gói rơi vào site-packages
#     hệ thống thay vì `/install` (PYTHONUSERBASE, dòng 19) ⟹ `COPY --from=
#     builder /install` ở stage 2 mang sang một thư mục RỖNG. Build XANH, ảnh
#     CHẠY KHÔNG ĐƯỢC, và hỏng ở runtime — xa hẳn chỗ gây ra.
#   ② script:49 chỉ thử lại khi khớp 8 chuỗi lỗi mạng ĐÃ TỪNG THẤY. [ĐO] grep
#     đủ 8 chuỗi trên log lần đỏ trên → 0 kết quả ⟹ nó sẽ vào nhánh "LỖI KHÔNG
#     PHẢI MẠNG — DỪNG" và exit 1. Tức nó KHÔNG vá được đúng ca ta đang nói tới.
#   ③ script:32 từ chối mọi tệp không phải `*.lock.txt` (exit 2), nên nó cũng
#     KHÔNG dùng được cho lệnh tải wheel spaCy ở dưới. Hai cờ này thì phủ cả hai.
# Một bộ khớp theo DANH SÁCH TRẮNG các lỗi đã từng thấy luôn đi sau thực tế
# đúng một sự cố; cờ của chính pip xử ở tầng không cần biết lỗi tên gì.
RUN pip install --no-cache-dir --user --retries 5 --timeout 60 -r requirements.txt
# Model NER cho PII scrubbing hybrid (src/observability/pii.py) — dùng thẳng
# `pip install --user <wheel URL>` thay vì `spacy download` (lệnh tiện ích
# của spaCy KHÔNG tôn trọng PYTHONUSERBASE/--user — phát hiện thật lúc build:
# model cài vào site-packages toàn cục của stage builder, KHÔNG nằm trong
# /install nên bị rớt mất khi COPY --from=builder /install sang stage 2,
# runtime báo "Can't find model 'xx_ent_wiki_sm'"). pip install --user thì
# tôn trọng PYTHONUSERBASE, model nằm chung chỗ với các gói khác, copy đúng.
RUN pip install --no-cache-dir --user --retries 5 --timeout 60 \
    https://github.com/explosion/spacy-models/releases/download/xx_ent_wiki_sm-3.8.0/xx_ent_wiki_sm-3.8.0-py3-none-any.whl

# ---- Stage 2: Production ----
FROM python:3.12-slim

WORKDIR /app

# libpq5: psycopg2-binary cần thư viện client Postgres lúc runtime dù đã có
# sẵn trong wheel binary — libpq-dev không cần (chỉ cần lúc build/compile).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder — /install là thư mục top-level trung
# lập, không dính quyền hạn chế của /root, appuser (non-root) đọc/thực thi
# được bình thường.
COPY --from=builder /install /install
ENV PYTHONUSERBASE=/install
ENV PATH=/install/bin:$PATH

# DẤU VẬT của bản đang chạy. Truyền bằng --build-arg, KHÔNG đọc git lúc chạy:
# image runtime không có `.git` (.dockerignore loại), nên một cách lấy nhãn mà
# tự nó có thể thất bại im lặng thì tệ hơn không có nhãn.
#
# Vì sao cần: 16/08 phải đọc `git merge-base` trên máy dev mới biết production
# đã nhận vá 429 chưa — KHÔNG có cách nào hỏi chính sản phẩm đang chạy.
#
# Mặc định "khong-ro" CỐ Ý tự tố cáo. Tuyệt đối không để rỗng hay một giá trị
# trông hợp lệ: nhãn nói dối nguy hơn không nhãn.
ARG BUILD_COMMIT=khong-ro
ARG BUILD_AT=khong-ro
ENV BUILD_COMMIT=$BUILD_COMMIT
ENV BUILD_AT=$BUILD_AT
# Nhãn định danh MÃ SẢN PHẨM (băm nội dung src/**/*.py), khác BUILD_COMMIT là
# nhãn định danh TRẠNG THÁI KHO. Cần cả hai: commit trả lời "kho ở đâu", băm
# trả lời "mã nào" — và 17/08 đã chứng minh commit không trả lời được câu sau.
# (nhãn băm src/ KHÔNG phải build-arg — xem RUN sau COPY bên dưới)

# Non-root user cho tiến trình ứng dụng thật (không chạy uvicorn bằng root) —
# việc hạ quyền thực hiện trong docker-entrypoint.sh lúc container khởi động,
# không phải ở đây, vì named volume (chroma_data/logs_data) chỉ tồn tại lúc
# container chạy, không tồn tại lúc build image.
RUN useradd -m appuser

# Copy application code
COPY . .
# NHÃN BĂM src/ — tính TỪ NỘI DUNG VỪA COPY, không nhận từ ngoài.
#
# Bản đầu (17/08) nhận qua `--build-arg BUILD_SRC_HASH`. Sai, và sai theo hình
# dạng tệ nhất: quên truyền -> nhãn thành "khong-ro" -> phép kiểm lúc khởi động
# TỰ TẮT, mà vẫn trông y hệt một cổng đang bảo vệ. Cổng tự tắt khi thiếu đầu
# vào tệ hơn cổng không có, vì nó tắt đúng lúc quy trình dựng bị làm ẩu — tức
# đúng lúc cần nó nhất.
#
# Sửa tận gốc thay vì fail-closed trên tham số: BỎ tham số. Không còn gì để
# quên truyền. Dùng lại chính `bam_ma_nguon()` nên ảnh và runtime không thể
# dùng hai thuật toán khác nhau.
RUN python -c "import sys; sys.path.insert(0,'/app'); from src.dau_ma_nguon import bam_ma_nguon; open('/app/.bam_ma_nguon','w').write(bam_ma_nguon())"  && cat /app/.bam_ma_nguon

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && mkdir -p /app/data /app/logs

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/health')" || exit 1

# entrypoint chown /app/data + /app/logs (volume mount, quyền root mặc định
# lúc Docker tạo mới) rồi mới hạ quyền xuống appuser để chạy migration +
# uvicorn — xem docker-entrypoint.sh.
#
# TỪ 2026-08-13 chạy NHIỀU worker được (biến UVICORN_WORKERS). Ràng buộc "đúng
# 1 worker" trước đây đến từ 2 thứ giữ state trong RAM per-process, cả hai đã
# được đưa ra ngoài:
#   - MemorySaver -> PostgresSaver (ADR-014): hội thoại nằm ở Postgres.
#   - ConnectionManager: thêm fan-out Redis pub/sub (ADR-015) để socket ở
#     worker khác vẫn nhận được tin.
# Thiếu MỘT trong hai thì multi-worker làm hỏng âm thầm (mất trí nhớ agent
# hoặc mất tin nhắn live-chat), nên đừng tăng worker mà bỏ qua 2 ADR trên.
ENTRYPOINT ["/docker-entrypoint.sh"]
