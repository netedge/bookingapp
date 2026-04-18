import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserPlus } from '@phosphor-icons/react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Register = () => {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    business_name: '',
    subdomain: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubdomainChange = (value) => {
    const cleaned = value.toLowerCase().replace(/[^a-z0-9-]/g, '');
    setFormData((prev) => ({ ...prev, subdomain: cleaned }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await axios.post(
        `${API}/auth/register-tenant`,
        formData,
        { withCredentials: true }
      );
      await checkAuth();
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const update = (field, value) => setFormData((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center px-6 py-12">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-600 rounded-full blur-3xl opacity-10"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-orange-600 rounded-full blur-3xl opacity-10"></div>
      </div>

      <div className="relative w-full max-w-lg">
        <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-emerald flex items-center justify-center mb-4">
              <UserPlus className="w-6 h-6 text-white" weight="bold" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-medium tracking-tight text-indigo-950">Create Your Venue</h1>
            <p className="text-base text-stone-600 mt-2">Start managing bookings in minutes</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-lg bg-orange-50 border border-orange-200" data-testid="register-error">
              <p className="text-sm text-orange-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} data-testid="register-form">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block mb-2 text-sm font-medium text-indigo-950">Your Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => update('name', e.target.value)}
                  className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                  placeholder="John Doe"
                  required
                  data-testid="register-name-input"
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium text-indigo-950">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => update('email', e.target.value)}
                  className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                  placeholder="you@example.com"
                  required
                  data-testid="register-email-input"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block mb-2 text-sm font-medium text-indigo-950">Password</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => update('password', e.target.value)}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="Min 6 characters"
                required
                minLength={6}
                data-testid="register-password-input"
              />
            </div>

            <hr className="my-5 border-stone-200" />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block mb-2 text-sm font-medium text-indigo-950">Business Name</label>
                <input
                  type="text"
                  value={formData.business_name}
                  onChange={(e) => update('business_name', e.target.value)}
                  className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                  placeholder="Champions Arena"
                  required
                  data-testid="register-business-name-input"
                />
              </div>
              <div>
                <label className="block mb-2 text-sm font-medium text-indigo-950">Subdomain</label>
                <input
                  type="text"
                  value={formData.subdomain}
                  onChange={(e) => handleSubdomainChange(e.target.value)}
                  className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                  placeholder="champions"
                  required
                  data-testid="register-subdomain-input"
                />
                <p className="text-xs text-stone-500 mt-1">{formData.subdomain || 'your-venue'}.spancle.com</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="register-submit-button"
            >
              {loading ? 'Creating your venue...' : 'Create Account & Venue'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-stone-600">
              Already have an account?{' '}
              <Link to="/login" className="text-emerald-700 hover:text-emerald-800 font-medium" data-testid="login-link">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link to="/" className="text-sm text-stone-500 hover:text-indigo-950" data-testid="back-home-link">
            &larr; Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
