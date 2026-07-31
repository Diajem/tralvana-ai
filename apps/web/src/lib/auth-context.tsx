"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  createContext,
  useContext,
  useEffect,
  type ReactNode,
} from "react";
import { setAuthTokenProvider } from "@/lib/api";

interface TralvanaAuth {
  clerkEnabled: boolean;
  loaded: boolean;
  signedIn: boolean;
  userId: string | null;
}

const AuthContext = createContext<TralvanaAuth>({
  clerkEnabled: false,
  loaded: true,
  signedIn: true,
  userId: null,
});

export function LocalAuthBridge({ children }: { children: ReactNode }) {
  useEffect(() => {
    setAuthTokenProvider(null);
  }, []);
  return (
    <AuthContext.Provider
      value={{ clerkEnabled: false, loaded: true, signedIn: true, userId: null }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function ClerkAuthBridge({ children }: { children: ReactNode }) {
  const { getToken, isLoaded, isSignedIn, userId } = useAuth();

  useEffect(() => {
    setAuthTokenProvider(() => getToken());
    return () => setAuthTokenProvider(null);
  }, [getToken]);

  return (
    <AuthContext.Provider
      value={{
        clerkEnabled: true,
        loaded: isLoaded,
        signedIn: Boolean(isSignedIn),
        userId: userId ?? null,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

const PUBLIC_PATHS = new Set(["/", "/demo"]);
const PUBLIC_PATH_PREFIXES = ["/sign-in", "/sign-up"];

function isPublicPath(pathname: string): boolean {
  return (
    PUBLIC_PATHS.has(pathname) ||
    PUBLIC_PATH_PREFIXES.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    )
  );
}

export function AuthenticationGate({ children }: { children: ReactNode }) {
  const auth = useContext(AuthContext);
  const pathname = usePathname();

  if (!auth.clerkEnabled || isPublicPath(pathname)) {
    return children;
  }
  if (!auth.loaded) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <p className="text-sm text-gray-500">Checking your secure session…</p>
      </main>
    );
  }
  if (!auth.signedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
        <div className="max-w-sm rounded-2xl bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-gray-900">Sign in to Tralvana</h1>
          <p className="mt-2 text-sm text-gray-500">
            Your profile, saved goals, trips, and AI planning history are private to your account.
          </p>
          <Link
            href="/sign-in"
            className="mt-6 inline-flex rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Continue to sign in
          </Link>
        </div>
      </main>
    );
  }
  return children;
}

export function useTralvanaAuth(): TralvanaAuth {
  return useContext(AuthContext);
}
