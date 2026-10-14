import React, { useState } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      setSuccess(data.message || 'Account created successfully!');
      setUsername('');
      setPassword('');
    } catch (err) {
      console.error('Registration Error:', err);
      if (err.message === 'Failed to fetch') {
        setError('Cannot connect to backend server. Make sure uvicorn is running on port 8000.');
      } else {
        setError(err.message || 'Registration failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '360px', margin: '50px auto', padding: '24px', border: '1px solid #e0e0e0', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
      <h2 style={{ textAlign: 'center', marginTop: 0 }}>Register</h2>
      
      {error && <div style={{ color: '#d32f2f', backgroundColor: '#fde8e8', padding: '10px', borderRadius: '4px', marginBottom: '14px', fontSize: '14px', textAlign: 'center' }}>{error}</div>}
      {success && <div style={{ color: '#2e7d32', backgroundColor: '#edf7ed', padding: '10px', borderRadius: '4px', marginBottom: '14px', fontSize: '14px', textAlign: 'center' }}>{success}</div>}

      <form onSubmit={handleRegister}>
        <div style={{ marginBottom: '14px' }}>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px' }}>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
            required
          />
        </div>

        <div style={{ marginBottom: '18px' }}>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px' }}>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
            required
          />
        </div>

        <button 
          type="submit" 
          disabled={loading}
          style={{ width: '100%', padding: '10px', backgroundColor: '#1976d2', color: '#ffffff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
    </div>
  );
}