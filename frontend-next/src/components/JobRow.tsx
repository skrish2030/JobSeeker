'use client';

interface JobRowProps {
  job: any;
  isSaved: boolean;
  onToggleSave: (jobId: string, isSaved: boolean) => void;
  onClick: () => void;
}

export default function JobRow({ job, isSaved, onToggleSave, onClick }: JobRowProps) {
  
  const displayDate = job.posted_date 
    ? new Date(job.posted_date).toLocaleDateString() 
    : (job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Recent');

  return (
    <div 
      onClick={onClick}
      className="bg-[#15121E] border border-[#ffffff10] hover:border-indigo-500/50 hover:bg-[#1A1625] px-6 py-4 rounded-xl transition-all cursor-pointer flex items-center justify-between group"
    >
      <div className="flex-1 min-w-0 pr-4">
        <div className="flex items-center gap-3 mb-1">
          <h3 className="text-lg font-bold text-gray-100 group-hover:text-indigo-400 truncate transition-colors">{job.title}</h3>
          
          {/* Match Badge */}
          {job.score >= 80 && (
            <span className="shrink-0 px-2 py-0.5 bg-green-500/20 text-green-400 text-[10px] font-bold rounded uppercase tracking-wider border border-green-500/30">
              {job.score}% Match
            </span>
          )}
        </div>
        
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-400">
          <span className="font-semibold text-indigo-300 truncate max-w-[200px]">{job.company}</span>
          <span className="w-1 h-1 bg-gray-600 rounded-full"></span>
          <span className="truncate max-w-[150px]">{job.location || 'Location Not Specified'}</span>
          <span className="w-1 h-1 bg-gray-600 rounded-full"></span>
          
          {/* Emp Type Logic */}
          {(() => {
            const desc = (job.description || "").toLowerCase();
            const title = (job.title || "").toLowerCase();
            let empType = null;
            if (desc.includes("contract") || desc.includes("1099") || desc.includes("c2c") || desc.includes("contract to hire")) empType = "Contract";
            else if (desc.includes("intern") || title.includes("intern")) empType = "Internship";
            else if (desc.includes("part-time") || desc.includes("part time")) empType = "Part-Time";
            else if (desc.includes("full-time") || desc.includes("full time") || desc.includes("w2")) empType = "Full-Time";
            return empType ? <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-xs border border-blue-500/20">{empType}</span> : null;
          })()}
          
          {/* H1B Logic */}
          {(() => {
            const desc = (job.description || "").toLowerCase();
            const noSponsor = ["no visa sponsorship", "will not sponsor", "does not sponsor", "unable to sponsor", "no h1b", "no c2c", "us citizen", "no sponsorship"];
            const yesSponsor = ["h1b", "h-1b", "visa sponsorship", "sponsor visa", "will sponsor"];
            if (noSponsor.some(kw => desc.includes(kw))) return <span className="bg-red-500/10 text-red-400 px-2 py-0.5 rounded text-xs border border-red-500/20">No Sponsorship</span>;
            if (yesSponsor.some(kw => desc.includes(kw))) return <span className="bg-green-500/10 text-green-400 px-2 py-0.5 rounded text-xs border border-green-500/20">H-1B</span>;
            return null;
          })()}
        </div>
      </div>
      
      <div className="flex flex-col items-end gap-2 shrink-0 pl-4">
        <span className="text-xs font-medium text-gray-500 flex items-center gap-1">
          <svg className="w-3 h-3 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          {displayDate}
        </span>
        <button 
          onClick={(e) => { e.stopPropagation(); onToggleSave(job.id, isSaved); }}
          className={`p-1.5 rounded-lg transition-colors border ${isSaved ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' : 'bg-[#ffffff05] text-gray-500 border-[#ffffff10] hover:bg-[#ffffff10] hover:text-gray-300'}`}
          title={isSaved ? "Saved" : "Save Job"}
        >
          <svg className="w-4 h-4" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={isSaved ? 1 : 2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
        </button>
      </div>
    </div>
  );
}
