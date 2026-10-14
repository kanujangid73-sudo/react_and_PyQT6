import { useState } from 'react';
import API from '../api';

export default function InquiryForm({ onInquiryCreated }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    number: '',
    company: '',
    subject: '',
    msg: '',
    purpose: 'General',
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await API.post('/inquiries/', formData);
      alert('Inquiry submitted successfully!');
      setFormData({ name: '', email: '', number: '', company: '', subject: '', msg: '', purpose: 'General' });
      onInquiryCreated();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit inquiry');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
      <h3>Create New Inquiry</h3>
      <input name="name" placeholder="Name" value={formData.name} onChange={handleChange} required style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }} />
      <input name="email" type="email" placeholder="Email" value={formData.email} onChange={handleChange} required style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }} />
      <input name="number" placeholder="Phone Number" value={formData.number} onChange={handleChange} required style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }} />
      <input name="company" placeholder="Company" value={formData.company} onChange={handleChange} required style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }} />
      <input name="subject" placeholder="Subject" value={formData.subject} onChange={handleChange} required style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }} />
      <select name="purpose" value={formData.purpose} onChange={handleChange} style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px' }}>
        <option value="General">General</option>
        <option value="Sales">Sales</option>
        <option value="Support">Support</option>
      </select>
      <textarea name="msg" placeholder="Message" value={formData.msg} onChange={handleChange} required style={{ display: 'block', marginBottom: '10px', width: '100%', padding: '8px', minHeight: '80px' }} />
      <button type="submit" style={{ padding: '10px 20px', cursor: 'pointer' }}>Submit Inquiry</button>
    </form>
  );
}