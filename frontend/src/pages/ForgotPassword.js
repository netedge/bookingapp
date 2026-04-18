import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { EnvelopeSimple, ArrowLeft, CheckCircle } from '@phosphor-icons/react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setSent(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
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
          {sent ? (
            <div className="text-center" data-testid="forgot-password-success">
              <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-emerald-700" weight="fill" />
              </div>
              <h1 className="text-2xl font-medium tracking-tight text-indigo-950 mb-3">Check Your Email</h1>
              <p className="text-base text-stone-600 mb-6">
                If an account with <span className="font-medium text-indigo-950">{email}</span> exists, we've sent a password reset link.
              </p>
              <Link
                to="/login"
                className="inline-flex items-center text-sm font-medium text-emerald-700 hover:text-emerald-800"
                data-testid="back-to-login-link"
              >
                <ArrowLeft className="w-4 h-4 mr-1" weight="bold" />
                Back to Sign In
              </Link>
            </div>
          ) : (
            <>
              <div className="flex flex-col items-center mb-8">
                <div className="w-12 h-12 rounded-xl bg-gradient-emerald flex items-center justify-center mb-4">
                  <EnvelopeSimple className="w-6 h-6 text-white" weight="bold" />
                </div>
                <h1 className="text-2xl sm:text-3xl font-medium tracking-tight text-indigo-950">Forgot Password?</h1>
                <p className="text-base text-stone-600 mt-2 text-center">
                  Enter your email and we'll send you a reset link
                </p>
              </div>

              {error && (
                <div className="mb-6 p-4 rounded-lg bg-orange-50 border border-orange-200" data-testid="forgot-password-error">
                  <p className="text-sm text-orange-800">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} data-testid="forgot-password-form">
                <div className="mb-6">
                  <label className="block mb-2 text-sm font-medium text-indigo-950">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                    placeholder="you@example.com"
                    required
                    data-testid="forgot-password-email-input"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                  data-testid="forgot-password-submit-button"
                >
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </button>
              </form>

              <div className="mt-6 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center text-sm text-stone-600 hover:text-indigo-950"
                  data-testid="forgot-password-back-link"
                >
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Back to Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
