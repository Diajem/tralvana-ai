import { auth } from "@clerk/nextjs/server";

export async function serverSessionToken(): Promise<string | undefined> {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return undefined;
  }
  const session = await auth();
  if (!session.userId) {
    session.redirectToSignIn();
    return undefined;
  }
  return (await session.getToken()) ?? undefined;
}
