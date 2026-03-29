import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { SignIn } from '@phosphor-icons/react';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(email, password);
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
        <div className="absolute top-0 left-0 w-96 h-96 bg-emerald-700 rounded-full blur-3xl opacity-10"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-sky-600 rounded-full blur-3xl opacity-10"></div>
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-emerald flex items-center justify-center mb-4">
              <SignIn className="w-6 h-6 text-white" weight="bold" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-medium tracking-tight text-indigo-950">Welcome Back</h1>
            <p className="text-base text-stone-600 mt-2">Sign in to your Kelika account</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-lg bg-orange-50 border border-orange-200" data-testid="login-error">
              <p className="text-sm text-orange-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} data-testid="login-form">
            <div className="mb-4">
              <label className="block mb-2 text-sm font-medium text-indigo-950">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="you@example.com"
                required
                data-testid="login-email-input"
              />
            </div>

            <div className="mb-6">
              <label className="block mb-2 text-sm font-medium text-indigo-950">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="••••••••"
                required
                data-testid="login-password-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="login-submit-button"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-stone-600">
              Don't have an account?{' '}
              <Link to="/register" className="text-emerald-700 hover:text-emerald-800 font-medium" data-testid="register-link">
                Sign up
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

export default Login;