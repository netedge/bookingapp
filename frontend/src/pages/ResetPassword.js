import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { LockKey, CheckCircle, WarningCircle } from '@phosphor-icons/react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: password,
      });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map(e => e?.msg || JSON.stringify(e)).join('. '));
      } else {
        setError(err.message || 'Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center px-6 py-12">
        <div className="relative w-full max-w-md">
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-8 text-center" data-testid="reset-password-no-token">
            <div className="w-16 h-16 rounded-full bg-orange-50 flex items-center justify-center mx-auto mb-6">
              <WarningCircle className="w-8 h-8 text-orange-600" weight="fill" />
            </div>
            <h1 className="text-2xl font-medium tracking-tight text-indigo-950 mb-3">Invalid Link</h1>
            <p className="text-base text-stone-600 mb-6">This password reset link is invalid or has expired.</p>
            <Link
              to="/forgot-password"
              className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800"
              data-testid="request-new-link"
            >
              Request New Link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center px-6 py-12">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-96 h-96 bg-emerald-700 rounded-full blur-3xl opacity-10"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-sky-600 rounded-full blur-3xl opacity-10"></div>
      </div>

      <div className="relative w-full max-w-md">
        <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-8">
          {success ? (
            <div className="text-center" data-testid="reset-password-success">
              <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-emerald-700" weight="fill" />
              </div>
              <h1 className="text-2xl font-medium tracking-tight text-indigo-950 mb-3">Password Reset!</h1>
              <p className="text-base text-stone-600 mb-2">Your password has been successfully reset.</p>
              <p className="text-sm text-stone-500">Redirecting to sign in...</p>
            </div>
          ) : (
            <>
              <div className="flex flex-col items-center mb-8">
                <div className="w-12 h-12 rounded-xl bg-gradient-emerald flex items-center justify-center mb-4">
                  <LockKey className="w-6 h-6 text-white" weight="bold" />
                </div>
                <h1 className="text-2xl sm:text-3xl font-medium tracking-tight text-indigo-950">Set New Password</h1>
                <p className="text-base text-stone-600 mt-2 text-center">Enter your new password below</p>
              </div>

              {error && (
                <div className="mb-6 p-4 rounded-lg bg-orange-50 border border-orange-200" data-testid="reset-password-error">
                  <p className="text-sm text-orange-800">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} data-testid="reset-password-form">
                <div className="mb-4">
                  <label className="block mb-2 text-sm font-medium text-indigo-950">New Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                    placeholder="Min 6 characters"
                    required
                    minLength={6}
                    data-testid="reset-password-input"
                  />
                </div>

                <div className="mb-6">
                  <label className="block mb-2 text-sm font-medium text-indigo-950">Confirm Password</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                    placeholder="Re-enter password"
                    required
                    minLength={6}
                    data-testid="reset-password-confirm-input"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                  data-testid="reset-password-submit-button"
                >
                  {loading ? 'Resetting...' : 'Reset Password'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
