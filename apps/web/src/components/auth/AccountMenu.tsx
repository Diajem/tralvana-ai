"use client";

import {
  SignInButton,
  SignUpButton,
  UserButton,
  useAuth,
} from "@clerk/nextjs";

export function AccountMenu() {
  const { isLoaded, isSignedIn } = useAuth();
  if (!isLoaded) {
    return null;
  }
  return (
    <div className="fixed right-4 top-4 z-50 flex items-center gap-2">
      {!isSignedIn ? (
        <>
        <SignInButton mode="modal">
          <button className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:border-indigo-300">
            Sign in
          </button>
        </SignInButton>
        <SignUpButton mode="modal">
          <button className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700">
            Create account
          </button>
        </SignUpButton>
        </>
      ) : (
        <UserButton showName />
      )}
    </div>
  );
}
