'use client';

import { useState, useRef, useEffect } from 'react';
import { chatWithInterviewer } from './actions';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';

type Message = { role: 'user' | 'assistant', content: string };

export default function InterviewPage() {
  const [jobDescription, setJobDescription] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    setMessages([{ role: 'assistant', content: "Hello! I will be your interviewer today. Are you ready to begin?" }]);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setInput('');
    const newMessages = [...messages, { role: 'user' as const, content: userMsg }];
    setMessages(newMessages);
    setLoading(true);
    setError('');

    try {
      const response = await chatWithInterviewer(newMessages, jobDescription);
      setMessages([...newMessages, { role: 'assistant', content: response.text }]);
    } catch (err: any) {
      if (err.message.includes('API_KEY_MISSING')) {
        setError('Please configure your Gemini API Key in the Settings tab first.');
      } else {
        setError(err.message);
      }
      // Revert user message on error
      setMessages(messages);
      setInput(userMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 flex items-center gap-2">
          <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
          Mock Interview Assistant
        </h2>
      </header>

      <div className="flex-1 overflow-hidden flex flex-col p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0A0710] to-[#0A0710]">
        <div className="max-w-5xl mx-auto w-full h-full flex flex-col gap-6">
          
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm shrink-0">
              {error}
              {error.includes('Settings tab') && (
                <Link href="/settings" className="block mt-2 underline font-bold">Go to Settings</Link>
              )}
            </div>
          )}

          {messages.length === 0 ? (
            <div className="flex-1 bg-[#120F1A]/80 backdrop-blur-xl border border-[#ffffff15] p-8 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] flex flex-col justify-center max-w-2xl mx-auto w-full">
              <div className="text-center mb-8">
                <div className="w-20 h-20 bg-indigo-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-indigo-500/30">
                  <svg className="w-10 h-10 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-100 mb-2">Start a Mock Interview</h3>
                <p className="text-gray-400">Provide the job description you are interviewing for, and our AI will simulate a realistic technical interview.</p>
              </div>

              <form onSubmit={handleStart} className="flex flex-col gap-4">
                <textarea
                  required
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  className="w-full min-h-[150px] p-4 bg-[#1A1625] border border-[#ffffff10] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-600 transition-all resize-none shadow-inner"
                  placeholder="Paste the job description here..."
                />
                <button
                  type="submit"
                  className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.4)]"
                >
                  Start Interview
                </button>
              </form>
            </div>
          ) : (
            <div className="flex-1 flex flex-col bg-[#120F1A]/80 backdrop-blur-xl border border-[#ffffff15] rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] overflow-hidden">
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-2xl p-5 ${
                      msg.role === 'user' 
                        ? 'bg-indigo-600 text-white rounded-br-none' 
                        : 'bg-[#1A1625] border border-[#ffffff10] text-gray-200 rounded-bl-none prose prose-invert'
                    }`}>
                      {msg.role === 'assistant' ? (
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      ) : (
                        msg.content
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-[#1A1625] border border-[#ffffff10] rounded-2xl rounded-bl-none p-5 flex items-center gap-2 text-gray-400">
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-4 bg-[#15121E] border-t border-[#ffffff10]">
                <form onSubmit={handleSend} className="flex gap-2 relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={loading}
                    placeholder="Type your answer..."
                    className="flex-1 bg-[#1A1625] border border-[#ffffff10] rounded-xl pl-4 pr-12 py-4 outline-none focus:border-indigo-500/50 text-gray-100 placeholder-gray-600 transition-all shadow-inner disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="absolute right-2 top-2 bottom-2 aspect-square bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
