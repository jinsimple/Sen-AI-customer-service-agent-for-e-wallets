.PHONY: run test lint format typecheck check clean data data-check db-reset db-seed db demo-data verify-security

run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8010

test:
	pytest tests/ -v

# Kiểm tra lại JWT/RBAC/mã hoá/CORS/rate-limit đã vá — cần backend (:8010)
# và frontend (:3000) đang chạy sẵn (make run + npm run dev bên frontend/).
verify-security:
	bash scripts/verify_security.sh

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

check: lint format test

# ---------------------------------------------------------------------------
# Pipeline nạp dữ liệu — Data Brief §5.3. Ba tính chất bắt buộc:
# idempotent (chạy 2 lần ra cùng kết quả), deterministic (cùng seed → cùng
# DB byte-for-byte về mặt logic), fail-fast (data-check chặn dữ liệu bẩn
# trước khi seed, không bao giờ để DB chứa dữ liệu vi phạm bất biến).
# ---------------------------------------------------------------------------

# `data` sinh DỮ LIỆU ỨNG DỤNG và cố ý KHÔNG đụng thước đo: gen_dataset.py ghi
# cả eval/golden_set.jsonl qua một đường riêng không nằm trong --out, mà thước
# đó mang nhãn kiểm thêm tay đã được PO duyệt. Đẩy phần eval sinh ra vào thư mục
# tạm để nó bị vứt đi. Muốn sinh lại THƯỚC thì dùng `make data-va-thuoc` —
# tách hai lệnh để việc đó luôn là một quyết định, không phải tác dụng phụ.
data:
	python3 scripts/gen_dataset.py --seed 20260802 --out data/generated/ --eval-out $$(mktemp -d)/

# Chỉ dùng ở đợt reseed có chủ đích. Nó XOÁ mọi nhãn kiểm thêm tay trong
# eval/golden_set.jsonl — kiểm `git diff eval/` ngay sau khi chạy.
data-va-thuoc:
	python3 scripts/gen_dataset.py --seed 20260802 --out data/generated/ --cho-phep-ghi-de-thuoc

data-check:
	python3 scripts/validate_dataset.py data/generated/

db-reset:
	rm -f data/app.db
	python3 -m alembic upgrade head

db-seed:
	python3 scripts/seed_db.py

db: data data-check db-reset db-seed

# Ticket/resolution mẫu để bấm thử tay trên UI (phủ 12 ô ma trận + các trạng
# thái HITL/escalate/FS-06) — không thuộc pipeline tái lập, chạy sau `make db`.
demo-data:
	python3 scripts/seed_demo_scenarios.py

clean:
	rm -f data/app.db
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
