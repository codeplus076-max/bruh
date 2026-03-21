/** @type {import('next').NextConfig} */
const nextConfig = {
    compress: true, // Enable gzip and brotli
    swcMinify: true, // Use SWC minifier for faster/smaller builds
    experimental: {
        optimizePackageImports: ["lucide-react", "framer-motion"],
    },
};

export default nextConfig;
