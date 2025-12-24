"use client";
import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useSWRConfig } from 'swr';
import {
  ChevronLeft, RotateCcw, CheckCircle,
  BookOpen, MessageCircle, Volume2,
  Maximize2, Minimize2, Loader2, Music, AlertCircle,
  DownloadCloud, FileAudio, Cpu
} from 'lucide-react';

export default function PracticeRoom() {
  const params = useParams();
  const router = useRouter();
  const { mutate } = useSWRConfig();

  const category = Array.isArray(params.category) ? params.category[0] : params.category;
  const id = Array.isArray(params.id) ? params.id[0] : params.id;

  const [data, setData] = useState<any>(null);
  const [tab, setTab] = useState<'transcript' | 'vocab'>('transcript');
  const [showVi, setShowVi] = useState(false);
  const [showGuide, setShowGuide] = useState(true);
  const [isDone, setIsDone] = useState(false);
  const [isTheaterMode, setIsTheaterMode] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isLoading, setIsLoading] = useState(true);

  const videoRef = useRef<HTMLVideoElement>(null);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Polling for data
  useEffect(() => {
    if (!category || !id) return;

    let isMounted = true;
    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/lesson/${category}/${id}`);
        const d = await res.json();

        if (isMounted) {
          setData(d);
          setIsLoading(false);

          // Poll if in any processing state
          if (['downloading', 'transcribing', 'generating_ai'].includes(d.status)) {
            setTimeout(fetchData, 3000);
          }
        }
      } catch (error) {
        console.error(error);
        if (isMounted) setIsLoading(false);
      }
    };

    fetchData();

    // Check done status
    fetch('http://localhost:8000/api/lessons').then(res => res.json()).then(all => {
      const lesson = Object.values(all).flat().find((l: any) => l.lesson === id) as any;
      if (lesson?.done) setIsDone(true);
    });

    return () => { isMounted = false; };
  }, [category, id]);

  // Sync Transcript
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !data?.transcript) return;

    const handleTimeUpdate = () => {
      const time = video.currentTime;
      const index = data.transcript.findIndex((s: any) => time >= s.start && time <= s.end);

      if (index !== -1 && index !== activeIndex) {
        setActiveIndex(index);
        itemRefs.current[index]?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      }
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    return () => video.removeEventListener('timeupdate', handleTimeUpdate);
  }, [data, activeIndex]);

  const seekTo = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      videoRef.current.play();
    }
  };

  const speakText = (text: string) => {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  };

  const toggleDone = async () => {
    if (!id) return;
    const newState = !isDone;
    setIsDone(newState);
    await fetch('http://localhost:8000/api/done', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lesson_id: id, done: newState })
    });
    mutate('http://localhost:8000/api/lessons');
  };

  // --- LOADING / PROCESSING STATES ---

  if (isLoading) return (
    <div className="h-screen flex items-center justify-center bg-white dark:bg-slate-950">
      <Loader2 className="animate-spin text-brand-600" size={40} />
    </div>
  );

  const status = data?.status;

  if (['downloading', 'transcribing', 'generating_ai'].includes(status)) {
    let icon = <Loader2 className="animate-spin text-brand-600" size={60} />;
    let text = "Processing...";
    let subtext = "Please wait.";

    if (status === 'downloading') {
      icon = <DownloadCloud className="animate-bounce text-blue-500" size={60} />;
      text = "Downloading Video";
      subtext = "Fetching content from YouTube...";
    } else if (status === 'transcribing') {
      icon = <FileAudio className="animate-pulse text-purple-500" size={60} />;
      text = "Transcribing Audio";
      subtext = "Extracting text timestamps...";
    } else if (status === 'generating_ai') {
      icon = <Cpu className="animate-spin text-amber-500" size={60} />;
      text = "AI Processing";
      subtext = "Generating translations and shadowing guides...";
    }

    return (
      <div className="h-screen flex flex-col items-center justify-center bg-white dark:bg-slate-950 space-y-6">
        <div className="relative">
          <div className="absolute inset-0 bg-slate-200 blur-xl opacity-20"></div>
          <div className="relative z-10">{icon}</div>
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-xl font-black text-slate-800 dark:text-white uppercase tracking-tight">{text}</h2>
          <p className="text-slate-400 text-sm font-medium">{subtext}</p>
        </div>
        <button onClick={() => router.back()} className="text-xs font-bold text-slate-400 hover:text-brand-600">
          Go Back
        </button>
      </div>
    );
  }

  if (status === 'not_found' || status === 'not_started' || !data?.transcript) return (
    <div className="h-screen flex flex-col items-center justify-center bg-white dark:bg-slate-950 space-y-4">
      <AlertCircle className="text-rose-500" size={60} />
      <h2 className="text-xl font-black text-slate-800 dark:text-white uppercase">Lesson Not Ready</h2>
      <p className="text-slate-400">This lesson has not been generated yet.</p>
      <button onClick={() => router.back()} className="px-6 py-3 bg-slate-100 dark:bg-slate-800 rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-slate-200">
        Back to Dashboard
      </button>
    </div>
  );

  // --- MAIN UI ---

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-slate-950 overflow-hidden font-sans">

      {/* NAVIGATION BAR */}
      <nav className="flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 z-50">
        <div className="flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors">
            <ChevronLeft size={24} className="text-slate-600 dark:text-slate-300" />
          </button>
          <div className="hidden md:block">
            <h1 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-tight">Practice Session</h1>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{(category as string).replace('_', ' ')}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsTheaterMode(!isTheaterMode)}
            className={`p-2.5 rounded-xl transition-all ${isTheaterMode ? 'bg-brand-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}
          >
            {isTheaterMode ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
          </button>

          <div className="h-6 w-[1px] bg-slate-200 dark:bg-slate-800 mx-1"></div>

          <button onClick={() => setShowGuide(!showGuide)} className={`px-4 py-2 rounded-xl text-[10px] font-black tracking-widest transition-all ${showGuide ? 'bg-amber-500 text-white shadow-md' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'}`}>GUIDE</button>
          <button onClick={() => setShowVi(!showVi)} className={`px-4 py-2 rounded-xl text-[10px] font-black tracking-widest transition-all ${showVi ? 'bg-brand-600 text-white shadow-md' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'}`}>TRANS</button>
          <button onClick={toggleDone} className={`p-2.5 rounded-xl transition-all ${isDone ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-200' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'}`}>
            <CheckCircle size={20} />
          </button>
        </div>
      </nav>

      <div className={`flex flex-1 overflow-hidden ${isTheaterMode ? 'flex-col' : 'flex-col lg:flex-row'}`}>

        {/* PLAYER SECTION */}
        <div className={`bg-black flex items-center justify-center transition-all duration-500 ${isTheaterMode ? 'h-[45vh]' : 'w-full lg:w-3/5 xl:w-2/3'}`}>
          <video ref={videoRef} src={data.video_url} controls className="w-full h-full max-h-full" playsInline />
        </div>

        {/* TRANSCRIPT SECTION */}
        <div className={`flex flex-col bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 transition-all ${isTheaterMode ? 'flex-1' : 'w-full lg:w-2/5 xl:w-1/3'}`}>
          <div className="flex border-b border-slate-200 dark:border-slate-800">
            <button onClick={() => setTab('transcript')} className={`flex-1 py-4 text-xs font-black uppercase tracking-widest transition-all ${tab === 'transcript' ? 'text-brand-600 bg-brand-50/50 dark:bg-brand-900/10 border-b-2 border-brand-600' : 'text-slate-400 hover:text-slate-600'}`}>
              <div className="flex items-center justify-center gap-2"><MessageCircle size={16} /> Transcript</div>
            </button>
            <button onClick={() => setTab('vocab')} className={`flex-1 py-4 text-xs font-black uppercase tracking-widest transition-all ${tab === 'vocab' ? 'text-brand-600 bg-brand-50/50 dark:bg-brand-900/10 border-b-2 border-brand-600' : 'text-slate-400 hover:text-slate-600'}`}>
              <div className="flex items-center justify-center gap-2"><BookOpen size={16} /> Vocabulary</div>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
            {tab === 'transcript' ? (
              data.transcript.map((item: any, idx: number) => (
                <div
                  key={idx}
                  ref={(el) => { itemRefs.current[idx] = el; }}
                  onClick={() => seekTo(item.start)}
                  className={`relative p-6 rounded-[2rem] border-2 transition-all duration-300 cursor-pointer ${activeIndex === idx
                    ? 'bg-brand-50 border-brand-500 dark:bg-slate-800 dark:border-brand-500 shadow-xl shadow-brand-500/10 scale-[1.02] z-10'
                    : 'bg-slate-50/50 dark:bg-slate-800/30 border-transparent opacity-75 hover:opacity-100 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                >
                  <div className="flex justify-between items-start gap-4">
                    <p className={`text-xl font-extrabold leading-tight tracking-tight ${activeIndex === idx
                      ? 'text-slate-950 dark:text-white'
                      : 'text-slate-700 dark:text-slate-300'
                      }`}>
                      {item.en}
                    </p>
                    <button
                      onClick={(e) => { e.stopPropagation(); speakText(item.en); }}
                      className={`p-2 rounded-xl transition-all ${activeIndex === idx ? 'bg-brand-600 text-white' : 'bg-white dark:bg-slate-700 text-slate-400 shadow-sm'}`}
                    >
                      <Volume2 size={18} />
                    </button>
                  </div>

                  {showVi && (
                    <p className={`text-base font-medium mt-3 border-t pt-3 border-slate-200 dark:border-slate-700 ${activeIndex === idx ? 'text-brand-700 dark:text-brand-400' : 'text-slate-400'
                      }`}>
                      {item.vi}
                    </p>
                  )}

                  {showGuide && item.guide && (
                    <div className={`mt-4 p-4 rounded-2xl border font-mono text-sm leading-relaxed transition-all ${activeIndex === idx
                      ? 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-900/20 dark:border-amber-900/50 dark:text-amber-200 shadow-inner'
                      : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700 text-slate-400'
                      }`}>
                      <div className="flex items-center gap-2 opacity-50 mb-2">
                        <Music size={14} /> <span className="text-[10px] font-black uppercase tracking-widest">Shadowing Guide</span>
                      </div>
                      {item.guide}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 text-center p-10">
                <BookOpen size={48} className="mb-4 opacity-20" />
                <p className="font-black uppercase tracking-widest text-xs">Vocabulary list coming soon...</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <button
        onClick={() => { if (videoRef.current) videoRef.current.currentTime -= 5 }}
        className="fixed bottom-10 left-10 w-16 h-16 bg-slate-950 text-white rounded-[2rem] shadow-2xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-50 border-4 border-white/10"
      >
        <RotateCcw size={28} />
      </button>
    </div>
  );
}
