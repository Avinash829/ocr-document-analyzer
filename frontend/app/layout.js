import "./globals.css";

export const metadata = {
  title: "Veda - Assessment Mapper",
  description: "Map handwritten student answers to assessment questions.",
  icons: {
    icon: "/assets/logo.png",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
