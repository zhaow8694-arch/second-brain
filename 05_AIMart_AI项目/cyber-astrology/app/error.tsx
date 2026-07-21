'use client';

import React, { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Global Error Boundary:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#030712] flex flex-col items-center justify-center p-6 text-center space-y-8">
      <div className="relative">
        <div className="text-8xl md:text-9xl font-black text-red-500/20 animate-pulse select-none">
          ERROR
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-4xl md:text-6xl font-black text-red-500 tracking-tighter uppercase italic">
            System <span className="text-white">Failure</span>
          </div>
        </div>
      </div>

      <div className="max-w-md space-y-4">
        <p className="text-gray-400 font-mono text-xs uppercase tracking-widest leading-relaxed">
          The quantum resonance has been interrupted. The matrix is unstable.
          <br />
          错误代码: <span className="text-red-400">{error.digest || 'UNKNOWN_COLLAPSE'}</span>
        </p>
      </div>

      <div className="flex gap-4">
        <button
          onClick={() => reset()}
          className="px-8 py-3 bg-red-500 hover:bg-red-600 text-black font-black uppercase text-xs rounded-xl transition-all shadow-[0_0_30px_rgba(239,68,68,0.3)]"
        >
          Re-establish Link
        </button>
        <button
          onClick={() => window.location.href = '/'}
          className="px-8 py-3 border border-gray-800 text-gray-400 hover:text-white hover:border-gray-600 font-black uppercase text-xs rounded-xl transition-all"
        >
          Return to Hall
        </button>
      </div>

      {/* Decorative Glitch Effect */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.05] overflow-hidden">
        <div className="h-full w-full bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
      </div>
    </div>
  );
}
