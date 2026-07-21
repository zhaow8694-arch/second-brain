'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';

export default function PrivacyPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'EN' | 'CN'>('EN');

  const t = useMemo(() => ({
    back: lang === 'EN' ? '← Back to Home' : '← 返回首页',
    title: lang === 'EN' ? 'Privacy Policy' : '隐私政策',
    lastUpdated: lang === 'EN' ? 'Last updated: June 2026' : '最后更新：2026年6月',
    sections: [
      {
        heading: lang === 'EN' ? '1. Information We Collect' : '1. 我们收集的信息',
        body: lang === 'EN'
          ? 'We collect information you provide when using our Service, including: name, email address, birth date/time/place (for astrology reports), payment information (processed by our payment providers, not stored by us), and usage data such as IP address and browser type.'
          : '我们收集您使用服务时提供的信息，包括：姓名、电子邮件地址、出生日期/时间/地点（用于占星报告）、付款信息（由我们的支付服务商处理，我们不存储），以及使用数据如 IP 地址和浏览器类型。',
      },
      {
        heading: lang === 'EN' ? '2. How We Use Your Information' : '2. 我们如何使用您的信息',
        body: lang === 'EN'
          ? 'We use your information to: generate personalized reports, process payments, communicate with you about your orders, improve our Service, and comply with legal obligations. We do not sell your personal information to third parties.'
          : '我们使用您的信息来：生成个性化报告、处理付款、就您的订单与您沟通、改进我们的服务，以及遵守法律义务。我们不会将您的个人信息出售给第三方。',
      },
      {
        heading: lang === 'EN' ? '3. Data Storage & Security' : '3. 数据存储与安全',
        body: lang === 'EN'
          ? 'Your data is stored securely using industry-standard encryption. Birth data and personal information are processed to generate your report and are not permanently stored unless you create an account. Payment data is handled by our payment processors (PayPal, blockchain networks) and is subject to their privacy policies.'
          : '您的数据使用行业标准加密安全存储。出生数据和个人信息仅用于处理生成您的报告，除非您创建账户，否则不会永久存储。付款数据由我们的支付处理商（PayPal、区块链网络）处理，并受其隐私政策约束。',
      },
      {
        heading: lang === 'EN' ? '4. Cookies & Tracking' : '4. Cookie 与追踪',
        body: lang === 'EN'
          ? 'We use essential cookies to operate the Service. We may also use analytics cookies to understand how visitors use our site. You can control cookie settings through your browser preferences.'
          : '我们使用必要的 Cookie 来运营服务。我们也可能使用分析 Cookie 来了解访问者如何使用我们的网站。您可以通过浏览器偏好设置控制 Cookie。',
      },
      {
        heading: lang === 'EN' ? '5. Third-Party Services' : '5. 第三方服务',
        body: lang === 'EN'
          ? 'Our Service integrates with third-party providers including PayPal (payment processing), TronGrid/Tron network (USDT payments), and AI model providers (report generation). These services have their own privacy policies.'
          : '我们的服务集成了第三方提供商，包括 PayPal（支付处理）、TronGrid/Tron 网络（USDT 付款）和 AI 模型提供商（报告生成）。这些服务有自己的隐私政策。',
      },
      {
        heading: lang === 'EN' ? '6. Your Rights' : '6. 您的权利',
        body: lang === 'EN'
          ? 'Depending on your jurisdiction, you may have rights including: access to your data, correction of inaccurate data, deletion of your data, and data portability. To exercise these rights, contact us at support@fatematrices.com.'
          : '根据您的司法管辖区，您可能拥有以下权利：访问您的数据、更正不准确的数据、删除您的数据，以及数据可携带权。要行使这些权利，请联系 support@fatematrices.com。',
      },
      {
        heading: lang === 'EN' ? '7. Children\'s Privacy' : '7. 儿童隐私',
        body: lang === 'EN'
          ? 'Our Service is not intended for children under 18. We do not knowingly collect personal information from children under 18. If you believe we have collected such information, please contact us immediately.'
          : '我们的服务不适用于 18 岁以下的儿童。我们不会故意收集 18 岁以下儿童的个人信息。如果您认为我们收集了此类信息，请立即联系我们。',
      },
      {
        heading: lang === 'EN' ? '8. Changes to This Policy' : '8. 政策修改',
        body: lang === 'EN'
          ? 'We may update this Privacy Policy from time to time. Changes will be posted on this page with an updated date. Significant changes will be notified via email or site notice.'
          : '我们可能会不时更新本隐私政策。修改内容将发布在本页面并注明更新日期。重大修改将通过电子邮件或网站通知告知。',
      },
      {
        heading: lang === 'EN' ? '9. Contact' : '9. 联系方式',
        body: lang === 'EN'
          ? 'For questions about this Privacy Policy, please contact us at: support@fatematrices.com'
          : '如有关于本隐私政策的问题，请联系：support@fatematrices.com',
      },
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

      <footer className="border-t border-gray-800/50 py-8 text-center">
        <p className="text-gray-600 text-xs uppercase tracking-[0.3em] font-mono">
          FateMatrices © 2026
        </p>
      </footer>
    </div>
  );
}
