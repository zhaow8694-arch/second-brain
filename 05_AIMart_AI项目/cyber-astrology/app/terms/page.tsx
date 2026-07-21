'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';

export default function TermsPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'EN' | 'CN'>('EN');

  const t = useMemo(() => ({
    back: lang === 'EN' ? '← Back to Home' : '← 返回首页',
    title: lang === 'EN' ? 'Terms of Service' : '服务条款',
    lastUpdated: lang === 'EN' ? 'Last updated: June 2026' : '最后更新：2026年6月',
    sections: [
      {
        heading: lang === 'EN' ? '1. Acceptance of Terms' : '1. 条款接受',
        body: lang === 'EN'
          ? 'By accessing or using FateMatrices (the "Service"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.'
          : '访问或使用 FateMatrices（"服务"），即表示您同意受本服务条款的约束。如果您不同意，请勿使用本服务。',
      },
      {
        heading: lang === 'EN' ? '2. Description of Service' : '2. 服务描述',
        body: lang === 'EN'
          ? 'FateMatrices provides AI-generated astrology, tarot, zodiac, and personality entertainment reports ("Reports"). Reports are generated digitally and delivered after payment. The Service is for entertainment and personal insight only.'
          : 'FateMatrices 提供 AI 生成的占星、塔罗、星座和性格娱乐报告（"报告"）。报告以数字方式生成，付款后交付。本服务仅用于娱乐和个人参考。',
      },
      {
        heading: lang === 'EN' ? '3. Eligibility' : '3. 使用资格',
        body: lang === 'EN'
          ? 'You must be at least 18 years old to use this Service. By using the Service, you represent that you are 18 or older.'
          : '您必须年满 18 岁才能使用本服务。使用本服务即表示您确认已满 18 岁。',
      },
      {
        heading: lang === 'EN' ? '4. Payment & No-Refund Policy' : '4. 付款与不予退款政策',
        body: lang === 'EN'
          ? 'Payments are processed through our payment providers (PayPal, USDT/TRC20). Once a Report has started generating or has been delivered, all sales are final and non-refundable, except where required by applicable law or payment network rules. See our Refund Policy for details.'
          : '付款通过我们的支付服务商（PayPal、USDT/TRC20）处理。一旦报告开始生成或已交付，所有销售均为最终交易，不予退款，适用法律或支付网络规则要求的除外。详见退款政策。',
      },
      {
        heading: lang === 'EN' ? '5. Disclaimer' : '5. 免责声明',
        body: lang === 'EN'
          ? 'Reports are for entertainment purposes only. They do not constitute financial, legal, medical, investment, or life-decision advice. No guarantees are made regarding real-world outcomes. You are solely responsible for any decisions or actions taken based on the Reports.'
          : '报告仅供娱乐用途。不构成财务、法律、医疗、投资或人生决策建议。不对现实世界的结果作出任何保证。您对所基于报告做出的任何决定或行动承担全部责任。',
      },
      {
        heading: lang === 'EN' ? '6. Intellectual Property' : '6. 知识产权',
        body: lang === 'EN'
          ? 'All content, trademarks, and code on this Service are the property of FateMatrices. You may not copy, reproduce, or distribute any part of the Service without written permission.'
          : '本服务上的所有内容、商标和代码均为 FateMatrices 的财产。未经书面许可，您不得复制、转载或分发本服务的任何部分。',
      },
      {
        heading: lang === 'EN' ? '7. Limitation of Liability' : '7. 责任限制',
        body: lang === 'EN'
          ? 'To the maximum extent permitted by law, FateMatrices shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the Service.'
          : '在法律允许的最大范围内，FateMatrices 不对因您使用本服务而产生的任何间接、附带、特殊或后果性损害承担责任。',
      },
      {
        heading: lang === 'EN' ? '8. Changes to Terms' : '8. 条款修改',
        body: lang === 'EN'
          ? 'We reserve the right to modify these Terms at any time. Changes will be posted on this page with an updated date. Continued use of the Service constitutes acceptance of the modified Terms.'
          : '我们保留随时修改本条款的权利。修改内容将发布在本页面并注明更新日期。继续使用本服务即表示接受修改后的条款。',
      },
      {
        heading: lang === 'EN' ? '9. Contact' : '9. 联系方式',
        body: lang === 'EN'
          ? 'For questions about these Terms, please contact us at: support@fatematrices.com'
          : '如有关于本条款的问题，请联系：support@fatematrices.com',
      },
    ],
  }), [lang]);

  return (
    <div className="min-h-screen bg-[#030712] text-white">
      {/* Header */}
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

      {/* Content */}
      <main className="max-w-3xl mx-auto px-4 md:px-8 py-12 md:py-20">
        <h1 className="text-3xl md:text-5xl font-black uppercase tracking-tighter mb-2 text-white">
          {t.title}
        </h1>
        <p className="text-gray-500 text-xs uppercase tracking-[0.3em] font-mono mb-10 md:mb-16">
          {t.lastUpdated}
        </p>

        <div className="space-y-10 md:space-y-14">
          {t.sections.map((section, i) => (
            <section key={i}>
              <h2 className="text-lg md:text-xl font-bold text-cyan-400 mb-3 md:mb-4 uppercase tracking-wide">
                {section.heading}
              </h2>
              <p className="text-gray-300 text-sm md:text-base leading-relaxed">
                {section.body}
              </p>
            </section>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-8 text-center">
        <p className="text-gray-600 text-xs uppercase tracking-[0.3em] font-mono">
          FateMatrices © 2026
        </p>
      </footer>
    </div>
  );
}
