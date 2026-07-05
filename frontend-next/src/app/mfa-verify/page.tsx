'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/utils/supabase/client';

export default function MfaVerifyPage() {
  const [factorId, setFactorId] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    async function checkMFA() {
      try {
        const { data: factors, error } = await supabase.auth.mfa.listFactors();
        if (error) throw error;
        
        const totpFactor = factors.totp[0];
        if (!totpFactor) {
          // If they somehow reached here without MFA setup, send them to setup
          router.push('/mfa-setup');
          return;
        }
        
        setFactorId(totpFactor.id);
      } catch (e: any) {
        setError(e.message || 'Failed to load MFA settings');
      } finally {
        setLoading(false);
      }
    }
    checkMFA();
  }, [router, supabase]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerifying(true);
    setError('');

    try {
      const { data, error } = await supabase.auth.mfa.challengeAndVerify({
        factorId,
        code
      });

      if (error) throw error;
      
      // Successfully verified
      router.push('/');
      router.refresh();
    } catch (e: any) {
      setError(e.message || 'Invalid code. Please try again.');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#0A0710] to-[#0A0710] p-4 font-sans">
      <div className="w-full max-w-[420px] bg-[#120F1A]/90 backdrop-blur-2xl border border-[#ffffff15] p-8 rounded-3xl shadow-[0_15px_50px_rgba(0,0,0,0.6)] text-center">
        <h1 className="text-2xl font-bold text-gray-100 mb-2">Two-Factor Authentication</h1>
        <p className="text-gray-400 text-sm mb-8">Enter the 6-digit code from your Authenticator app to continue.</p>

        {loading ? (
          <div className="flex justify-center items-center py-6">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
          </div>
        ) : (
          <form onSubmit={handleVerify} className="w-full flex flex-col gap-5">
            <input 
              type="text" 
              maxLength={6}
              value={code}
              onChange={e => setCode(e.target.value)}
              placeholder="000000"
              required
              className="w-full text-center tracking-[1em] text-2xl font-mono px-4 py-4 bg-[#1A1625] border border-[#ffffff15] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-500/50 transition-all shadow-inner"
            />
            
            {error && <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm font-medium">{error}</div>}

            <button
              type="submit"
              disabled={verifying || code.length !== 6}
              className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {verifying ? 'Verifying...' : 'Verify & Continue'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
