import "./globals.css";

export const metadata = {
  title: "Bitcoin Recovery Vault",
  description: "Non-custodial public-chain research dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}