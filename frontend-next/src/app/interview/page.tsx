'use client';

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { createClient } from '@/utils/supabase/client';

export default function InterviewPage() {
  const [jobDescription, setJobDescription] = useState('');
  const [savedJobs, setSavedJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [questions, setQuestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeQuestion, setActiveQuestion] = useState(0);
  
  const [userAnswer, setUserAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [feedbacks, setFeedbacks] = useState<Record<number, { score: number, feedback: string }>>({});
  
  const recognitionRef = useRef<any>(null);
  const supabase = createClient();

  useEffect(() => {
    fetchSavedJobs();
  }, []);

  async function fetchSavedJobs() {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const { data } = await supabase
        .from('user_saved_jobs')
        .select(`job_id, jobs (*)`)
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });
        
      if (data) {
        const jobs = data.map((d: any) => d.jobs).filter(Boolean);
        setSavedJobs(jobs);
      }
    }
  }

  const handleJobSelect = (jobId: string) => {
    setSelectedJobId(jobId);
    const job = savedJobs.find(j => j.id === jobId);
    if (job) {
      setJobDescription(job.description || '');
    } else {
      setJobDescription('');
    }
  };

  const speakText = (text: string) => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const msg = new SpeechSynthesisUtterance(text);
      // Optional: adjust voice/pitch
      msg.rate = 1.0;
      window.speechSynthesis.speak(msg);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech Recognition is not supported in this browser. Please use Google Chrome.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setUserAnswer((prev) => prev + (prev ? ' ' : '') + finalTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error', event.error);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognition.start();
    recognitionRef.current = recognition;
    setIsRecording(true);
  };

  const generateQuestions = async () => {
    if (!jobDescription) return;
    setIsLoading(true);

    const provider = localStorage.getItem('ai_provider') || 'gemini';
    const model = localStorage.getItem('ai_model') || 'gemini-2.5-flash';
    const apiKey = localStorage.getItem('ai_api_key') || localStorage.getItem('gemini_api_key') || '';

    try {
      const response = await fetch('/api/ai/interview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jobDescription, provider, model, apiKey })
      });
      const data = await response.json();
      if (response.status !== 200) throw new Error(data.error);
      
      setQuestions(data.questions);
      setActiveQuestion(0);
      setUserAnswer('');
      setFeedbacks({});
      
      // AI speaks the first question
      speakText("Let's begin. " + data.questions[0]);
    } catch (e) {
      console.error(e);
      alert('Failed to generate questions.');
    } finally {
      setIsLoading(false);
    }
  };

  const changeQuestion = (idx: number) => {
    setActiveQuestion(idx);
    setUserAnswer('');
    speakText(questions[idx]);
  };

  const submitAnswer = async () => {
    if (!userAnswer) return;
    setIsEvaluating(true);

    const provider = localStorage.getItem('ai_provider') || 'gemini';
    const model = localStorage.getItem('ai_model') || 'gemini-2.5-flash';
    const apiKey = localStorage.getItem('ai_api_key') || localStorage.getItem('gemini_api_key') || '';

    try {
      const response = await fetch('/api/ai/interview/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: questions[activeQuestion], 
          userAnswer, 
          jobDescription, 
          provider, 
          model, 
          apiKey 
        })
      });
      const data = await response.json();
      if (response.status !== 200) throw new Error(data.error);

      setFeedbacks(prev => ({ ...prev, [activeQuestion]: data }));
      
      // AI speaks the feedback
      speakText(`You scored ${data.score} out of 10. ${data.feedback}`);
      
    } catch (e) {
      console.error(e);
      alert('Failed to get feedback.');
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">AI Interview Assistant</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0A0710] to-[#0A0710]">
        <div className="max-w-4xl mx-auto">
          {!questions.length ? (
            <div className="bg-[#15121E] border border-[#ffffff10] p-8 rounded-3xl shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
              
              <div className="mb-8 text-center relative z-10">
                <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(99,102,241,0.4)]">
                  <span className="text-4xl">🎙️</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-100 mb-2">Practice for your next role</h3>
                <p className="text-gray-400">Select a saved job or paste the description below. I will act as the hiring manager and conduct a voice-enabled mock interview!</p>
              </div>

              <div className="space-y-4 relative z-10 mb-6">
                {savedJobs.length > 0 && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">Select a Saved Job</label>
                    <select 
                      value={selectedJobId}
                      onChange={(e) => handleJobSelect(e.target.value)}
                      className="w-full bg-[#0A0710] border border-[#ffffff15] rounded-xl px-4 py-3 text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-colors appearance-none"
                    >
                      <option value="">-- Paste Custom Description Below --</option>
                      {savedJobs.map(job => (
                        <option key={job.id} value={job.id}>{job.title} at {job.company}</option>
                      ))}
                    </select>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-semibold text-gray-300 mb-2">Job Description Context</label>
                  <textarea 
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the full job description here..."
                    className="w-full h-48 bg-[#0A0710] border border-[#ffffff10] rounded-xl p-4 text-gray-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none resize-none"
                  />
                </div>
              </div>

              <button 
                onClick={generateQuestions}
                disabled={isLoading || !jobDescription}
                className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 disabled:from-[#ffffff05] disabled:to-[#ffffff05] text-white font-bold rounded-xl transition-all shadow-lg flex justify-center items-center gap-2 relative z-10"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-t-white border-white/20 rounded-full animate-spin"></div>
                    Preparing Interview Panel...
                  </>
                ) : (
                  'Start Mock Interview ✨'
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-500">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-gray-200">Mock Interview Session</h3>
                <div className="flex gap-3">
                  <button 
                    onClick={() => {
                      window.speechSynthesis.cancel();
                      setQuestions([]);
                    }}
                    className="px-4 py-2 bg-[#ffffff05] hover:bg-[#ffffff10] border border-[#ffffff10] rounded-lg text-sm font-semibold text-gray-300 transition-colors"
                  >
                    End Session
                  </button>
                </div>
              </div>

              {questions.map((q, idx) => (
                <div 
                  key={idx} 
                  className={`bg-[#15121E] border ${idx === activeQuestion ? 'border-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.2)]' : 'border-[#ffffff10] opacity-60'} p-8 rounded-3xl transition-all ${idx !== activeQuestion && 'cursor-pointer'}`}
                  onClick={() => { if (idx !== activeQuestion) changeQuestion(idx); }}
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold shrink-0 ${idx === activeQuestion ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white' : 'bg-[#ffffff05] text-gray-500'}`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-start gap-4">
                        <h4 className={`text-lg ${idx === activeQuestion ? 'text-gray-100 font-bold' : 'text-gray-400 font-medium'}`}>{q}</h4>
                        {idx === activeQuestion && (
                          <button onClick={() => speakText(q)} className="p-2 bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 rounded-lg transition-colors shrink-0" title="Read Aloud">
                            🔊
                          </button>
                        )}
                      </div>

                      {idx === activeQuestion && (
                        <div className="mt-6 space-y-4">
                          <div className="relative">
                            <textarea 
                              value={userAnswer}
                              onChange={(e) => setUserAnswer(e.target.value)}
                              placeholder="Type your answer here, or click the mic to speak..."
                              className="w-full h-32 bg-[#0A0710] border border-[#ffffff10] rounded-xl p-4 pr-16 text-gray-300 focus:border-indigo-500 outline-none resize-none transition-colors"
                            />
                            <button 
                              onClick={toggleRecording}
                              className={`absolute bottom-4 right-4 p-3 rounded-full shadow-lg transition-all ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-indigo-600 hover:bg-indigo-500 text-white'}`}
                              title={isRecording ? 'Stop Recording' : 'Start Recording'}
                            >
                              🎤
                            </button>
                          </div>
                          
                          {feedbacks[idx] ? (
                            <div className="p-6 bg-gradient-to-br from-indigo-900/40 to-purple-900/40 border border-indigo-500/30 rounded-2xl">
                              <div className="flex items-center gap-3 mb-2">
                                <span className={`text-2xl font-black ${feedbacks[idx].score >= 8 ? 'text-green-400' : feedbacks[idx].score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
                                  {feedbacks[idx].score}/10
                                </span>
                                <h5 className="font-bold text-gray-200">AI Feedback</h5>
                              </div>
                              <p className="text-gray-300 leading-relaxed">{feedbacks[idx].feedback}</p>
                            </div>
                          ) : (
                            <div className="flex justify-end">
                              <button 
                                onClick={submitAnswer}
                                disabled={isEvaluating || !userAnswer}
                                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold rounded-xl transition-colors shadow-lg flex items-center gap-2"
                              >
                                {isEvaluating ? 'Evaluating...' : 'Submit Answer'}
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
