'use client';

import React from 'react';

interface LoadingSkeletonProps {
  type?: 'BAZI' | 'TAROT' | 'ZODIAC';
  lang?: 'EN' | 'CN';
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ type = 'BAZI', lang = 'CN' }) => {
  const t = {
    loading: lang === 'EN' ? 'Initializing Quantum Matrix...' : '正在初始化量子矩阵...',
    syncing: lang === 'EN' ? 'Syncing Astral Data...' : '同步星历数据中...',
    calibrating: lang === 'EN' ? 'Calibrating Energy Resonance...' : '校准能量共振...',
  };

  const colors = {
    BAZI: 'from-cyan-500/20 to-blue-500/20 border-cyan-500/30 text-cyan-500',
    TAROT: 'from-purple-500/20 to-pink-500/20 border-purple-500/30 text-purple-500',
    ZODIAC: 'from-yellow-500/20 to-orange-500/20 border-yellow-500/30 text-yellow-500',
  };

  const selectedColor = colors[type];

  return (
    <div className="min-h-screen bg-[#030712] flex flex-col items-center justify-center p-6 space-y-8 overflow-hidden relative">
      {/* Background Ambience */}
      <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full blur-[120px] opacity-20 bg-gradient-to-r ${selectedColor.split(' ')[0]}`}></div>
      
      {/* Central Scanner Circle */}
      <div className="relative">
        <div className={`w-32 h-32 rounded-full border-2 border-dashed ${selectedColor.split(' ')[1]} animate-[spin_10s_linear_infinite] opacity-40`}></div>
        <div className={`absolute inset-0 w-32 h-32 rounded-full border-t-2 ${selectedColor.split(' ')[1]} animate-spin`}></div>
        <div className="absolute inset-4 rounded-full bg-black/40 backdrop-blur-md border border-white/5 flex items-center justify-center">
          <div className={`w-2 h-2 rounded-full bg-current ${selectedColor.split(' ')[2]} animate-ping`}></div>
        </div>
      </div>

      {/* Loading Text */}
      <div className="text-center space-y-4 relative z-10">
        <h2 className={`text-xs font-black uppercase tracking-[0.5em] ${selectedColor.split(' ')[2]} animate-pulse`}>
          {t.loading}
        </h2>
        
        {/* Progress Bar Skeleton */}
        <div className="w-64 h-1 bg-white/5 rounded-full overflow-hidden border border-white/5">
          <div className={`h-full bg-gradient-to-r ${selectedColor.split(' ')[0]} animate-[loading-progress_2s_ease-in-out_infinite] w-1/3`}></div>
        </div>
        
        <div className="flex justify-center gap-8 pt-4">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/5 animate-pulse"></div>
            <div className="w-12 h-2 bg-white/5 rounded animate-pulse"></div>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/5 animate-pulse delay-75"></div>
            <div className="w-12 h-2 bg-white/5 rounded animate-pulse delay-75"></div>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/5 animate-pulse delay-150"></div>
            <div className="w-12 h-2 bg-white/5 rounded animate-pulse delay-150"></div>
          </div>
        </div>
      </div>

      {/* Decorative Matrix Lines */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03] overflow-hidden">
        <div className="grid grid-cols-12 h-full w-full">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="border-r border-white h-full"></div>
          ))}
        </div>
      </div>

      <style jsx>{`
        @keyframes loading-progress {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>
    </div>
  );
};
