import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import {
  AuthenticationGate,
  ClerkAuthBridge,
  LocalAuthBridge,
} from "@/lib/auth-context";
import { AccountMenu } from "@/components/auth/AccountMenu";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tralvana AI | One Intelligent Plan for Your Whole Trip",
  description:
    "Plan flights, accommodation, budget, visa guidance, weather, events, and a daily itinerary in one AI-powered travel plan.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const content = publishableKey ? (
    <ClerkProvider
      publishableKey={publishableKey}
      localization={{
        signIn: {
          start: {
            title: "Sign in to Tralvana",
            titleCombined: "Sign in to Tralvana",
          },
        },
        signUp: {
          start: {
            title: "Create your Tralvana account",
            titleCombined: "Create your Tralvana account",
          },
        },
      }}
    >
      <ClerkAuthBridge>
        <AccountMenu />
        <AuthenticationGate>{children}</AuthenticationGate>
      </ClerkAuthBridge>
    </ClerkProvider>
  ) : (
    <LocalAuthBridge>
      <AuthenticationGate>{children}</AuthenticationGate>
    </LocalAuthBridge>
  );
  return (
    <html lang="en">
      <body>{content}</body>
    </html>
  );
}
