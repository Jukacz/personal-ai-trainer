'use client';

import { QueryProvider } from './query-provider';
import { GoogleOAuthProvider } from './google-oauth-provider';
import { AuthProvider } from './auth-provider';

export function RootProviders({ children }: { children: React.ReactNode }) {
  return (
    <QueryProvider>
      <GoogleOAuthProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </GoogleOAuthProvider>
    </QueryProvider>
  );
}
