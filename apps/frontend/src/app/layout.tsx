import type { Metadata } from 'next';
import '../styles/globals.css';
import { Providers } from '@/components/providers';

export const metadata: Metadata = {
  title: 'AgentForge - AI-Powered Software Development Platform',
  description: 'Build software with AI agents',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}