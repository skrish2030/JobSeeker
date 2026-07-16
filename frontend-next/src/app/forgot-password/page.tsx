'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Turnstile } from '@marsidev/react-turnstile';
import { createClient } from '@/utils/supabase/client';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Captcha State
  const [verified, setVerified] = useState(false);
  const [captchaToken, setCaptchaToken] = useState('');
  
  const supabase = createClient();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verified) {
      setError('Please complete the security check.');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
        captchaToken: captchaToken
      });
      
      if (resetError) throw new Error(resetError.message);
      
      setSuccess('Verification link sent! Please check your email to reset your password.');
    } catch (err: any) {
      setError(err.message || 'Failed to send password reset email.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#0A0710] to-[#0A0710] p-4 font-sans">
      <div className="w-full max-w-[420px] bg-[#120F1A]/90 backdrop-blur-2xl border border-[#ffffff15] p-8 rounded-3xl shadow-[0_15px_50px_rgba(0,0,0,0.6)]">
        
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 mb-4 rounded-2xl overflow-hidden border border-indigo-500/30 shadow-[0_0_20px_rgba(79,70,229,0.3)] bg-[#1A1625] flex items-center justify-center">
            <Image src="/logo.png" alt="JobSeeker" width={64} height={64} className="object-cover" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100 tracking-wide">Reset Password 🔒</h1>
          <p className="text-gray-400 text-sm mt-1 text-center">Enter your email to receive a password reset link</p>
        </div>

        {success ? (
          <div className="flex flex-col gap-6 text-center">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-400 text-sm font-medium leading-relaxed">
              {success}
            </div>
            <Link
              href="/login"
              className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all text-center shadow-[0_0_15px_rgba(79,70,229,0.3)]"
            >
              Back to Login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-300 ml-1">Email</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" /></svg>
                </div>
                <input 
                  type="email" 
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full pl-10 pr-4 py-3.5 bg-[#1A1625] border border-[#ffffff15] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-500 transition-all shadow-inner"
                />
              </div>
            </div>

            {/* Turnstile Captcha */}
            <div className="flex justify-center mt-2">
              <Turnstile
                siteKey="0x4AAAAAADv0uli2XL9wdroN"
                onSuccess={(token) => {
                  setCaptchaToken(token);
                  setVerified(true);
                }}
                onError={() => {
                  setError("Captcha failed. Please try again.");
                  setVerified(false);
                }}
                onExpire={() => {
                  setVerified(false);
                  setCaptchaToken('');
                }}
                options={{ theme: 'dark' }}
              />
            </div>

            {error && <div className="p-3 mt-1 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center font-medium">{error}</div>}

            <button
              type="submit"
              disabled={loading || !verified}
              className="w-full mt-2 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? 'Sending link...' : 'Send Reset Link'}
            </button>
            
            <div className="text-center mt-2">
              <Link href="/login" className="text-sm text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">
                Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
