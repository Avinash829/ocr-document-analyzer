import "./globals.css";

export const metadata = {
  title: "Veda — Assessment Mapper",
  description: "Map handwritten student answers to assessment questions.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
