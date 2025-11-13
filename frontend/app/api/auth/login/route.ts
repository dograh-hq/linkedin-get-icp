import { NextRequest, NextResponse } from 'next/server';

/**
 * Authentication API Route (Frontend Proxy)
 * 
 * POST /api/auth/login
 * 
 * Proxies authentication to backend FastAPI server.
 * Backend validates password against PORTAL_PASSWORD env variable.
 * 
 * Request Body:
 * {
 *   "password": string
 * }
 * 
 * Success Response (200):
 * {
 *   "success": true,
 *   "message": "Authentication successful"
 * }
 * Sets HTTP-only cookie "auth_token" with value "authenticated"
 * 
 * Error Response (401):
 * {
 *   "success": false,
 *   "error": "Invalid password"
 * }
 * 
 * Note: Password validation happens on backend (localhost:8000)
 * Password must be set in backend/.env: PORTAL_PASSWORD=your-password-here
 */

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body = await request.json();
    const { password } = body;

    // Validate password exists
    if (!password) {
      return NextResponse.json(
        { success: false, error: 'Password is required' },
        { status: 400 }
      );
    }

    // Call backend authentication endpoint
    // Use server-side env variable (not NEXT_PUBLIC_* which is for client-side)
    const apiEndpoint = process.env.API_ENDPOINT || 'http://localhost:8000';
    const backendResponse = await fetch(`${apiEndpoint}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ password }),
    });

    const backendData = await backendResponse.json();

    // Check if backend authentication succeeded
    if (backendResponse.ok && backendData.success) {
      // Authentication successful - create response with cookie
      const response = NextResponse.json({
        success: true,
        message: 'Authentication successful',
      });

      // Set HTTP-only secure cookie
      // Cookie expires in 7 days
      response.cookies.set('auth_token', 'authenticated', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days in seconds
        path: '/',
      });

      return response;
    } else {
      // Authentication failed - pass through backend error
      return NextResponse.json(
        { success: false, error: backendData.detail || backendData.error || 'Invalid password' },
        { status: backendResponse.status }
      );
    }
  } catch (error) {
    // Handle unexpected errors (e.g., backend not running)
    console.error('Authentication error:', error);
    return NextResponse.json(
      { success: false, error: 'Authentication service unavailable. Make sure backend is running.' },
      { status: 500 }
    );
  }
}
