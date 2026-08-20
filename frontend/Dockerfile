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
# Băm nguồn frontend — cùng vai trò với /app/.bam_ma_nguon của backend
# (src/dau_ma_nguon.py): danh tính CỦA ẢNH là nội dung src/, không phải
# BUILD_COMMIT/image ID (xem src/dau_ma_nguon.py — build_commit đã bị chứng
# minh nói dối theo cả hai chiều 17/08). Phải chạy TRƯỚC `npm run build` vì
# `output: "standalone"` xoá hẳn frontend/src/ khỏi stage runner — không tính
# băm được ở đó như phía backend, nên đóng nhãn ngay tại đây rồi copy sang.
RUN node src/dau_ma_nguon.mjs > /app/.bam_ma_nguon && cat /app/.bam_ma_nguon

# BACKEND_URL không cần lúc build — server-api.ts đọc process.env lúc request
# chạy thật (route handler server-side), không phải lúc `next build`.
RUN npm run build

# ---- Stage 3: runtime ----
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /app/public ./public
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder /app/.bam_ma_nguon ./.bam_ma_nguon

USER appuser
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
