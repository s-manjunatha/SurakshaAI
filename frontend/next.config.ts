/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  transpilePackages: ["echarts", "zrender"],
};

module.exports = nextConfig;
