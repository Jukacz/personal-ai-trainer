import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const AUTH_PAGES = ['/login', '/register'];

// Paths that don't require authentication
const publicPaths = AUTH_PAGES;

// Paths that are always public (exact match)
const publicExactPaths = ['/'];

function isJwtToken(value: string | undefined): boolean {
  if (!value) {
    return false;
  }

  const parts = value.split('.');
  return parts.length === 3 && parts.every(part => part.length > 0);
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get('access_token')?.value;
  const isAuthenticated = isJwtToken(accessToken);

  const isPublicPath =
    publicExactPaths.includes(pathname) ||
    publicPaths.some(path => pathname.startsWith(path));

  // Auth pages (login/register) - redirect authenticated users to dashboard
  const isAuthPage = AUTH_PAGES.some(path => pathname.startsWith(path));
  if (isAuthPage && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // If user is not authenticated and trying to access protected pages, redirect to login
  if (!isPublicPath && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
