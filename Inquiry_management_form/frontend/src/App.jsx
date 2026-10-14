import React, { useState } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [view, setView] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [inquiries, setInquiries] = useState([]);
  const [clientName, setClientName] = useState('');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Registration failed');
      setMessage('Registration successful! Please login.');
      setView('login');
    } catch (err) {
      setMessage(err.message === 'Failed to fetch' ? 'Backend server is offline! Start uvicorn.' : err.message);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      setView('dashboard');
      fetchInquiries(data.access_token);
    } catch (err) {
      setMessage(err.message === 'Failed to fetch' ? 'Backend server is offline!' : err.message);
    }
  };

  const fetchInquiries = async (authToken = token) => {
    try {
      const res = await fetch(`${API_BASE}/inquiries`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      const data = await res.json();
      if (res.ok) setInquiries(data.inquiries || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateInquiry = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/inquiries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ client_name: clientName, subject, description })
      });
      if (res.ok) {
        setClientName('');
        setSubject('');
        setDescription('');
        fetchInquiries();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateStatus = async (id) => {
    try {
      await fetch(`${API_BASE}/inquiries/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: 'Resolved' })
      });
      fetchInquiries();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteInquiry = async (id) => {
    try {
      await fetch(`${API_BASE}/inquiries/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchInquiries();
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    setView('login');
  };

  return (
    <div className="min-h-screen bg-slate-100 py-10 px-4 text-slate-800">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <header className="bg-slate-900 text-white p-6 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">Inquiry System</h1>
            <p className="text-xs text-slate-400">FastAPI & React Dashboard</p>
          </div>
          {token && (
            <button onClick={handleLogout} className="px-4 py-1.5 text-xs font-semibold bg-red-500 hover:bg-red-600 text-white rounded-lg transition">
              Logout
            </button>
          )}
        </header>

        <div className="p-6">
          {message && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm font-medium">
              {message}
            </div>
          )}

          {/* LOGIN VIEW */}
          {view === 'login' && !token && (
            <form onSubmit={handleLogin} className="space-y-4 max-w-sm mx-auto py-4">
              <h2 className="text-2xl font-bold text-center text-slate-900 mb-6">Account Login</h2>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Username</label>
                <input type="text" value={username} onChange={e => setUsername(e.target.value)} required className="w-full px-4 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Enter username" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full px-4 py-2 border rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" placeholder="••••••••" />
              </div>
              <button type="submit" className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-md transition">Login</button>
              <p className="text-sm text-center text-slate-600 mt-4 cursor-pointer hover:underline" onClick={() => setView('register')}>Need an account? <span className="text-blue-600 font-semibold">Register</span></p>
            </form>
          )}

          {/* REGISTER VIEW */}
          {view === 'register' && !token && (
            <form onSubmit={handleRegister} className="space-y-4 max-w-sm mx-auto py-4">
              <h2 className="text-2xl font-bold text-center text-slate-900 mb-6">Create Account</h2>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Username</label>
                <input type="text" value={username} onChange={e => setUsername(e.target.value)} required className="w-full px-4 py-2 border rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none" placeholder="Choose username" />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full px-4 py-2 border rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none" placeholder="••••••••" />
              </div>
              <button type="submit" className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl shadow-md transition">Register</button>
              <p className="text-sm text-center text-slate-600 mt-4 cursor-pointer hover:underline" onClick={() => setView('login')}>Already registered? <span className="text-blue-600 font-semibold">Login</span></p>
            </form>
          )}

          {/* DASHBOARD VIEW */}
          {token && (
            <div className="space-y-8">
              <form onSubmit={handleCreateInquiry} className="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-3">
                <h3 className="text-md font-bold text-slate-900 border-b pb-2">Add New Inquiry</h3>
                <input type="text" placeholder="Client Name" value={clientName} onChange={e => setClientName(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-sm outline-none" />
                <input type="text" placeholder="Subject" value={subject} onChange={e => setSubject(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-sm outline-none" />
                <textarea placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} required className="w-full px-3 py-2 border rounded-lg text-sm outline-none h-20"></textarea>
                <button type="submit" className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white font-medium text-sm rounded-lg transition">Submit Inquiry</button>
              </form>

              <div>
                <h3 className="text-md font-bold text-slate-900 mb-4">Inquiry Database</h3>
                {inquiries.length === 0 ? (
                  <p className="text-slate-500 text-sm italic">No inquiries found in database.</p>
                ) : (
                  <div className="space-y-3">
                    {inquiries.map((item) => (
                      <div key={item.id} className="p-4 border rounded-xl flex justify-between items-center bg-white shadow-sm">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-bold text-slate-800">{item.client_name}</h4>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${item.status === 'Resolved' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                              {item.status}
                            </span>
                          </div>
                          <p className="text-sm font-medium text-slate-600 mt-1">{item.subject}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{item.description}</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => handleUpdateStatus(item.id)} className="px-3 py-1 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200 text-xs font-semibold rounded-lg transition">
                            Resolve
                          </button>
                          <button onClick={() => handleDeleteInquiry(item.id)} className="px-3 py-1 bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 text-xs font-semibold rounded-lg transition">
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}