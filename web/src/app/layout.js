import './globals.css';

export const metadata = {
  title: 'Content Generator | Vitti Capital',
  description: 'AI-powered content generation dashboard for LinkedIn ideas and CEO posts.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <main className="container">
          {children}
        </main>
      </body>
    </html>
  );
}
