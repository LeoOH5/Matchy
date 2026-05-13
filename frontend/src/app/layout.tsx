import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Matchy — 청년 맞춤 정책 찾기",
  description: "내 조건에 딱 맞는 청년 정책·대출 상품을 한 번에 찾아보세요",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-slate-50 antialiased">{children}</body>
    </html>
  );
}
