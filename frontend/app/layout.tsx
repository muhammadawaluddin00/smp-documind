import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SMP DocuMind — AI Document Q&A',
  description:
    'Internal Document Q&A assistant for SMP Technology. Ask questions, get grounded answers with citations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin=""
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-ink-50 text-ink-900 font-body antialiased">
        {children}
      </body>
    </html>
  );
}
