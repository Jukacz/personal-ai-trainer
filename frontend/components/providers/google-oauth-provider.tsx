'use client';

import { GoogleOAuthProvider as Provider } from '@react-oauth/google';

export function GoogleOAuthProvider({ children }: { children: React.ReactNode }) {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

  if (!clientId) {
    console.warn('NEXT_PUBLIC_GOOGLE_CLIENT_ID is not set. Google OAuth will not work.');
  }

  return (
    <Provider clientId={clientId}>
      {children}
    </Provider>
  );
}
