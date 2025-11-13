import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Authentication Middleware
 * 
 * Protects all routes except /login with password authentication.
 * 
 * How it works:
 * 1. Checks for "auth_token" cookie on every request
 * 2. If user is NOT authenticated:
 *    - Accessing /login → Allow (show login page)
 *    - Accessing any other route → Redirect to /login
 * 3. If user IS authenticated:
 *    - Accessing /login → Redirect to / (already logged in)
 *    - Accessing any other route → Allow
 * 
 * Cookie Details:
 * - Name: auth_token
 * - Expected Value: "authenticated"
 * - Set by: /api/auth/login route
 * - Expires: 7 days
 */

export function middleware(request: NextRequest) {
  // Get authentication cookie
  const authToken = request.cookies.get('auth_token');
  const isAuthenticated = authToken?.value === 'authenticated';
  
  // Get current path
  const { pathname } = request.nextUrl;
  
  // Allow access to login page assets and API routes
  const isLoginPage = pathname === '/login';
  const isApiRoute = pathname.startsWith('/api');
  
  // Skip middleware for API routes (they have their own logic)
  if (isApiRoute) {
    return NextResponse.next();
  }
  
  // If user is authenticated and trying to access login page
  if (isAuthenticated && isLoginPage) {
    // Redirect to dashboard (already logged in)
    return NextResponse.redirect(new URL('/', request.url));
  }
  
  // If user is NOT authenticated and trying to access protected route
  if (!isAuthenticated && !isLoginPage) {
    // Redirect to login page
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Allow the request to proceed
  return NextResponse.next();
}

/**
 * Matcher Configuration
 * 
 * Defines which routes the middleware should run on.
 * 
 * Pattern: Matches all routes except:
 * - /_next/ (Next.js internal files)
 * - /favicon.ico, /robots.txt (static files)
 * - Files with extensions (images, CSS, JS, etc.)
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc.)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\..*|api/auth).*)',
  ],
};
