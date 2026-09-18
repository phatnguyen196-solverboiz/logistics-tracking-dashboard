import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hải Lộ Logistics",
  description: "Automated shipment tracking dashboard",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <Link className="brand" href="/">
            <span className="brand-mark">HL</span>
            <span>Hải Lộ</span>
          </Link>
          <nav>
            <Link href="/">Dashboard</Link>
            <Link className="primary-link" href="/shipments/new">Add shipment</Link>
          </nav>
        </header>
        <main className="page-shell">{children}</main>
      </body>
    </html>
  );
}
