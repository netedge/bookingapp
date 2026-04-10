import React, { useState } from 'react';
import { X } from '@phosphor-icons/react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CreateTenantModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    business_name: '',
    subdomain: '',
    admin_email: '',
    admin_password: '',
    admin_name: '',
    timezone: 'UTC',
    currency: 'USD'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await axios.post(`${API}/tenants`, formData, { withCredentials: true });
      onSuccess();
      onClose();
      setFormData({
        business_name: '',
        subdomain: '',
        admin_email: '',
        admin_password: '',
        admin_name: '',
        timezone: 'UTC',
        currency: 'USD'
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create tenant');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" data-testid="create-tenant-modal">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-stone-200 flex items-center justify-between sticky top-0 bg-white">
          <h2 className="text-2xl font-semibold text-indigo-950">Create New Tenant</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-stone-100 rounded-lg transition-colors"
            data-testid="close-modal-button"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <p className="text-sm text-orange-800">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Business Name</label>
              <input
                type="text"
                value={formData.business_name}
                onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="Champions Arena"
                required
                data-testid="business-name-input"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Subdomain</label>
              <input
                type="text"
                value={formData.subdomain}
                onChange={(e) => setFormData({ ...formData, subdomain: e.target.value.toLowerCase() })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="champions"
                required
                data-testid="subdomain-input"
              />
              <p className="text-xs text-stone-500 mt-1">URL: {formData.subdomain || 'subdomain'}.spancle.com</p>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Admin Name</label>
              <input
                type="text"
                value={formData.admin_name}
                onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="John Doe"
                required
                data-testid="admin-name-input"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Admin Email</label>
              <input
                type="email"
                value={formData.admin_email}
                onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="admin@champions.com"
                required
                data-testid="admin-email-input"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Admin Password</label>
              <input
                type="password"
                value={formData.admin_password}
                onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="••••••••"
                required
                minLength="6"
                data-testid="admin-password-input"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Timezone</label>
              <select
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                data-testid="timezone-select"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
              </select>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                data-testid="currency-select"
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="INR">INR (₹)</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end space-x-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-3 text-sm font-medium transition-all bg-white border border-stone-200 text-indigo-950 rounded-xl hover:bg-stone-50"
              data-testid="cancel-button"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 disabled:opacity-50"
              data-testid="submit-button"
            >
              {loading ? 'Creating...' : 'Create Tenant'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTenantModal;