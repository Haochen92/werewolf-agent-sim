/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone keeps the P4 Docker image small (build_plan §7).
  output: 'standalone',
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['@mantine/core', '@mantine/hooks', '@tabler/icons-react'],
  },
};

export default nextConfig;
