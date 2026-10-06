/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Django URLs end with "/"; keep them as-is for the /api proxy route.
  skipTrailingSlashRedirect: true,
};

export default nextConfig;
