import { useEffect, useState } from 'react';
import API from '../api';

export default function InquiryList({ setToken }) {
  const [inquiries, setInquiries] = useState([]);

  const fetchInquiries = async () => {
    try {
      const res = await API.get('/inquiries/');
      setInquiries(res.data);
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout();
      }
    }
  };

  useEffect(() => {
    fetchInquiries();
  }, []);

  const handleStatusChange = async (id, status) => {
    try {
      await API.patch(`/inquiries/${id}`, { status });
      fetchInquiries();
    } catch (err) {
      alert('Failed to update status');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Inquiries List</h2>
        <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer' }}>Logout</button>
      </div>

      <table border="1" cellPadding="10" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Number</th>
            <th>Company</th>
            <th>Subject</th>
            <th>Message</th>
            <th>Purpose</th>
            <th>Date</th>
            <th>Time</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {inquiries.map((inq) => (
            <tr key={inq.id}>
              <td>{inq.id}</td>
              <td>{inq.name}</td>
              <td>{inq.email}</td>
              <td>{inq.number}</td>
              <td>{inq.company}</td>
              <td>{inq.subject}</td>
              <td>{inq.msg}</td>
              <td>{inq.purpose}</td>
              <td>{inq.data}</td>
              <td>{inq.time}</td>
              <td>
                <select value={inq.status} onChange={(e) => handleStatusChange(inq.id, e.target.value)}>
                  <option value="Pending">Pending</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}