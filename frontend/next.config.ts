import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker multi-stage build (frontend/Dockerfile) copy đúng
  // .next/standalone + .next/static thay vì cả node_modules — image runtime
  // gọn hơn nhiều. Không ảnh hưởng `npm run dev`/`next start` chạy tay.
  output: "standalone",
};

export default nextConfig;
