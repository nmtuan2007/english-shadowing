"use client";
import { useState, useMemo } from 'react';
import useSWR, { useSWRConfig } from 'swr';
import Link from 'next/link';
import {
  PlayCircle,
  CheckCircle2,
  Search,
  LayoutGrid,
  Trophy,
  Clock,
  Layers,
  Sparkles,
  Check,
  Loader2,
  Youtube,
  DownloadCloud,
  Cpu,
  FileAudio
} from 'lucide-react';

const fetcher = (url: string) => fetch(url).then(res => res.json());

export default function Dashboard() {
  const { mutate } = useSWRConfig();
  const { data, isLoading } = useSWR('http://localhost:8000/api/lessons', fetcher, {
    refreshInterval: 3000 // Poll frequently to update progress bars/status
  });

  const [searchQuery, setSearchQuery] = useState("");
  const [addUrl, setAddUrl] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [activeCategory, setActiveCategory] = useState("All");
  const [startingLessons, setStartingLessons] = useState<Set<string>>(new Set());

  const categories = useMemo(() => {
    if (!data) return ["All"];
    return ["All", ...Object.keys(data)];
  }, [data]);

  const stats = useMemo(() => {
    if (!data) return { total: 0, done: 0 };
    const all = Object.values(data).flat() as any[];
    return {
      total: all.length,
      done: all.filter(l => l.done).length
    };
  }, [data]);

  const filteredData = useMemo(() => {
    if (!data) return {};
    const filtered: any = {};

    Object.keys(data).forEach(cat => {
      if (activeCategory !== "All" && cat !== activeCategory) return;
      const matches = data[cat].filter((l: any) =>
        l.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
      if (matches.length > 0) filtered[cat] = matches;
    });
    return filtered;
  }, [data, searchQuery, activeCategory]);

  const handleAddLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addUrl) return;

    setIsAdding(true);
    try {
      const res = await fetch('http://localhost:8000/api/add-lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: addUrl, category: 'custom' })
      });

      if (res.ok) {
        setAddUrl("");
        mutate('http://localhost:8000/api/lessons');
        alert("Lesson added! Processing started.");
      } else {
        const err = await res.json();
        alert("Error: " + err.detail);
      }
    } catch (error) {
      console.error(error);
      alert("Failed to connect to server.");
    } finally {
      setIsAdding(false);
    }
  };

  const handleStartDownload = async (e: React.MouseEvent, category: string, lessonId: string) => {
    e.preventDefault(); // Prevent Link navigation
    e.stopPropagation();

    setStartingLessons(prev => new Set(prev).add(lessonId));

    try {
      await fetch('http://localhost:8000/api/start-lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category, lesson_id: lessonId })
      });
      mutate('http://localhost:8000/api/lessons');
    } catch (err) {
      console.error(err);
      alert("Failed to start download.");
    } finally {
      // Keep loading state briefly to ensure UI transitions smoothly until next poll
      setTimeout(() => {
        setStartingLessons(prev => {
          const next = new Set(prev);
          next.delete(lessonId);
          return next;
        });
      }, 1000);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'downloading':
        return <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-100 text-blue-600 text-[10px] font-black tracking-widest animate-pulse"><DownloadCloud size={12} /> DOWNLOADING</div>;
      case 'transcribing':
        return <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-100 text-purple-600 text-[10px] font-black tracking-widest animate-pulse"><FileAudio size={12} /> TRANSCRIBING</div>;
      case 'generating_ai':
        return <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-100 text-amber-600 text-[10px] font-black tracking-widest animate-pulse"><Cpu size={12} /> GENERATING AI</div>;
      case 'not_started':
        return <span className="text-[10px] font-black px-3 py-1.5 rounded-full bg-slate-100 text-slate-400 uppercase">Not Downloaded</span>;
      default:
        return null;
    }
  };

  if (isLoading) return (
    <div className="flex h-screen items-center justify-center space-x-2">
      <div className="w-3 h-3 bg-brand-600 rounded-full animate-bounce"></div>
      <div className="w-3 h-3 bg-brand-600 rounded-full animate-bounce [animation-delay:-.3s]"></div>
      <div className="w-3 h-3 bg-brand-600 rounded-full animate-bounce [animation-delay:-.5s]"></div>
    </div>
  );

  return (
    <main className="min-h-screen bg-[#F8FAFC] dark:bg-slate-950 pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="p-2 bg-brand-600 rounded-xl text-white group-hover:rotate-12 transition-transform">
              <Sparkles size={20} fill="currentColor" />
            </div>
            <h1 className="text-xl font-black tracking-tight text-slate-900 dark:text-white uppercase">Fluency</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-black bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded-full text-slate-500">
              <Trophy size={14} className="text-amber-500" />
              <span>{stats.done} / {stats.total} COMPLETED</span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6 space-y-8">

        {/* --- ADD LESSON & SEARCH BAR --- */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <form onSubmit={handleAddLesson} className="md:col-span-2 relative group">
            <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400">
              {isAdding ? <Loader2 className="animate-spin" size={20} /> : <Youtube size={20} />}
            </div>
            <input
              type="text"
              placeholder="Paste YouTube URL to add a new lesson..."
              className="w-full pl-14 pr-32 py-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-[2rem] text-sm font-medium focus:outline-none focus:ring-4 focus:ring-brand-500/10 focus:border-brand-500 transition-all shadow-sm"
              value={addUrl}
              onChange={(e) => setAddUrl(e.target.value)}
              disabled={isAdding}
            />
            <button
              type="submit"
              disabled={!addUrl || isAdding}
              className="absolute right-2 top-2 bottom-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-6 rounded-[1.5rem] text-xs font-black uppercase tracking-wider hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:hover:scale-100"
            >
              {isAdding ? 'Adding...' : 'Import'}
            </button>
          </form>

          <div className="relative group">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-600 transition-colors" size={20} />
            <input
              type="text"
              placeholder="Search lessons..."
              className="w-full pl-14 pr-6 py-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-[2rem] text-sm font-medium focus:outline-none focus:ring-4 focus:ring-brand-500/10 focus:border-brand-500 transition-all shadow-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </section>

        {/* --- CATEGORIES --- */}
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-6 py-3 rounded-2xl text-xs font-black transition-all border ${activeCategory === cat
                  ? 'bg-brand-600 border-brand-600 text-white shadow-lg shadow-brand-500/30 scale-105'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-500 hover:border-brand-300 hover:text-brand-600'
                  }`}
              >
                {cat.replace('_', ' ').toUpperCase()}
              </button>
            ))}
          </div>
        </section>

        {/* Content Grid */}
        <div className="space-y-16 pt-4">
          {Object.keys(filteredData).map(category => (
            <section key={category}>
              <div className="flex items-center gap-4 mb-8">
                <div className="w-10 h-10 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-brand-600 shadow-sm">
                  <LayoutGrid size={20} />
                </div>
                <h2 className="text-xl font-black text-slate-900 dark:text-slate-100 uppercase tracking-tight">
                  {category.replace('_', ' ')}
                </h2>
                <span className="text-xs font-bold text-slate-400 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full">
                  {filteredData[category].length} Lessons
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                {filteredData[category].map((lesson: any) => {
                  const status = lesson.status || 'not_started';
                  const isReady = status === 'ready';
                  const isProcessing = ['downloading', 'transcribing', 'generating_ai'].includes(status);
                  const isStarting = startingLessons.has(lesson.lesson);

                  return (
                    <Link
                      key={lesson.lesson}
                      href={isReady ? `/practice/${category}/${lesson.lesson}` : '#'}
                      onClick={(e) => {
                        // Prevent navigation if not ready
                        if (!isReady) e.preventDefault();
                      }}
                      className={`block h-full ${!isReady ? 'cursor-default' : ''}`}
                    >
                      <div className={`group relative flex flex-col h-full p-8 rounded-[2.5rem] border transition-all duration-300 ${isReady ? 'hover:shadow-2xl hover:-translate-y-2 active:scale-95' : ''
                        } ${lesson.done
                          ? 'bg-emerald-50/30 border-emerald-100 dark:bg-emerald-950/10 dark:border-emerald-900/30'
                          : isProcessing
                            ? 'bg-brand-50/20 border-brand-200 dark:bg-slate-900 dark:border-brand-900'
                            : 'bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 hover:border-brand-200'
                        }`}>

                        <div className="flex items-start justify-between mb-6">
                          <span className={`text-[10px] font-black px-3 py-1.5 rounded-full uppercase tracking-wider ${lesson.level.startsWith('A') ? 'bg-emerald-100 text-emerald-700' :
                              lesson.level.startsWith('B') ? 'bg-amber-100 text-amber-700' :
                                lesson.level === '??' ? 'bg-slate-100 text-slate-500' :
                                  'bg-rose-100 text-rose-700'
                            }`}>
                            Level {lesson.level}
                          </span>

                          {lesson.done ? (
                            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500 text-white text-[10px] font-black tracking-widest animate-in fade-in zoom-in">
                              <Check size={12} strokeWidth={4} /> COMPLETED
                            </div>
                          ) : (
                            getStatusBadge(status)
                          )}
                        </div>

                        <h3 className={`font-black text-xl leading-tight mb-8 ${lesson.done ? 'text-slate-500 line-through decoration-emerald-500/30' : 'text-slate-800 dark:text-slate-200'
                          }`}>
                          {lesson.title}
                        </h3>

                        <div className="mt-auto flex items-center justify-between">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-slate-400 text-[11px] font-black uppercase tracking-tight">
                              <Clock size={14} className="text-brand-500" />
                              {Math.floor(lesson.duration / 60)}m {lesson.duration % 60}s
                            </div>
                            <div className="flex items-center gap-2 text-slate-400 text-[11px] font-black uppercase tracking-tight">
                              <Layers size={14} className="text-brand-500" />
                              {lesson.source.split(' ')[0]}
                            </div>
                          </div>

                          {/* ACTION BUTTON */}
                          <div className="relative">
                            {isReady ? (
                              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all ${lesson.done
                                  ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-200'
                                  : 'bg-slate-50 dark:bg-slate-800 text-slate-400 group-hover:bg-brand-600 group-hover:text-white group-hover:shadow-xl group-hover:shadow-brand-500/40'
                                }`}>
                                {lesson.done ? <CheckCircle2 size={28} /> : <PlayCircle size={28} />}
                              </div>
                            ) : isProcessing || isStarting ? (
                              <div className="w-14 h-14 rounded-2xl bg-brand-50 flex items-center justify-center text-brand-500">
                                <Loader2 className="animate-spin" size={24} />
                              </div>
                            ) : (
                              <button
                                onClick={(e) => handleStartDownload(e, category, lesson.lesson)}
                                className="w-14 h-14 rounded-2xl bg-slate-100 hover:bg-slate-900 hover:text-white flex items-center justify-center text-slate-400 transition-all shadow-sm hover:shadow-xl"
                                title="Download Lesson"
                              >
                                <DownloadCloud size={24} />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </Link>
                  )
                })}
              </div>
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}
