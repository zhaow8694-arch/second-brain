'use client';

import React from 'react';

export const AtmosphericBackground: React.FC = () => {
  return (
    <>
      <div className="fixed inset-0 z-[-1] pointer-events-none overflow-hidden">
        {/* Base Gradient */}
        <div className="absolute inset-0 bg-radial-at-t from-[#0a0f1d] via-[#030712] to-[#010206]"></div>
        
        {/* Cyber Grid */}
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-[0.03] mix-blend-overlay"></div>

        {/* Drifting Nebula Clouds (Ambient Glows) */}
        <div className="absolute top-[-10%] left-[-5%] w-[60%] h-[60%] rounded-full bg-cyan-500/5 blur-[120px] animate-[drift_20s_linear_infinite]"></div>
        <div className="absolute bottom-[-10%] right-[-5%] w-[60%] h-[60%] rounded-full bg-purple-500/5 blur-[120px] animate-[drift_25s_linear_reverse_infinite]"></div>
        <div className="absolute top-[20%] right-[10%] w-[40%] h-[40%] rounded-full bg-yellow-500/3 blur-[100px] animate-pulse"></div>
      </div>

      <style jsx global>{`
        @keyframes drift {
          0% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(5%, 5%) scale(1.1); }
          66% { transform: translate(-5%, 10%) scale(0.9); }
          100% { transform: translate(0, 0) scale(1); }
        }
        .bg-radial-at-t {
          background: radial-gradient(circle at top, #0a0f1d 0%, #030712 45%, #010206 100%);
        }
      `}</style>
    </>
  );
};
