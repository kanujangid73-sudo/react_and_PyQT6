import { useState } from 'react';
import API from '../api';

export default function Login({ setToken }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      if (isRegister) {
        await API.post('/auth/register', { username, password });
        alert('Registration successful! Please login.');
        setIsRegister(false);
      } else {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        const res = await API.post('/auth/login', formData);
        const token = res.data.access_token;
        localStorage.setItem('token', token);
        setToken(token);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred');
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>{isRegister ? 'Register' : 'Login'}</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>

        <button type="submit" style={{ width: '100%', padding: '10px', cursor: 'pointer' }}>
          {isRegister ? 'Register' : 'Login'}
        </button>
      </form>

      <p 
        onClick={() => setIsRegister(!isRegister)} 
        style={{ cursor: 'pointer', color: 'blue', marginTop: '15px', textAlign: 'center' }}
      >
        {isRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
      </p>
    </div>
  );
}