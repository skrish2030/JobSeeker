'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const DEFAULT_RESUME = `# Jane Doe
Software Engineer | New York, NY | jane.doe@example.com

## Professional Summary
Passionate software engineer with 5 years of experience building scalable web applications.

## Experience

### Senior Developer at TechCorp
*Jan 2020 - Present*
- Built the backend API using Node.js
- Managed a team of 3 developers

### Web Developer at WebSolutions
*Jun 2017 - Dec 2019*
- Created front-end features using React
- Optimized database queries

## Education
**B.S. Computer Science** - University of Technology, 2017

## Skills
JavaScript, React, Node.js, SQL, AWS
`;

export default function ResumeBuilderPage() {
  const [markdown, setMarkdown] = useState(DEFAULT_RESUME);
  const [isPolishing, setIsPolishing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load from local storage
  useEffect(() => {
    const saved = localStorage.getItem('resume_markdown');
    if (saved) setMarkdown(saved);
  }, []);

  // Save to local storage
  useEffect(() => {
    if (markdown !== DEFAULT_RESUME) {
      localStorage.setItem('resume_markdown', markdown);
    }
  }, [markdown]);

  const handleDownloadPDF = () => {
    window.print();
  };

  const handleAIPolish = async () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = markdown.substring(start, end);

    if (!selectedText || selectedText.trim().length < 5) {
      alert("Please highlight at least a few words to polish!");
      return;
    }

    setIsPolishing(true);
    const provider = localStorage.getItem('ai_provider') || 'gemini';
    const model = localStorage.getItem('ai_model') || 'gemini-2.5-flash';
    const apiKey = localStorage.getItem('ai_api_key') || localStorage.getItem('gemini_api_key') || '';

    try {
      const response = await fetch('/api/ai/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: selectedText, provider, model, apiKey })
      });
      const data = await response.json();
      if (response.status !== 200) throw new Error(data.error);

      const newText = markdown.substring(0, start) + data.result + markdown.substring(end);
      setMarkdown(newText);
      
    } catch (e: any) {
      console.error(e);
      alert(`AI Polish failed: ${e.message}`);
    } finally {
      setIsPolishing(false);
      textarea.focus();
    }
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
          body * {
            visibility: hidden;
          }
          #resume-preview, #resume-preview * {
            visibility: visible;
          }
          #resume-preview {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            margin: 0;
            padding: 0;
            background: white !important;
            color: black !important;
          }
          /* Print typography styling */
          #resume-preview h1 { font-size: 24pt; margin-bottom: 4pt; }
          #resume-preview h2 { font-size: 14pt; border-bottom: 1px solid black; margin-top: 12pt; margin-bottom: 6pt; }
          #resume-preview h3 { font-size: 12pt; margin-top: 8pt; margin-bottom: 2pt; }
          #resume-preview p, #resume-preview li { font-size: 10pt; line-height: 1.4; }
          #resume-preview ul { margin-top: 2pt; margin-bottom: 6pt; padding-left: 20pt; }
        }
      `}} />

      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex justify-between items-center sticky top-0 z-10 shrink-0 print:hidden">
        <div>
          <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Premium Resume Builder</h2>
          <p className="text-sm text-gray-400">Zero-cost local preview. Use AI only when you need it.</p>
        </div>
        <div className="flex gap-4">
          <button 
            onClick={handleDownloadPDF}
            className="px-6 py-2 bg-white text-black font-bold rounded-xl hover:bg-gray-200 transition-colors shadow-lg flex items-center gap-2"
          >
            📄 Export to PDF
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden bg-[#0A0710] print:hidden">
        {/* Editor Pane */}
        <div className="w-full md:w-1/2 h-full border-r border-[#ffffff10] flex flex-col bg-[#15121E]">
          <div className="p-4 border-b border-[#ffffff10] flex justify-between items-center bg-[#1A1625]">
            <h3 className="font-bold text-gray-200 flex items-center gap-2"><span>✏️</span> Markdown Editor</h3>
            <button 
              onClick={handleAIPolish}
              disabled={isPolishing}
              title="Highlight text in the editor and click this to rewrite it professionally"
              className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 disabled:opacity-50 text-white text-sm font-bold rounded-lg transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] flex items-center gap-2"
            >
              {isPolishing ? 'Polishing...' : '✨ AI Polish Selection'}
            </button>
          </div>
          <textarea
            ref={textareaRef}
            value={markdown}
            onChange={(e) => setMarkdown(e.target.value)}
            className="flex-1 w-full bg-transparent p-6 text-gray-300 font-mono text-sm resize-none outline-none focus:ring-1 focus:ring-emerald-500/50"
            placeholder="Type your resume in Markdown format..."
          />
        </div>

        {/* Live Preview Pane */}
        <div className="w-full md:w-1/2 h-full overflow-y-auto bg-gray-100 p-8 flex justify-center">
          <div 
            id="resume-preview" 
            className="w-full max-w-[800px] min-h-[1056px] bg-white text-black p-12 shadow-2xl rounded-sm"
          >
            <div className="prose prose-sm max-w-none prose-h1:text-3xl prose-h1:mb-2 prose-h2:border-b prose-h2:border-gray-300 prose-h2:pb-1 prose-h2:mt-6 prose-h2:mb-3 prose-h3:mt-4 prose-h3:mb-1 prose-p:my-1 prose-li:my-0.5">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {markdown}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
