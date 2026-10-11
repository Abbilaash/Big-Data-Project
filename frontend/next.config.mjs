/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  // The prototype's old routes now live under /people.
  async redirects() {
    return [
      { source: '/students', destination: '/people', permanent: true },
      { source: '/students/:id', destination: '/people/:id', permanent: true },
      { source: '/teammates', destination: '/people', permanent: true },
    ]
  },
}

export default nextConfig
