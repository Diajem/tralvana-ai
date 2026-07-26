import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
        <p className="max-w-md text-center text-sm text-gray-500">
          Clerk registration is disabled in this local environment. Add the
          Clerk development keys to enable account creation.
        </p>
      </main>
    );
  }
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 p-6">
      <SignUp />
    </main>
  );
}
