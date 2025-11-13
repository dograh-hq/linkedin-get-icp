'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';

/**
 * Login Page Component
 * 
 * Simple password-based authentication page for portal access.
 * Password: ______
 * 
 * Features:
 * - Single password field (no username required)
 * - Client-side form submission to /api/auth/login
 * - Sets HTTP-only cookie on successful authentication
 * - Redirects to dashboard on success
 * - Shows error message on failure
 */
export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Handle form submission
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Send password to authentication endpoint
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Authentication successful - store password for API authentication
        sessionStorage.setItem('apiKey', password);
        
        // Redirect to dashboard
        router.push('/');
        router.refresh();
      } else {
        // Authentication failed - show error
        setError(data.error || 'Invalid password');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f5f5f5',
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '40px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '400px',
      }}>
        {/* Header */}
        <h1 style={{
          fontSize: '24px',
          fontWeight: 'bold',
          marginBottom: '8px',
          textAlign: 'center',
        }}>
          LinkedIn Profiling Portal
        </h1>
        <p style={{
          color: '#666',
          marginBottom: '32px',
          textAlign: 'center',
        }}>
          Enter password to access
        </p>

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label htmlFor="password" style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              fontWeight: '500',
            }}>
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoFocus
              style={{
                width: '100%',
                padding: '10px 12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
              }}
              placeholder="Enter password"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              backgroundColor: '#fee',
              color: '#c00',
              padding: '10px',
              borderRadius: '4px',
              marginBottom: '20px',
              fontSize: '14px',
            }}>
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !password}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: loading || !password ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: loading || !password ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
}
