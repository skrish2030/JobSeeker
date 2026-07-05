'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/utils/supabase/client';

export default function MfaSetupPage() {
  const [qrCodeSvg, setQrCodeSvg] = useState<string>('');
  const [factorId, setFactorId] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    async function setupMFA() {
      try {
        const { data, error } = await supabase.auth.mfa.enroll({ factorType: 'totp' });
        if (error) throw error;
        
        if (data.totp.qr_code) {
          setQrCodeSvg(data.totp.qr_code);
          setFactorId(data.id);
        }
      } catch (e: any) {
        setError(e.message || 'Failed to setup MFA');
      } finally {
        setLoading(false);
      }
    }
    setupMFA();
  }, []);

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
      
      // Successfully enrolled and verified
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
        <h1 className="text-2xl font-bold text-gray-100 mb-2">Secure Your Account</h1>
        <p className="text-gray-400 text-sm mb-6">Scan this QR code with Google Authenticator or Authy to enable Two-Factor Authentication.</p>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
          </div>
        ) : qrCodeSvg ? (
          <div className="flex flex-col items-center gap-6">
            <div 
              className="bg-white p-4 rounded-2xl shadow-lg"
              dangerouslySetInnerHTML={{ __html: qrCodeSvg }} 
            />
            
            <form onSubmit={handleVerify} className="w-full flex flex-col gap-4">
              <input 
                type="text" 
                maxLength={6}
                value={code}
                onChange={e => setCode(e.target.value)}
                placeholder="Enter 6-digit code"
                required
                className="w-full text-center tracking-widest text-xl px-4 py-3.5 bg-[#1A1625] border border-[#ffffff15] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-500 transition-all shadow-inner"
              />
              
              {error && <div className="text-red-400 text-sm font-medium">{error}</div>}

              <button
                type="submit"
                disabled={verifying || code.length !== 6}
                className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {verifying ? 'Verifying...' : 'Enable 2FA'}
              </button>
            </form>
          </div>
        ) : null}
      </div>
    </div>
  );
}
