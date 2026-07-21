'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';

export default function ContactPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'EN' | 'CN'>('EN');

  const t = useMemo(() => ({
    back: lang === 'EN' ? '← Back to Home' : '← 返回首页',
    title: lang === 'EN' ? 'Contact Us' : '联系我们',
    lastUpdated: lang === 'EN' ? 'Last updated: June 2026' : '最后更新：2026年6月',
    intro: lang === 'EN'
      ? 'We are here to help. Reach out to us through any of the channels below.'
      : '我们随时为您提供帮助。请通过以下任意渠道联系我们。',
    emailLabel: lang === 'EN' ? 'Email' : '电子邮件',
    emailValue: 'support@fatematrices.com',
    responseTime: lang === 'EN'
      ? 'We aim to respond to all inquiries within 24–48 hours.'
      : '我们力争在 24-48 小时内回复所有咨询。',
    subjects: lang === 'EN'
      ? [
          { label: 'Order & Payment Support', desc: 'Questions about orders, payments, or refunds' },
          { label: 'Report Issues', desc: 'Problems with report generation or delivery' },
          { label: 'Technical Support', desc: 'Website bugs or technical difficulties' },
          { label: 'General Inquiries', desc: 'Partnerships, media, or other questions' },
        ]
      : [
          { label: '订单与付款支持', desc: '关于订单、付款或退款的问题' },
          { label: '报告问题', desc: '报告生成或交付出现问题' },
          { label: '技术支持', desc: '网站故障或技术困难' },
          { label: '一般咨询', desc: '合作、媒体或其他问题' },
        ],
  }), [lang]);

  return (
    <div className="min-h-screen bg-[#030712] text-white">
      <header className="flex items-center justify-between p-4 md:p-6 border-b border-gray-800/50">
        <button
          onClick={() => router.push('/')}
          className="text-cyan-400 hover:text-cyan-300 text-sm font-mono uppercase tracking-wider transition-colors"
        >
          {t.back}
        </button>
        <div className="flex gap-2">
          <button
            onClick={() => setLang('EN')}
            className={`px-3 py-1 rounded-lg text-xs uppercase tracking-wider transition-all ${
              lang === 'EN' ? 'bg-cyan-500 text-black font-bold' : 'text-gray-400 hover:text-white'
            }`}
          >
            EN
          </button>
          <button
            onClick={() => setLang('CN')}
            className={`px-3 py-1 rounded-lg text-xs uppercase tracking-wider transition-all ${
              lang === 'CN' ? 'bg-cyan-500 text-black font-bold' : 'text-gray-400 hover:text-white'
            }`}
          >
            中文
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 md:px-8 py-12 md:py-20">
        <h1 className="text-3xl md:text-5xl font-black uppercase tracking-tighter mb-2 text-white">
          {t.title}
        </h1>
        <p className="text-gray-500 text-xs uppercase tracking-[0.3em] font-mono mb-10 md:mb-16">
          {t.lastUpdated}
        </p>

        <p className="text-gray-300 text-sm md:text-base leading-relaxed mb-10 md:mb-16">
          {t.intro}
        </p>

        {/* Email card */}
        <div className="border border-gray-800/70 rounded-2xl p-6 md:p-8 mb-10 md:mb-16 bg-gray-900/40">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-lg">
              ✉
            </div>
            <div>
              <p className="text-gray-500 text-xs uppercase tracking-wider font-mono">{t.emailLabel}</p>
              <a
                href={`mailto:${t.emailValue}`}
                className="text-cyan-400 hover:text-cyan-300 text-lg font-bold transition-colors"
              >
                {t.emailValue}
              </a>
            </div>
          </div>
          <p className="text-gray-400 text-sm">{t.responseTime}</p>
        </div>

        {/* Inquiry topics */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-cyan-400 uppercase tracking-wide mb-4">
            {lang === 'EN' ? 'Common Topics' : '常见问题主题'}
          </h2>
          {t.subjects.map((item, i) => (
            <div key={i} className="border border-gray-800/50 rounded-xl p-4 md:p-5">
              <p className="text-white font-bold text-sm mb-1">{item.label}</p>
              <p className="text-gray-500 text-xs">{item.desc}</p>
            </div>
          ))}
        </div>
      </main>

      <footer className="border-t border-gray-800/50 py-8 text-center">
        <p className="text-gray-600 text-xs uppercase tracking-[0.3em] font-mono">
          FateMatrices © 2026
        </p>
      </footer>
    </div>
  );
}
