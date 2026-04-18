import React, { useState, useEffect, useCallback } from 'react';
import { X } from '@phosphor-icons/react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CreateVenueModal = ({ isOpen, onClose, onSuccess }) => {
  const { user } = useAuth();
  const [tenants, setTenants] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    address: '',
    image_url: '',
    tenant_id: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchTenants = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/tenants`, { withCredentials: true });
      setTenants(data);
    } catch (err) {
      // silently ignore
    }
  }, []);

  useEffect(() => {
    if (isOpen && user?.role === 'super_admin') {
      fetchTenants();
    }
  }, [isOpen, user, fetchTenants]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = { ...formData };
      if (!payload.image_url) {
        payload.image_url = 'https://images.unsplash.com/photo-1765124540460-b884e248ac2b';
      }
      
      await axios.post(`${API}/venues`, payload, { withCredentials: true });
      onSuccess();
      onClose();
      setFormData({ name: '', description: '', address: '', image_url: '', tenant_id: '' });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create venue');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" data-testid="create-venue-modal">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-stone-200 flex items-center justify-between sticky top-0 bg-white">
          <h2 className="text-2xl font-semibold text-indigo-950">Create New Venue</h2>
          <button onClick={onClose} className="p-2 hover:bg-stone-100 rounded-lg transition-colors" data-testid="close-modal-button">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <p className="text-sm text-orange-800">{error}</p>
            </div>
          )}

          {user?.role === 'super_admin' && (
            <div className="mb-4">
              <label className="block mb-2 text-sm font-medium text-indigo-950">Tenant</label>
              <select
                value={formData.tenant_id}
                onChange={(e) => setFormData({ ...formData, tenant_id: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                required
                data-testid="tenant-select"
              >
                <option value="">Select a tenant</option>
                {tenants.map((tenant) => (
                  <option key={tenant.id} value={tenant.id}>
                    {tenant.business_name} ({tenant.subdomain})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium text-indigo-950">Venue Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              placeholder="Downtown Sports Complex"
              required
              data-testid="venue-name-input"
            />
          </div>

          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium text-indigo-950">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              placeholder="Premier sports facility in the heart of the city"
              rows="3"
              required
              data-testid="venue-description-input"
            />
          </div>

          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium text-indigo-950">Address</label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              placeholder="123 Main St, City, State 12345"
              required
              data-testid="venue-address-input"
            />
          </div>

          <div className="mb-4">
            <label className="block mb-2 text-sm font-medium text-indigo-950">Image URL (optional)</label>
            <input
              type="url"
              value={formData.image_url}
              onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              placeholder="https://example.com/image.jpg"
              data-testid="venue-image-input"
            />
          </div>

          <div className="flex items-center justify-end space-x-4 mt-6">
            <button type="button" onClick={onClose} className="px-6 py-3 text-sm font-medium transition-all bg-white border border-stone-200 text-indigo-950 rounded-xl hover:bg-stone-50" data-testid="cancel-button">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 disabled:opacity-50" data-testid="submit-button">
              {loading ? 'Creating...' : 'Create Venue'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateVenueModal;
