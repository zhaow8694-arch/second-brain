'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';

export default function HallPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'EN' | 'CN'>('CN');
  const [isMounted, setIsMounted] = useState(false);
  const [isNavigating, setIsNavigating] = useState<string | null>(null);

  useEffect(() => {
    const initialize = () => {
      if (typeof window !== 'undefined') {
        const params = new URLSearchParams(window.location.search);
        const l = params.get('lang');
        if (l === 'EN' || l === 'CN') {
          setLang(l);
        }
      }
      setIsMounted(true);
    };
    
    initialize();
  }, []);

  const t = useMemo(() => ({
    mainTitle: 'FATE',
    subTitle: lang === 'EN' ? 'Cyber Esoteric Portal' : '赛博神秘学大厅',
    baziCard: lang === 'EN' ? 'Eastern Matrix' : '东方能量罗盘',
    baziDesc: lang === 'EN' ? 'BaZi · Wealth Pillars' : '东方八字 · 财富大运',
    tarotCard: lang === 'EN' ? 'Western Arcana' : '西方赛博塔罗',
    tarotDesc: lang === 'EN' ? 'Tarot · Subconscious' : '潜意识抽牌 · 秘仪占卜',
    zodiacCard: lang === 'EN' ? 'Zodiac Nebula' : '赛博星系星盘',
    zodiacDesc: lang === 'EN' ? 'Horoscope · Love Match' : '星座分析 · 恋爱匹配',
    btnEnter: lang === 'EN' ? 'Enter Room' : '进入房间',
    btnEntering: lang === 'EN' ? 'Entering...' : '正在连接...',
    footer: lang === 'EN' ? 'Select your matrix to begin decryption' : '请选择你要连接的命运矩阵',
    loading: lang === 'EN' ? 'Initializing Cyber Portal...' : '正在初始化赛博门户...',
    navError: lang === 'EN' ? 'Connection failed, please try again' : '连接失败，请重试',
    langEN: lang === 'EN' ? 'Switch to English' : '切换到英文',
    langCN: lang === 'EN' ? 'Switch to Chinese' : '切换到中文'
  }), [lang]);

  const navigate = useCallback(async (url: string, cardId: string) => {
    if (isNavigating) return;
    
    setIsNavigating(cardId);
    
    try {
      await router.push(url);
      // 🐛 BUG FIX 1: 添加导航超时保护
      const timeoutId = setTimeout(() => {
        setIsNavigating(null);
        console.warn('Navigation timeout');
      }, 5000);
      
      // 清理超时定时器
      return () => clearTimeout(timeoutId);
    } catch (error) {
      console.error('Navigation error:', error);
      alert(t.navError);
      setIsNavigating(null);
    }
  }, [isNavigating, router, t.navError]);

  if (!isMounted) {
    return (
      <div 
        className="min-h-screen bg-[#030712] flex items-center justify-center"
        role="status"
        aria-live="polite"
        aria-label={t.loading}
      >
        <div className="text-cyan-500 text-sm animate-pulse font-mono tracking-widest uppercase">
          {t.loading}
        </div>
      </div>
    );
  }

  const cards = [
    {
      id: 'bazi',
      emoji: '☯️',
      title: t.baziCard,
      desc: t.baziDesc,
      gradient: 'from-cyan-500 to-blue-600',
      textColor: 'text-cyan-500',
      borderColor: 'border-cyan-400',
      hoverBorder: 'hover:border-cyan-400',
      url: `/bazi?lang=${lang}`,
      bgImage: '/items/og-bazi.webp',
      ariaLabel: lang === 'EN' 
        ? 'Enter Eastern Matrix room for BaZi fortune analysis' 
        : '进入东方能量罗盘房间进行八字财富分析'
    },
    {
      id: 'tarot',
      emoji: '🃏',
      title: t.tarotCard,
      desc: t.tarotDesc,
      gradient: 'from-purple-500 to-pink-600',
      textColor: 'text-purple-400',
      borderColor: 'border-purple-400',
      hoverBorder: 'hover:border-purple-400',
      url: `/tarot?lang=${lang}`,
      bgImage: '/items/og-tarot.webp',
      ariaLabel: lang === 'EN'
        ? 'Enter Western Arcana room for Tarot subconscious reading'
        : '进入西方赛博塔罗房间进行潜意识塔罗占卜'
    },
    {
      id: 'zodiac',
      emoji: '✨',
      title: t.zodiacCard,
      desc: t.zodiacDesc,
      gradient: 'from-yellow-500 to-orange-600',
      textColor: 'text-yellow-500',
      borderColor: 'border-yellow-400',
      hoverBorder: 'hover:border-yellow-400',
      url: `/zodiac?lang=${lang}`,
      bgImage: '/items/og-zodiac.webp',
      ariaLabel: lang === 'EN'
        ? 'Enter Zodiac Nebula room for horoscope and love match analysis'
        : '进入赛博星系星盘房间进行星座分析和恋爱匹配'
    }
  ];

  // 🐛 BUG FIX 2: 动态生成边框颜色类名，避免Tailwind无法识别动态类
  const getBorderColorClass = (color: string, isHover = false) => {
    const colorMap: Record<string, string> = {
      'cyan': isHover ? 'hover:border-cyan-400' : 'border-cyan-400',
      'purple': isHover ? 'hover:border-purple-400' : 'border-purple-400',
      'yellow': isHover ? 'hover:border-yellow-400' : 'border-yellow-400'
    };
    
    const baseColor = color.split('-')[1]; // 从 'border-cyan-400' 提取 'cyan'
    return colorMap[baseColor] || color;
  };

  // 🐛 BUG FIX 3: 动态生成背景颜色类名
  const getBgColorClass = (color: string) => {
    const colorMap: Record<string, string> = {
      'cyan': 'bg-cyan-500/20',
      'purple': 'bg-purple-500/20',
      'yellow': 'bg-yellow-500/20'
    };
    
    const baseColor = color.split('-')[1];
    return colorMap[baseColor] || 'bg-gray-500/20';
  };

  // 🐛 BUG FIX 4: 动态生成旋转边框颜色类名
  const getSpinnerBorderColorClass = (color: string) => {
    const colorMap: Record<string, string> = {
      'cyan': 'border-t-cyan-500',
      'purple': 'border-t-purple-500',
      'yellow': 'border-t-yellow-500'
    };
    
    const baseColor = color.split('-')[1];
    return colorMap[baseColor] || 'border-t-cyan-500';
  };

  return (
    <div 
      className="min-h-screen bg-transparent text-white flex flex-col items-center justify-center p-4 font-sans selection:bg-cyan-500/30 overflow-hidden relative"
      role="main"
      aria-label={t.subTitle}
    >
      {/* Top Progress Bar for Navigation */}
      {isNavigating && (
        <div className="fixed top-0 left-0 w-full h-1.5 z-[100] overflow-hidden bg-cyan-950/30 backdrop-blur-sm">
          <div className="h-full bg-cyan-500 shadow-[0_0_20px_rgba(6,182,212,1),0_0_40px_rgba(6,182,212,0.6)] animate-[progress_1.5s_infinite] relative">
            <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
          </div>
          {/* Energy Surge Effect */}
          <div className="absolute top-0 left-0 h-full w-20 bg-gradient-to-r from-transparent via-white/80 to-transparent animate-[surge_1s_linear_infinite]"></div>
        </div>
      )}

      {/* Navigation Overlay - Dims the screen slightly to focus on the bar */}
      {isNavigating && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[1px] z-[90] animate-in fade-in duration-500"></div>
      )}

      {/* Global Scanning Line */}
      <div className="fixed inset-0 pointer-events-none z-[60] overflow-hidden opacity-[0.05]">
        <div className="w-full h-[2px] bg-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.8)] animate-[scan_4s_linear_infinite]"></div>
      </div>

      <div 
        className="absolute top-4 right-4 md:top-8 md:right-8 flex gap-2 z-[100] bg-black/50 backdrop-blur-md p-1.5 rounded-xl border border-gray-800/50"
        role="group"
        aria-label={lang === 'EN' ? 'Language selection' : '语言选择'}
      >
        <button
          onClick={() => setLang('EN')}
          aria-label={t.langEN}
          aria-pressed={lang === 'EN'}
          className={`px-4 py-1.5 rounded-lg text-[10px] uppercase tracking-widest transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:ring-offset-2 focus:ring-offset-[#030712] ${
            lang === 'EN'
              ? 'bg-cyan-500 text-black font-black shadow-[0_0_15px_rgba(6,182,212,0.3)]'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          EN
        </button>
        <button
          onClick={() => setLang('CN')}
          aria-label={t.langCN}
          aria-pressed={lang === 'CN'}
          className={`px-4 py-1.5 rounded-lg text-[10px] uppercase tracking-widest transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:ring-offset-2 focus:ring-offset-[#030712] ${
            lang === 'CN'
              ? 'bg-cyan-500 text-black font-black shadow-[0_0_15px_rgba(6,182,212,0.3)]'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          中文
        </button>
      </div>

      <header className="text-center mb-12 md:mb-16 z-10 animate-in slide-in-from-top-8 duration-700 px-4 pt-12 md:pt-0">
        <h1 className="text-5xl md:text-8xl font-black italic tracking-tighter uppercase relative drop-shadow-[0_0_30px_rgba(6,182,212,0.15)] leading-tight">
          {t.mainTitle}<span className="text-cyan-500">Matrices</span>
        </h1>
        <p className="text-gray-400 text-[10px] md:text-sm tracking-[0.3em] md:tracking-[0.5em] uppercase mt-4 md:mt-6 font-mono opacity-80">
          {t.subTitle}
        </p>
      </header>

      <div 
        className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 w-full max-w-6xl z-10 px-4 md:px-0 animate-in fade-in duration-1000 delay-150"
        role="region"
        aria-label={lang === 'EN' ? 'Destiny Matrix Selection' : '命运矩阵选择区域'}
      >
        {cards.map((card) => {
          const isCardNavigating = isNavigating === card.id;
          const isOtherNavigating = isNavigating !== null && !isCardNavigating;
          const borderClass = getBorderColorClass(card.borderColor);
          const hoverBorderClass = getBorderColorClass(card.borderColor, true);
          const bgColorClass = getBgColorClass(card.borderColor);
          const spinnerBorderClass = getSpinnerBorderColorClass(card.borderColor);
          
          return (
            <button
              key={card.id}
              onClick={() => navigate(card.url, card.id)}
              disabled={isNavigating !== null}
              aria-label={card.ariaLabel}
              aria-busy={isCardNavigating}
              className={`group relative p-1 rounded-[3rem] bg-gradient-to-b from-gray-800 to-black transition-all duration-500 w-full text-left focus:outline-none focus:ring-4 focus:ring-cyan-500/30 overflow-hidden ${
                isOtherNavigating 
                  ? 'opacity-30 scale-95 cursor-not-allowed filter grayscale-[50%]' 
                  : isCardNavigating
                    ? 'scale-[1.02] shadow-[0_0_50px_rgba(6,182,212,0.2)]'
                    : `cursor-pointer hover:-translate-y-2 hover:shadow-2xl ${hoverBorderClass}`
              }`}
            >
              <div className="bg-[#0a0f1d] h-full rounded-[2.9rem] flex flex-col items-center justify-center text-center relative overflow-hidden group-hover:shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                {/* Background Image - Full Cover */}
                <div 
                  className="absolute inset-0 z-0 bg-cover bg-center transition-all duration-1000 group-hover:scale-110 opacity-50 group-hover:opacity-80"
                  style={{ backgroundImage: `url(${card.bgImage})` }}
                ></div>
                {/* Gradient Overlay */}
                <div className={`absolute inset-0 z-1 bg-gradient-to-b ${card.gradient} opacity-40 group-hover:opacity-30 transition-opacity duration-500`}></div>
                {/* Dark Overlay for Readability */}
                <div className="absolute inset-0 z-1 bg-gradient-to-t from-black/80 via-black/40 to-transparent group-hover:from-black/60 group-hover:via-black/20 transition-all duration-500"></div>
                
                {/* Content Overlay */}
                <div className="relative z-10 p-6 md:p-10 flex flex-col items-center justify-center space-y-4 md:space-y-6 w-full h-full min-h-[280px] md:min-h-0 backdrop-blur-[1px] group-hover:backdrop-blur-0 transition-all duration-500">
                  <span 
                    className={`text-5xl md:text-6xl transition-transform duration-500 ${isCardNavigating ? 'scale-110 animate-pulse' : 'group-hover:scale-110'}`}
                    aria-hidden="true"
                  >
                    {card.emoji}
                  </span>
                  
                  <div className="space-y-1 md:space-y-2">
                    <h2 className="text-xl md:text-3xl font-black uppercase tracking-tight text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.9)] leading-tight">
                      {card.title}
                    </h2>
                    <p className={`${card.textColor} font-bold text-[9px] md:text-xs uppercase tracking-wider md:tracking-widest drop-shadow-[0_2px_5px_rgba(0,0,0,0.9)]`}>
                      {card.desc}
                    </p>
                  </div>
                  
                  <div 
                    className={`py-2.5 px-6 md:py-3 md:px-10 rounded-xl border-2 transition-all duration-300 text-[10px] md:text-xs font-black uppercase tracking-wider md:tracking-widest ${
                      isCardNavigating 
                        ? `${borderClass} ${bgColorClass} text-white` 
                        : `border-white/30 text-white/90 ${hoverBorderClass} group-hover:border-white group-hover:text-white group-hover:bg-white/10`
                    } shadow-xl`}
                  >
                    {isCardNavigating ? t.btnEntering : t.btnEnter}
                  </div>
                </div>
                
                {isCardNavigating && (
                  <div 
                    className="absolute inset-0 bg-[#0a0f1d]/80 backdrop-blur-sm rounded-[2.9rem] flex flex-col items-center justify-center z-20 animate-in fade-in duration-300"
                    role="status"
                    aria-label={lang === 'EN' ? 'Establishing connection' : '正在建立连接'}
                  >
                    <div className={`w-12 h-12 rounded-full border-4 ${spinnerBorderClass} border-r-transparent border-b-transparent border-l-transparent animate-spin`}></div>
                    <div className={`mt-6 text-[10px] ${card.textColor} uppercase tracking-[0.3em] font-black animate-pulse`}>
                      {lang === 'EN' ? 'Syncing...' : '数据同步中...'}
                    </div>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-20 text-center z-10 animate-in slide-in-from-bottom-8 duration-1000 delay-300">
        <p 
          className="text-[10px] text-gray-600 uppercase tracking-[0.4em] font-mono opacity-60"
          aria-live="polite"
        >
          {t.footer}
        </p>
      </div>

      <div className="sr-only">
        <p>
          {lang === 'EN' 
            ? 'Use Tab to navigate between destiny matrices, Enter to select, and arrow keys to move between language options.' 
            : '使用 Tab 键在命运矩阵间导航，Enter 键选择，方向键在语言选项间移动。'}
        </p>
      </div>

      <style jsx>{`
        @keyframes scan {
          0% { transform: translateY(-100vh); }
          100% { transform: translateY(100vh); }
        }
        @keyframes progress {
          0% { width: 0%; transform: translateX(-100%); }
          50% { width: 70%; transform: translateX(0%); }
          100% { width: 100%; transform: translateX(100%); }
        }
        @keyframes surge {
          0% { left: -20%; }
          100% { left: 120%; }
        }
      `}</style>
    </div>
  );
}