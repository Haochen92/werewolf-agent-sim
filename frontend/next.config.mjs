/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone keeps the P4 Docker image small (build_plan §7).
  output: 'standalone',
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['@mantine/core', '@mantine/hooks', '@tabler/icons-react'],
  },
  // the score's tracks carry their version in the name (`lobby-bossa.v1.mp3`; a new take is a
  // new name), so a browser and the CDN keep each for good instead of asking again every visit
  async headers() {
    return [
      {
        source: '/music/:file*',
        headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }],
      },
    ];
  },
};

export default nextConfig;
