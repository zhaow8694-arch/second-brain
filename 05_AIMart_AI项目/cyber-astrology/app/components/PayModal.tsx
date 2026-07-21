'use client';

import React, { useState } from 'react';
import { QRCodeCanvas } from 'qrcode.react';

type PlanType = { id: 'LITE' | 'ELITE'; price: string };
type PaymentMethod = 'TRC20' | 'PAYPAL' | 'PAYONEER';

interface PayModalProps {
  show: boolean;
  selectedPlan: PlanType | null;
  TRC20_ADDR: string;
  currentOrderId: string | null;
  walletTail: string;
  setWalletTail: (val: string) => void;
  isChecking: boolean;
  onVerify: () => void;
  onPayPalPay: () => void;              // triggers PayPal flow
  onClose: () => void;
  paymentMethod: PaymentMethod;
  onSwitchMethod: (method: PaymentMethod) => void;
  payoneerPaymentId?: string | null;
  paypalProcessing?: boolean;            // PayPal modal state
  artifactMode?: boolean;               // 周边商品模式：只显示 TRC20
  t: {
    modalTitle: string;
    copied: string;
    modalCopy: string;
    memoRequired: string;
    memoHint: string;
    walletTailHint: string;
    modalVerify: string;
    modalVerifying: string;
    modalCancel: string;
    payoneerTitle: string;
    payoneerAccountName: string;
    payoneerRouting: string;
    payoneerAccount: string;
    payoneerBank: string;
    payoneerRef: string;
    payoneerCopyRef: string;
    payoneerInstruction: string;
    payoneerTrc20: string;
    payoneerWire: string;
    payoneerTrc20Desc: string;
    payoneerWireDesc: string;
    paypalBtn: string;
    paypalDesc: string;
  };
}

export const PayModal: React.FC<PayModalProps> = ({
  show,
  selectedPlan,
  TRC20_ADDR,
  currentOrderId,
  walletTail,
  setWalletTail,
  isChecking,
  onVerify,
  onPayPalPay,
  onClose,
  paymentMethod,
  onSwitchMethod,
  payoneerPaymentId,
  paypalProcessing,
  artifactMode,
  t
}) => {
  const [copied, setCopied] = useState(false);

  if (!show || !selectedPlan) return null;

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const methods: { key: PaymentMethod; label: string; desc: string }[] = artifactMode
    ? [{ key: 'TRC20', label: 'USDT (TRC20)', desc: 'Crypto' }]
    : [
        { key: 'TRC20',    label: 'USDT (TRC20)', desc: 'Crypto' },
        { key: 'PAYPAL',   label: 'PayPal',       desc: 'Card / Wallet' },
        { key: 'PAYONEER', label: 'Wire',          desc: 'Bank Transfer' },
      ];

  return (
    <div
      className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-xl flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={t.modalTitle}
    >
      <div
        className="bg-[#0a0f1d] border border-gray-800 p-8 rounded-[3rem] max-w-sm w-full space-y-6 text-center shadow-2xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-2xl font-black italic text-cyan-400 uppercase tracking-tighter">{t.modalTitle}</h3>

        {/* 支付方式切换 — 3 columns */}
        <div className="flex gap-2">
          {methods.map(m => (
            <button
              key={m.key}
              onClick={() => onSwitchMethod(m.key)}
              className={`flex-1 p-3 rounded-xl border text-[10px] font-black uppercase tracking-widest transition-all ${
                paymentMethod === m.key
                  ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-400'
                  : 'bg-gray-900/50 border-gray-800 text-gray-500 hover:border-gray-600'
              }`}
            >
              <div>{m.label}</div>
              <div className="text-[8px] font-normal mt-0.5 opacity-60">{m.desc}</div>
            </button>
          ))}
        </div>

        {/* ── PayPal 支付 ──────────────────────── */}
        {paymentMethod === 'PAYPAL' && (
          <div className="p-6 bg-black rounded-[2.5rem] border border-gray-800 flex flex-col items-center space-y-4">
            <div className="text-4xl font-black text-white">${selectedPlan.price} USD</div>

            <div className="w-full p-4 bg-[#0070ba]/10 rounded-2xl border border-[#0070ba]/30 text-center">
              <p className="text-[10px] text-gray-400 uppercase tracking-wider mb-3">
                {t.paypalDesc}
              </p>
              <img
                src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_111x69.jpg"
                alt="PayPal"
                className="h-8 mx-auto mb-2"
              />
            </div>

            <button
              onClick={onPayPalPay}
              disabled={isChecking || paypalProcessing}
              className="w-full py-4 bg-[#0070ba] rounded-2xl font-black uppercase tracking-widest text-xs hover:bg-[#005c9e] focus:outline-none focus:ring-4 focus:ring-[#0070ba]/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              aria-label={t.paypalBtn}
            >
              {paypalProcessing
                ? (t.modalVerifying || 'Processing...')
                : t.paypalBtn}
            </button>
          </div>
        )}

        {/* ── TRC20 支付 ──────────────────────── */}
        {paymentMethod === 'TRC20' && (
          <div className="p-6 bg-black rounded-[2.5rem] border border-gray-800 flex flex-col items-center space-y-4">
            <div className="text-4xl font-black text-white">${selectedPlan.price} USDT</div>
            <div className="bg-white p-2 rounded-2xl">
              <QRCodeCanvas value={TRC20_ADDR} size={140} />
            </div>
            <div className="w-full space-y-2 mt-2">
              <div className="text-[9px] font-mono text-cyan-500 break-all bg-gray-900/80 p-4 rounded-2xl border border-gray-800">
                {TRC20_ADDR}
              </div>
              <button
                onClick={() => { navigator.clipboard.writeText(TRC20_ADDR); alert(t.copied); }}
                className="w-full py-3 bg-cyan-500/10 text-cyan-500 border border-cyan-500/30 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-cyan-500 hover:text-white transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500"
                aria-label={t.modalCopy}
              >
                {t.modalCopy}
              </button>

              {currentOrderId && (
                <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                  <p className="text-[10px] text-yellow-400 font-black uppercase tracking-widest mb-1">
                    {t.memoRequired}
                  </p>
                  <p className="text-xs text-gray-300 mb-2">
                    {t.memoHint}
                  </p>
                  <div className="bg-black/50 p-2 rounded-lg border border-yellow-500/50">
                    <code className="text-lg font-bold text-yellow-400 tracking-widest">{currentOrderId}</code>
                  </div>
                </div>
              )}
            </div>

            <div className="text-left w-full pt-2">
              <label className="text-[10px] text-cyan-500 font-black uppercase tracking-widest ml-1">{t.walletTailHint}</label>
              <input
                type="text"
                maxLength={4}
                value={walletTail}
                onChange={e => setWalletTail(e.target.value.toUpperCase())}
                className="w-full mt-1.5 p-4 bg-gray-900 border border-gray-800 rounded-2xl text-center text-white outline-none focus:border-cyan-500 uppercase font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500"
                aria-label={t.walletTailHint}
                pattern="[0-9A-Za-z]{4}"
                inputMode="text"
              />
            </div>

            <button
              onClick={onVerify}
              disabled={isChecking}
              className="w-full py-5 bg-blue-600 rounded-2xl font-black uppercase tracking-widest text-xs hover:bg-blue-500 focus:outline-none focus:ring-4 focus:ring-cyan-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label={t.modalVerify}
              aria-busy={isChecking}
            >
              {isChecking ? t.modalVerifying : t.modalVerify}
            </button>
          </div>
        )}

        {/* ── Payoneer 电汇 ──────────────────── */}
        {paymentMethod === 'PAYONEER' && (
          <div className="p-6 bg-black rounded-[2.5rem] border border-gray-800 space-y-4">
            <div className="text-4xl font-black text-white">${selectedPlan.price} USD</div>
            <div className="text-[10px] text-gray-400 uppercase tracking-wider">
              {t.payoneerTitle}
            </div>
            <div className="space-y-3 text-left">
              <div className="bg-gray-900/80 p-3 rounded-xl border border-gray-800">
                <div className="text-[9px] text-cyan-500 uppercase tracking-widest mb-1">{t.payoneerBank}</div>
                <div className="text-xs text-white font-mono">First Century Bank, NA</div>
              </div>
              <div className="bg-gray-900/80 p-3 rounded-xl border border-gray-800">
                <div className="text-[9px] text-cyan-500 uppercase tracking-widest mb-1">{t.payoneerAccountName}</div>
                <div className="text-xs text-white font-mono">
                  {process.env.NEXT_PUBLIC_PAYONEER_ACCOUNT_NAME || '************'}
                </div>
              </div>
              <div className="bg-gray-900/80 p-3 rounded-xl border border-gray-800">
                <div className="text-[9px] text-cyan-500 uppercase tracking-widest mb-1">{t.payoneerRouting}</div>
                <div className="text-xs text-white font-mono">
                  {process.env.NEXT_PUBLIC_PAYONEER_ROUTING_NUMBER || '************'}
                </div>
              </div>
              <div className="bg-gray-900/80 p-3 rounded-xl border border-gray-800">
                <div className="text-[9px] text-cyan-500 uppercase tracking-widest mb-1">{t.payoneerAccount}</div>
                <div className="text-xs text-white font-mono">
                  {process.env.NEXT_PUBLIC_PAYONEER_ACCOUNT_NUMBER || '************'}
                </div>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-3">
                <div className="text-[9px] text-yellow-400 uppercase tracking-widest mb-1">{t.payoneerRef}</div>
                <div className="flex items-center justify-between gap-2">
                  <code className="text-sm font-bold text-yellow-400 tracking-widest">
                    {payoneerPaymentId || 'REF-********'}
                  </code>
                  <button
                    onClick={() => handleCopy(payoneerPaymentId || 'REF-********')}
                    className="text-[9px] px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition-colors"
                  >
                    {copied ? t.copied : t.payoneerCopyRef}
                  </button>
                </div>
              </div>
            </div>
            <p className="text-[10px] text-gray-500 leading-relaxed">{t.payoneerInstruction}</p>
          </div>
        )}

        <button
          onClick={onClose}
          className="text-[10px] text-gray-600 uppercase font-bold tracking-widest hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500"
          aria-label={t.modalCancel}
        >
          {t.modalCancel}
        </button>
      </div>
    </div>
  );
};
