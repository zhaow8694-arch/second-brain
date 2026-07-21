'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';

export default function RefundPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'EN' | 'CN'>('EN');

  const t = useMemo(() => ({
    back: lang === 'EN' ? '← Back to Home' : '← 返回首页',
    title: lang === 'EN' ? 'Refund Policy' : '退款政策',
    lastUpdated: lang === 'EN' ? 'Last updated: June 2026' : '最后更新：2026年6月',
    intro: lang === 'EN'
      ? 'This Refund Policy describes when refunds may be issued for purchases made on FateMatrices. By making a purchase, you acknowledge that you have read and agree to this policy.'
      : '本退款政策描述了在 FateMatrices 上购买商品时可能获得退款的情形。进行购买即表示您确认已阅读并同意本政策。',
    sections: [
      {
        heading: lang === 'EN' ? '1. Digital Content & No-Refund Rule' : '1. 数字内容与不予退款规则',
        body: lang === 'EN'
          ? 'All reports sold on FateMatrices are digital content delivered electronically. Once a report has started generating or has been delivered, all sales are final and non-refundable. This is because the digital content has been made available to you and cannot be returned.'
          : 'FateMatrices 上出售的所有报告均为电子交付的数字内容。一旦报告开始生成或已交付，所有销售均为最终交易，不予退款。这是因为数字内容已向您提供且无法退回。',
      },
      {
        heading: lang === 'EN' ? '2. Exceptions – When Refunds May Be Issued' : '2. 例外情况——可能获得退款的情形',
        body: lang === 'EN'
          ? 'Refunds may be issued in the following circumstances only:\n• Duplicate or accidental double charges\n• Technical failure where the report could not be delivered after payment\n• Unauthorized transaction (validated by payment provider)\n• Required by applicable law or payment network rules (e.g., consumer protection laws in your jurisdiction)'
          : '仅在以下情况下可能获得退款：\n• 重复或意外双重扣款\n• 付款后报告因技术故障无法交付\n• 未经授权的交易（经支付服务商验证）\n• 适用法律或支付网络规则要求（例如您所在司法管辖区的消费者保护法）',
      },
      {
        heading: lang === 'EN' ? '3. How to Request a Refund' : '3. 如何申请退款',
        body: lang === 'EN'
          ? 'To request a refund, contact us at support@fatematrices.com within 14 days of the transaction, providing your order ID and the reason for the request. We will review your request and respond within 5 business days. Refunds, if approved, will be issued to the original payment method.'
          : '如需申请退款，请在交易后 14 天内联系 support@fatematrices.com，提供您的订单 ID 和申请理由。我们将审核您的请求并在 5 个工作日内回复。如获批准，退款将退回原付款方式。',
      },
      {
        heading: lang === 'EN' ? '4. Chargebacks & Disputes' : '4. 拒付与争议',
        body: lang === 'EN'
          ? 'Before filing a chargeback or payment dispute, please contact us first at support@fatematrices.com. We will work with you to resolve the issue. Filing a chargeback without contacting us may result in your account being blocked from future purchases.'
          : '在提出拒付或支付争议之前，请先联系 support@fatematrices.com。我们将与您合作解决问题。在未联系我们的情况下提出拒付，可能导致您的账户被禁止未来购买。',
      },
      {
        heading: lang === 'EN' ? '5. Processing Time' : '5. 处理时间',
        body: lang === 'EN'
          ? 'Approved refunds typically take 5–10 business days to appear in your account, depending on your payment provider and bank. FateMatrices is not responsible for delays caused by your bank or payment provider.'
          : '获批的退款通常需要 5-10 个工作日到账，具体取决于您的支付服务商和银行。FateMatrices 不对因您的银行或支付服务商造成的延迟负责。',
      },
      {
        heading: lang === 'EN' ? '6. Contact' : '6. 联系方式',
        body: lang === 'EN'
          ? 'For any refund-related questions, please contact us at: support@fatematrices.com'
          : '如有任何退款相关问题，请联系：support@fatematrices.com',
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
        <p className="text-gray-500 text-xs uppercase tracking-[0.3em] font-mono mb-6 md:mb-8">
          {t.lastUpdated}
        </p>
        <p className="text-gray-300 text-sm md:text-base leading-relaxed mb-10 md:mb-16">
          {t.intro}
        </p>

        <div className="space-y-10 md:space-y-14">
          {t.sections.map((section, i) => (
            <section key={i}>
              <h2 className="text-lg md:text-xl font-bold text-cyan-400 mb-3 md:mb-4 uppercase tracking-wide">
                {section.heading}
              </h2>
              <p className="text-gray-300 text-sm md:text-base leading-relaxed whitespace-pre-line">
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
