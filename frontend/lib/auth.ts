import Cookies from 'js-cookie';

const ACCESS_TOKEN_KEY = 'access_token';

/**
 * Get the access token from cookies
 */
export function getAccessToken(): string | null {
  return Cookies.get(ACCESS_TOKEN_KEY) || null;
}

/**
 * Set the access token in cookies
 * Expires in 30 minutes (1/48 of a day)
 */
export function setAccessToken(token: string): void {
  Cookies.set(ACCESS_TOKEN_KEY, token, {
    expires: 1/48, // 30 minutes
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production'
  });
}

/**
 * Remove the access token from cookies
 */
export function removeAccessToken(): void {
  Cookies.remove(ACCESS_TOKEN_KEY);
}
