/**
 * Root layout component - Wraps all pages with HTML structure and metadata
 */

// Page metadata for SEO and browser display
export const metadata = {
  title: 'LinkedIn Lead Profiling',
  description: 'Automated LinkedIn lead profiling and ICP matching',
};

// Root layout wrapper for all pages
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;  // Typed children prop
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
