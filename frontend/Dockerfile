# Next.js BFF (frontend/src/app/api/) — xem docs/DEPLOY.md. `output: "standalone"`
# (next.config.ts) cho phép copy đúng phần cần chạy, không phải cả node_modules.
#
# ---- Stage 1: deps ----
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- Stage 2: build ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Băm nguồn frontend — cùng vai trò với /app/.source_hash của backend
# (src/build_stamp.py): danh tính CỦA ẢNH là nội dung src/, không phải
# BUILD_COMMIT/image ID (xem src/build_stamp.py — build_commit đã bị chứng
# minh nói dối theo cả hai chiều 17/08). Phải chạy TRƯỚC `npm run build` vì
# `output: "standalone"` xoá hẳn frontend/src/ khỏi stage runner — không tính
# băm được ở đó như phía backend, nên đóng nhãn ngay tại đây rồi copy sang.
RUN node src/build_stamp.mjs > /app/.source_hash && cat /app/.source_hash

# BACKEND_URL không cần lúc build — server-api.ts đọc process.env lúc request
# chạy thật (route handler server-side), không phải lúc `next build`.
#
# NEXT_PUBLIC_QUICK_LOGIN — mặc định "false". Next.js thay NEXT_PUBLIC_* LÚC
# BUILD nên KHÔNG truyền --build-arg = ba nút đăng nhập nhanh (page.tsx) và
# mật khẩu đi kèm KHÔNG TỒN TẠI trong bundle, không phải chỉ ẩn UI. Chỉ bật
# cho ảnh gắn tag riêng dùng một lần (quay video demo), không đè `latest`.
ARG NEXT_PUBLIC_QUICK_LOGIN=false
ENV NEXT_PUBLIC_QUICK_LOGIN=$NEXT_PUBLIC_QUICK_LOGIN

# NEXT_PUBLIC_HIDE_ENV_BADGE — mặc định "false", cùng khuôn trên. Cảnh 6
# (ADR-060) cần APP_ENV != production để bật OTP_DEMO_MODE, cờ này ẩn badge
# môi trường độc lập với APP_ENV — xem EnvBadge.tsx.
ARG NEXT_PUBLIC_HIDE_ENV_BADGE=false
ENV NEXT_PUBLIC_HIDE_ENV_BADGE=$NEXT_PUBLIC_HIDE_ENV_BADGE
RUN npm run build

# ---- Stage 3: runtime ----
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /app/public ./public
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder /app/.source_hash ./.source_hash

USER appuser
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
