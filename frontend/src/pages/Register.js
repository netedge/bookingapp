import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { UserPlus } from '@phosphor-icons/react';

const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await register(formData.email, formData.password, formData.name);
    setLoading(false);

    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center px-6 py-12">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-600 rounded-full blur-3xl opacity-10"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-orange-600 rounded-full blur-3xl opacity-10"></div>
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-emerald flex items-center justify-center mb-4">
              <UserPlus className="w-6 h-6 text-white" weight="bold" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-medium tracking-tight text-indigo-950">Create Account</h1>
            <p className="text-base text-stone-600 mt-2">Start your free trial today</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-lg bg-orange-50 border border-orange-200" data-testid="register-error">
              <p className="text-sm text-orange-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} data-testid="register-form">
            <div className="mb-4">
              <label className="block mb-2 text-sm font-medium text-indigo-950">Full Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="John Doe"
                required
                data-testid="register-name-input"
              />
            </div>

            <div className="mb-4">
              <label className="block mb-2 text-sm font-medium text-indigo-950">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="you@example.com"
                required
                data-testid="register-email-input"
              />
            </div>

            <div className="mb-6">
              <label className="block mb-2 text-sm font-medium text-indigo-950">Password</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="••••••••"
                required
                data-testid="register-password-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="register-submit-button"
            >
              {loading ? 'Creating account...' : 'Create Account'}
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
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Register;