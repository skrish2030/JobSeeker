'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { signup } from '../login/actions';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  
  // Captcha State
  const [verified, setVerified] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);
  const handleRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verified) {
      setError('Please complete the security swipe.');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const res = await signup(email, password);
      if (res?.error) throw new Error(res.error);
      if (res?.message) {
        setSuccessMsg(res.message);
      } else {
        router.push('/');
        router.refresh();
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Captcha Logic
  const handleDragStart = (e: React.MouseEvent | React.TouchEvent) => {
    if (verified) return;
    setIsDragging(true);
  };

  const handleDragMove = (e: MouseEvent | TouchEvent) => {
    if (!isDragging || verified || !trackRef.current || !handleRef.current) return;
    
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const trackRect = trackRef.current.getBoundingClientRect();
    const handleRect = handleRef.current.getBoundingClientRect();
    
    let newOffset = clientX - trackRect.left - (handleRect.width / 2);
    const maxOffset = trackRect.width - handleRect.width;
    
    if (newOffset < 0) newOffset = 0;
    if (newOffset >= maxOffset) {
      newOffset = maxOffset;
      setVerified(true);
      setIsDragging(false);
    }
    
    setDragOffset(newOffset);
  };

  const handleDragEnd = () => {
    if (!isDragging) return;
    setIsDragging(false);
    if (!verified) {
      setDragOffset(0); // snap back
    }
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleDragMove);
      window.addEventListener('touchmove', handleDragMove, { passive: false });
      window.addEventListener('mouseup', handleDragEnd);
      window.addEventListener('touchend', handleDragEnd);
    }
    return () => {
      window.removeEventListener('mousemove', handleDragMove);
      window.removeEventListener('touchmove', handleDragMove);
      window.removeEventListener('mouseup', handleDragEnd);
      window.removeEventListener('touchend', handleDragEnd);
    };
  }, [isDragging, verified]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#0A0710] to-[#0A0710] p-4 font-sans">
      <div className="w-full max-w-[420px] bg-[#120F1A]/90 backdrop-blur-2xl border border-[#ffffff15] p-8 rounded-3xl shadow-[0_15px_50px_rgba(0,0,0,0.6)]">
        
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 mb-4 rounded-2xl overflow-hidden border border-indigo-500/30 shadow-[0_0_20px_rgba(79,70,229,0.3)] bg-[#1A1625] flex items-center justify-center">
            <Image src="/logo.png" alt="JobSeeker" width={64} height={64} className="object-cover" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100 tracking-wide">Create Account 🚀</h1>
          <p className="text-gray-400 text-sm mt-1">Join JobSeeker today</p>
        </div>

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

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-300 ml-1">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              </div>
              <input 
                type="password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Create a password"
                required
                minLength={6}
                className="w-full pl-10 pr-4 py-3.5 bg-[#1A1625] border border-[#ffffff15] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-500 transition-all shadow-inner"
              />
            </div>
          </div>

          {/* Swipe Captcha */}
          <div 
            ref={trackRef}
            className={`relative w-full h-12 rounded-xl border mt-2 flex items-center justify-center overflow-hidden select-none transition-colors ${verified ? 'bg-green-500/20 border-green-500/40' : 'bg-[#1A1625] border-[#ffffff15]'}`}
          >
            <div 
              className={`absolute top-0 left-0 h-full transition-all ${verified ? 'bg-green-500/30' : 'bg-indigo-500/20'}`} 
              style={{ width: `${dragOffset + 24}px` }}
            />
            
            <span className={`z-0 text-sm font-semibold transition-colors ${verified ? 'text-green-400' : 'text-gray-400'}`}>
              {verified ? 'Verified ✓' : 'Slide to Verify'}
            </span>

            <div
              ref={handleRef}
              onMouseDown={handleDragStart}
              onTouchStart={handleDragStart}
              style={{ transform: `translateX(${dragOffset}px)` }}
              className={`absolute left-1 top-1 w-10 h-10 rounded-lg cursor-grab flex items-center justify-center shadow-lg transition-transform ${isDragging ? 'cursor-grabbing scale-105' : verified ? 'cursor-default' : ''} ${verified ? 'bg-green-500 text-white' : 'bg-[#2A2438] border border-[#ffffff20] text-gray-300 hover:bg-[#322B42]'}`}
            >
              {verified ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
              )}
            </div>
          </div>

          {error && <div className="p-3 mt-1 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center font-medium">{error}</div>}
          {successMsg && <div className="p-3 mt-1 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 text-sm text-center font-medium">{successMsg}</div>}

          <button
            type="submit"
            disabled={loading || !verified}
            className="w-full mt-2 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating Account 🎉🚀
              </>
            ) : 'Create Account'}
          </button>
        </form>
        
        <div className="mt-8 text-center">
          <p className="text-gray-400 text-sm">
            Already have an account?{' '}
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
