'use client';

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// 动态导入重型组件
const RadarChartComponent = dynamic(() => import('recharts').then(mod => mod.RadarChart), { ssr: false });
const RadarComponent = dynamic(() => import('recharts').then(mod => mod.Radar), { ssr: false });
const PolarGridComponent = dynamic(() => import('recharts').then(mod => mod.PolarGrid), { ssr: false });
const PolarAngleAxisComponent = dynamic(() => import('recharts').then(mod => mod.PolarAngleAxis), { ssr: false });
const PolarRadiusAxisComponent = dynamic(() => import('recharts').then(mod => mod.PolarRadiusAxis), { ssr: false });
const ResponsiveContainerComponent = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });

const PayModal = dynamic(() => import('../components/PayModal').then(mod => mod.PayModal), { ssr: false });
const ArtifactRecommender = dynamic(() => import('../components/ArtifactRecommender').then(mod => mod.ArtifactRecommender), { ssr: false });
const LoadingSkeleton = dynamic(() => import('../components/LoadingSkeleton').then(mod => mod.LoadingSkeleton), { ssr: false });

const ZODIACS_CN = [
  "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
  "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"
];
const ZODIACS_EN = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];
const MBTIS = [
  "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"
];

type PlanType = { id: 'LITE' | 'ELITE'; price: string };
type ReadLevel = 'NONE' | 'PART1' | 'PART2' | 'PAID';

export default function ZodiacRoomPage() {
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);
  const [lang, setLang] = useState<'EN' | 'CN'>('CN');
  const [isNavigating, setIsNavigating] = useState(false);

  const ZODIACS = lang === 'EN' ? ZODIACS_EN : ZODIACS_CN;
  const [selfSign, setSelfSign] = useState(ZODIACS[0]);
  const [mbti, setMbti] = useState("");
  const [partnerSign, setPartnerSign] = useState("");

  const [interpretation, setInterpretation] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [readLevel, setReadLevel] = useState<ReadLevel>('NONE');

  const [radarData, setRadarData] = useState<Array<{ subject: string; A: number }>>([]);
  const [luckyTags, setLuckyTags] = useState({ color: '', freq: '', num: '' });
  const [signElement, setSignElement] = useState('');

  const [isWaitingForFriend, setIsWaitingForFriend] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [showPayModal, setShowPayModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<PlanType | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [walletTail, setWalletTail] = useState('');
  const [shareUrl, setShareUrl] = useState('');
  const [currentOrderId, setCurrentOrderId] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<'TRC20' | 'PAYPAL' | 'PAYONEER'>('TRC20');
  const [payoneerPaymentId, setPayoneerPaymentId] = useState<string | null>(null);
  const [paypalProcessing, setPaypalProcessing] = useState(false);
  const [artifactMode, setArtifactMode] = useState(false);

  const TRC20_ADDR = process.env.NEXT_PUBLIC_TRC20_ADDR || "TY2E8XcYbdX6ZsBbU166EbWowGusBP9Aw1";

  useEffect(() => {
    setIsMounted(true);
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const l = params.get('lang');
      if (l === 'EN' || l === 'CN') setLang(l);
      
      const refId = params.get('ref');
      if (refId) {
        fetch(`/api/share?id=${refId}&action=click`).catch(err => console.warn('Share click tracking failed:', err));
      }
      
      setShareUrl(window.location.origin + window.location.pathname);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const currentZodiacs = lang === 'EN' ? ZODIACS_EN : ZODIACS_CN;
    if (!currentZodiacs.includes(selfSign)) {
      setSelfSign(currentZodiacs[0]);
    }
  }, [lang, selfSign]);

  const t = useMemo(() => ({
    back: lang === 'EN' ? '← Back' : '← 返回',
    title: lang === 'EN' ? 'Zodiac Nebula' : '赛博星盘',
    sub: lang === 'EN' ? 'Sign & MBTI Synergy' : '占星学与 MBTI 量子协同',
    labelSelf: lang === 'EN' ? 'Your Sign' : '你的星座',
    labelMbti: lang === 'EN' ? 'Your MBTI (Opt)' : '你的 MBTI (加成)',
    labelPartner: lang === 'EN' ? 'Partner Sign (Opt)' : '对方星座 (匹配模式)',
    btnGen1: lang === 'EN' ? 'Generate Astral Teaser' : '提取星盘预告',
    denied: lang === 'EN' ? '... (Access Denied / Signal Encrypted)' : '... (权限不足，核心星语已加密)',
    shareTip: lang === 'EN' ? 'Share link to unlock Part 2' : '【分享链接给好友，点开即可解锁第二段星语】',
    btnShare: lang === 'EN' ? '🔗 Share to Unlock' : '🔗 分享并解锁下文',
    waiting: lang === 'EN' ? 'Resonance Monitoring...' : '正在监测量子共振...',
    btnManual: lang === 'EN' ? 'I have shared, unlock now' : '我已分享，立即解锁',
    skipWait: lang === 'EN' ? 'Pay 10U to Unlock All' : '直接支付 10U 立即解锁全部',
    friendClicked: lang === 'EN' ? 'Unlocked! Pay for final truth:' : '星语已解锁。核心破局真相请支付查看：',
    modalTitle: lang === 'EN' ? 'Offer Sacrifice' : '向星空献祭',
    modalVerify: lang === 'EN' ? 'Verify Paid' : '确认已支付',
    modalVerifying: lang === 'EN' ? 'Verifying...' : '验证中...',
    walletTailHint: lang === 'EN' ? 'Wallet Last 4 Chars' : '付款钱包尾号(后4位)',
    walletTip: lang === 'EN' ? 'Please enter 4 digits' : '请输入钱包后4位',
    verifyBtn: lang === 'EN' ? 'Verify Paid' : '确认已支付',
    emptySelf: lang === 'EN' ? 'Please select your sign' : '请选择您的星座',
    liteName: lang === 'EN' ? 'Basic Astrology' : '基础星盘解析',
    eliteName: lang === 'EN' ? 'Deep Karma Unlock' : '宿命深度解锁',
    modalCopy: lang === 'EN' ? 'COPY ADDRESS' : '复制地址',
    modalCancel: lang === 'EN' ? 'Cancel' : '取消支付',
    verifying: lang === 'EN' ? 'Verifying...' : '验证中...',
    copied: lang === 'EN' ? 'Copied!' : '已复制！',
    analyzing: lang === 'EN' ? 'Syncing...' : '同步中...',
    syncFailed: lang === 'EN' ? 'Quantum link lost.' : '量子链接丢失。',
    linkCopied: lang === 'EN' ? '🔗 Link copied!' : '🔗 链接已复制！',
    copyFailed: lang === 'EN' ? 'Copy failed, please try manually' : '复制失败，请手动复制',
    langEN: lang === 'EN' ? 'Switch to English' : '切换到英文',
    langCN: lang === 'EN' ? 'Switch to Chinese' : '切换到中文',
    loading: lang === 'EN' ? 'Loading Zodiac Nebula...' : '正在加载赛博星盘...',
    networkError: lang === 'EN' ? 'Network or Server Error.' : '网络或服务器错误。',
    alertWait: lang === 'EN' ? 'Payment not found. Ensure transfer is complete and memo is correct.' : '未扫描到账单，请确认转账已完成且备注正确。',
    memoRequired: lang === 'EN' ? '⚠️ MEMO REQUIRED' : '⚠️ 必须填写备注',
    memoHint: lang === 'EN' ? 'Please include this code in transfer memo:' : '转账时请在备注填写：',
    payoneerTitle: lang === 'EN' ? 'Bank Transfer' : '银行电汇',
    payoneerAccountName: lang === 'EN' ? 'Account Name' : '收款账户名',
    payoneerRouting: lang === 'EN' ? 'Routing Number' : '路由号码',
    payoneerAccount: lang === 'EN' ? 'Account Number' : '账户号码',
    payoneerBank: lang === 'EN' ? 'Bank Name' : '银行名称',
    payoneerRef: lang === 'EN' ? 'Reference Code' : '汇款参考号',
    payoneerCopyRef: lang === 'EN' ? 'Copy' : '复制',
    payoneerInstruction: lang === 'EN' ? 'Please include the reference code in your wire transfer. Payment will be verified within 1-2 business days.' : '请在国际电汇时填写汇款参考号，收款后1-2个工作日内自动解锁。',
    payoneerTrc20: lang === 'EN' ? 'USDT (TRC20)' : 'USDT (TRC20)',
    payoneerWire: lang === 'EN' ? 'Wire Transfer' : '银行电汇',
    payoneerTrc20Desc: lang === 'EN' ? 'Instant' : '即时到账',
    payoneerWireDesc: lang === 'EN' ? '1-2 Days' : '1-2个工作日',
    paypalBtn: lang === 'EN' ? 'Pay with PayPal' : 'PayPal 支付',
    paypalDesc: lang === 'EN' ? 'Credit / Debit Card or PayPal' : '信用卡 / 借记卡 或 PayPal',
  }), [lang]);

  const navigateBack = useCallback(async () => {
    if (isNavigating) return;
    setIsNavigating(true);
    try {
      await router.push(`/?lang=${lang}`);
    } catch (error) {
      console.error('Navigation error:', error);
    } finally {
      setIsNavigating(false);
    }
  }, [isNavigating, router, lang]);

  const handleCalculate = useCallback(async (pType: string, orderId?: string) => {
    if (!selfSign) {
      alert(t.emptySelf);
      return;
    }

    setIsAnalyzing(true);
    setInterpretation('');

    if (pType === 'FREE_PART1') {
      const { analyzeZodiacFull } = await import('./zodiac-analysis');
      
      const result = analyzeZodiacFull(
        selfSign,
        mbti || null,
        partnerSign || null,
        lang as 'EN' | 'CN'
      );
      
      setRadarData([
        { subject: lang === 'EN' ? 'Wealth' : '财富', A: result.radar.wealth },
        { subject: lang === 'EN' ? 'Love' : '桃花', A: result.radar.love },
        { subject: lang === 'EN' ? 'Career' : '事业', A: result.radar.career },
        { subject: lang === 'EN' ? 'Health' : '健康', A: result.radar.health },
        { subject: lang === 'EN' ? 'Cyber' : '赛博运', A: result.radar.cyber },
      ]);
      
      setLuckyTags(result.luckyTags);

      // 根据星座匹配五行元素用于饰品推荐
      const signToElement: Record<string, string> = {
        "白羊座": "火", "狮子座": "火", "射手座": "火", "Aries": "火", "Leo": "火", "Sagittarius": "火",
        "金牛座": "土", "处女座": "土", "摩羯座": "土", "Taurus": "土", "Virgo": "土", "Capricorn": "土",
        "双子座": "金", "天秤座": "金", "水瓶座": "金", "Gemini": "金", "Libra": "金", "Aquarius": "金",
        "巨蟹座": "水", "天蝎座": "水", "双鱼座": "水", "Cancer": "水", "Scorpio": "水", "Pisces": "水"
      };
      setSignElement(signToElement[selfSign] || "金");
    }

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'zodiac',
          selfSign,
          partnerSign,
          mbti,
          plan: pType,
          lang,
          orderId: orderId || null,
        })
      });
      
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      
      // 处理流式响应
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulatedText = '';

      while (!done) {
        const { value, done: doneReading } = await reader!.read();
        done = doneReading;
        if (value) {
          const chunkValue = decoder.decode(value);
          accumulatedText += chunkValue;
          setInterpretation(accumulatedText);
        }
      }

      if (pType === 'FREE_PART1') setReadLevel('PART1');
      else if (pType === 'FREE_PART2') setReadLevel('PART2');
      else setReadLevel('PAID');
    } catch (error) {
      console.error('Calculation failed:', error);
      const isDev = process.env.NODE_ENV === 'development' || (typeof window !== 'undefined' && window.location.hostname === 'localhost');
      if (isDev) {
        setInterpretation(lang === 'EN' 
          ? " [DEMO MODE] The zodiac nebula aligns with your aura. Great cosmic energy is shifting in your favor. (Mock text)"
          : "【演示模式】星云矩阵已对齐你的个人气场。庞大的宇宙能量正转向对你有利的相位。（模拟文本）"
        );
        if (pType === 'FREE_PART1') setReadLevel('PART1');
        else if (pType === 'FREE_PART2') setReadLevel('PART2');
        else setReadLevel('PAID');
      } else {
        setInterpretation(t.syncFailed);
      }
    } finally {
      setIsAnalyzing(false);
    }
  }, [selfSign, partnerSign, mbti, t, lang]);

  const handleShareAndTrack = useCallback(async () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    
    const trackId = Math.random().toString(36).substring(2, 10);
    const url = new URL(shareUrl);
    url.searchParams.set('ref', trackId);
    url.searchParams.set('lang', lang);
    const trackableUrl = url.toString();
    
    let shared = false;
    const isMobile = typeof navigator !== 'undefined' && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const hasShareApi = typeof navigator !== 'undefined' && navigator.share;
    
    if (isMobile && hasShareApi) {
      try {
        await navigator.share({
          title: 'FateMatrices',
          text: lang === 'EN' ? 'Check my Zodiac!' : '我的星座运势太绝了！',
          url: trackableUrl
        });
        shared = true;
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('Native share failed:', error);
        }
      }
    }

    if (!shared) {
      try {
        await navigator.clipboard.writeText(trackableUrl);
        alert(t.linkCopied);
      } catch (error) {
        console.error('Copy failed:', error);
        alert(t.copyFailed);
        return;
      }
    }

    try {
      await fetch('/api/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: trackId })
      });
    } catch (error) {
      console.warn('Share tracking failed:', error);
    }

    setIsWaitingForFriend(true);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const checkRes = await fetch(`/api/share?id=${trackId}&action=check`);
        if (!checkRes.ok) return;
        
        const checkData = await checkRes.json();
        if (checkData.clicked) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setIsWaitingForFriend(false);
          handleCalculate('FREE_PART2');
        }
      } catch (error) {
        console.warn('Polling check failed:', error);
      }
    }, 3000);
  }, [shareUrl, lang, t, handleCalculate]);

  const handleOpenPayModal = useCallback(async (plan: PlanType, isArtifact = false) => {
    setSelectedPlan(plan);
    setPaymentMethod('TRC20');
    setShowPayModal(true);
    setPayoneerPaymentId(`PAY-${Date.now()}`);
    setArtifactMode(isArtifact);

    try {
      const res = await fetch('/api/verify-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: isArtifact
          ? JSON.stringify({ action: 'create', planId: 'ELITE', amount: plan.price, artifact: true })
          : JSON.stringify({ action: 'create', planId: plan.id })
      });
      const data = await res.json();
      if (data.success && data.orderId) {
        setCurrentOrderId(data.orderId);
      }
    } catch (error) {
      console.error('Failed to create order:', error);
    }
  }, []);

  const verifyPayment = useCallback(async () => {
    if (!selectedPlan || isChecking) return;
    
    const trimmedTail = walletTail.trim();
    if (trimmedTail.length !== 4 || !/^[0-9A-Za-z]{4}$/.test(trimmedTail)) {
      alert(t.walletTip);
      return;
    }

    setIsChecking(true);
    try {
      const response = await fetch('/api/verify-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: TRC20_ADDR,
          amount: selectedPlan.price,
          walletTail: trimmedTail,
          orderId: currentOrderId
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Backend verification failed');
      }
      
      const data = await response.json();

      if (data.success && data.found) {
        setShowPayModal(false);
        setWalletTail('');
        const paidOrderId = currentOrderId;
        setCurrentOrderId(null);
        if (artifactMode) {
          alert(lang === 'EN'
            ? 'Payment confirmed! We will contact you shortly for shipping details. Thank you!'
            : '支付已确认！我们会尽快联系你获取发货信息，感谢供奉！');
        } else {
          await handleCalculate(selectedPlan.id, paidOrderId || undefined);
        }
      } else {
        alert(t.alertWait);
      }
    } catch (error) {
      console.error('Payment verification failed:', error);
      alert(t.networkError);
    } finally {
      setIsChecking(false);
    }
  }, [selectedPlan, isChecking, walletTail, currentOrderId, t, handleCalculate, TRC20_ADDR, artifactMode, lang]);

  const handleSwitchPaymentMethod = useCallback((method: 'TRC20' | 'PAYPAL' | 'PAYONEER') => {
    setPaymentMethod(method);
    if (method === 'PAYONEER') {
      setPayoneerPaymentId(`PAY-${Date.now()}`);
    }
  }, []);

  const handlePayPalPay = useCallback(async () => {
    if (!selectedPlan || isChecking) return;
    setPaypalProcessing(true);
    try {
      const res = await fetch('/api/paypal/create-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planId: selectedPlan.id }),
      });
      const data = await res.json();
      if (!data.success || !data.approvalUrl) { alert(data.error || t.networkError); setPaypalProcessing(false); return; }
      setCurrentOrderId(data.orderId);
      const paypalWindow = window.open(data.approvalUrl, '_blank', 'width=600,height=700');
      if (!paypalWindow) { window.location.href = data.approvalUrl; return; }
      const pollTimer = setInterval(async () => {
        if (paypalWindow.closed) {
          clearInterval(pollTimer);
          try {
            const captureRes = await fetch('/api/paypal/capture-order', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ paypalOrderId: data.paypalOrderId, orderId: data.orderId }),
            });
            const captureData = await captureRes.json();
            if (captureData.success) {
              setShowPayModal(false); setWalletTail(''); setPaymentMethod('TRC20'); setPaypalProcessing(false);
              await handleCalculate(selectedPlan.id, data.orderId);
            } else { alert(t.alertWait); setPaypalProcessing(false); }
          } catch { alert(t.networkError); setPaypalProcessing(false); }
        }
      }, 1000);
      setTimeout(() => { clearInterval(pollTimer); setPaypalProcessing(false); }, 300000);
    } catch { alert(t.networkError); setPaypalProcessing(false); }
  }, [selectedPlan, isChecking, t, handleCalculate]);

  const verifyPayoneerPayment = useCallback(async () => {
    if (!selectedPlan || isChecking) return;
    setIsChecking(true);
    try {
      const res = await fetch('/api/payoneer-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'create', planId: selectedPlan.id })
      });
      const data = await res.json();
      if (data.success && data.paymentId) {
        setPayoneerPaymentId(data.paymentId);
        alert(lang === 'EN'
          ? 'Payment instructions generated. Please complete the wire transfer using the reference code above.'
          : '已生成付款指引，请使用上方的汇款参考号完成电汇。');
      }
    } catch (error) {
      console.error('Payoneer payment failed:', error);
      alert(t.networkError);
    } finally {
      setIsChecking(false);
    }
  }, [selectedPlan, isChecking, lang, t]);

  const handleCloseModal = useCallback(() => {
    setShowPayModal(false);
    setWalletTail('');
    setSelectedPlan(null);
    setCurrentOrderId(null);
    setPayoneerPaymentId(null);
    setPaypalProcessing(false);
    setArtifactMode(false);
    setPaymentMethod('TRC20');
  }, []);

  if (!isMounted) {
    return <LoadingSkeleton type="ZODIAC" lang={lang} />;
  }

  const planCards = [
    { id: 'LITE' as const, price: '10', name: t.liteName, highlight: false },
    { id: 'ELITE' as const, price: '29.9', name: t.eliteName, highlight: true }
  ];

  return (
    <div className="min-h-screen bg-transparent text-white p-4 font-sans selection:bg-yellow-500/30 overflow-x-hidden relative">
      {/* Room Specific Glow */}
      <div className="fixed top-[10%] right-[-5%] w-[50%] h-[50%] rounded-full bg-yellow-500/10 blur-[120px] pointer-events-none z-[-1]"></div>
      <div className="fixed bottom-[20%] left-[-10%] w-[40%] h-[40%] rounded-full bg-orange-500/5 blur-[100px] pointer-events-none z-[-1]"></div>
      <div className="absolute top-4 right-4 flex gap-2 z-50">
        <button onClick={() => setLang('EN')} className={`px-3 py-1 rounded text-[10px] border transition-all ${lang === 'EN' ? 'bg-yellow-500 text-black font-bold' : 'text-gray-400 border-gray-800'}`}>EN</button>
        <button onClick={() => setLang('CN')} className={`px-3 py-1 rounded text-[10px] border transition-all ${lang === 'CN' ? 'bg-yellow-500 text-black font-bold' : 'text-gray-400 border-gray-800'}`}>中文</button>
      </div>

      <div className="absolute top-4 left-4 z-50">
        <button onClick={navigateBack} className="px-4 py-2 rounded-xl text-[10px] border border-gray-800 text-gray-400 uppercase tracking-widest hover:text-white transition-all">{t.back}</button>
      </div>

      <div className="max-w-4xl mx-auto py-16 space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <header className="text-center space-y-2">
          <h1 className="text-5xl font-black italic tracking-tighter uppercase">
            {lang === 'EN' ? 'Zodiac' : '赛博'}<span className="text-yellow-500">{lang === 'EN' ? 'Nebula' : '星盘'}</span>
          </h1>
          <p className="text-gray-500 text-[10px] tracking-[0.3em] uppercase">{t.sub}</p>
        </header>

        <div className="bg-[#0a0f1d] p-8 rounded-[2.5rem] border border-gray-800 shadow-xl space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] text-yellow-500 font-black uppercase tracking-widest">{t.labelSelf}</label>
              <select value={selfSign} onChange={e => setSelfSign(e.target.value)} className="w-full bg-black/40 border border-gray-800 rounded-2xl p-4 text-white outline-none focus:border-yellow-500 appearance-none cursor-pointer">
                {ZODIACS.map(z => <option key={z} value={z} className="bg-[#0a0f1d]">{z}</option>)}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] text-purple-400 font-black uppercase tracking-widest">{t.labelMbti}</label>
              <select value={mbti} onChange={e => setMbti(e.target.value)} className="w-full bg-black/40 border border-gray-800 rounded-2xl p-4 text-purple-300 outline-none focus:border-purple-500 appearance-none cursor-pointer">
                <option value="" className="bg-[#0a0f1d]">- {lang === 'EN' ? 'Skip' : '跳过'} -</option>
                {MBTIS.map(m => <option key={m} value={m} className="bg-[#0a0f1d]">{m}</option>)}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest">{t.labelPartner}</label>
              <select value={partnerSign} onChange={e => setPartnerSign(e.target.value)} className="w-full bg-black/40 border border-gray-800 rounded-2xl p-4 text-white outline-none focus:border-yellow-500 appearance-none cursor-pointer">
                <option value="" className="bg-[#0a0f1d]">- {lang === 'EN' ? 'None' : '无'} -</option>
                {ZODIACS.map(z => <option key={z} value={z} className="bg-[#0a0f1d]">{z}</option>)}
              </select>
            </div>
          </div>

          {readLevel === 'NONE' && (
            <button onClick={() => handleCalculate('FREE_PART1')} disabled={isAnalyzing} className="w-full py-5 bg-gradient-to-r from-yellow-600 to-yellow-500 rounded-2xl font-black text-black uppercase shadow-[0_0_30px_rgba(202,138,4,0.4)] hover:scale-[1.02] transition-transform">
              {isAnalyzing ? t.analyzing : t.btnGen1}
            </button>
          )}
        </div>

        {(interpretation || isAnalyzing) && (
          <div className="space-y-8 animate-in fade-in duration-700">
            <div className="bg-[#0a0f1d] p-8 rounded-[2.5rem] border border-yellow-900/30 space-y-8 relative">
              <h3 className="text-2xl font-black text-yellow-500 italic uppercase tracking-tighter">{lang === 'EN' ? "Nebula's Insight" : "星盘洞察"}</h3>

              <div className="flex flex-col md:flex-row gap-8 items-center border-b border-gray-800 pb-8">
                <div className="w-full md:w-1/2 h-64">
                  <ResponsiveContainerComponent width="100%" height="100%">
                    <RadarChartComponent cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                      <PolarGridComponent stroke="#374151" />
                      <PolarAngleAxisComponent dataKey="subject" tick={{ fill: '#EAB308', fontSize: 10, fontWeight: 'bold' }} />
                      <PolarRadiusAxisComponent angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                      <RadarComponent name="Aura" dataKey="A" stroke="#EAB308" fill="#EAB308" fillOpacity={0.3} isAnimationActive={true} />
                    </RadarChartComponent>
                  </ResponsiveContainerComponent>
                </div>

                <div className="w-full md:w-1/2 space-y-4">
                  <div className="bg-black/50 p-4 rounded-2xl border border-gray-800">
                    <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{lang === 'EN' ? 'Lucky Freq' : '共振频率'}</p>
                    <p className="text-xl font-black text-white">{luckyTags.freq} Hz</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-black/50 p-4 rounded-2xl border border-gray-800 flex items-center justify-between">
                      <div>
                        <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{lang === 'EN' ? 'Color' : '幸运色'}</p>
                        <p className="text-sm font-black font-mono" style={{ color: luckyTags.color }}>{luckyTags.color}</p>
                      </div>
                      <div className="w-6 h-6 rounded-full" style={{ backgroundColor: luckyTags.color }}></div>
                    </div>
                    <div className="bg-black/50 p-4 rounded-2xl border border-gray-800">
                      <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{lang === 'EN' ? 'Number' : '矩阵数字'}</p>
                      <p className="text-sm font-black text-white">{luckyTags.num}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-black/40 p-8 rounded-[2rem] border border-gray-800 italic text-gray-200 text-sm leading-relaxed whitespace-pre-line relative">
                {isAnalyzing && (
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-10 animate-in fade-in duration-300">
                    <div className="flex flex-col items-center space-y-4">
                      <div className="w-10 h-10 border-4 border-yellow-500/20 border-t-yellow-500 rounded-full animate-spin"></div>
                      <p className="text-yellow-500 font-black text-xs tracking-widest uppercase animate-pulse">{t.analyzing}</p>
                    </div>
                  </div>
                )}
                {interpretation}
                {(readLevel === 'PART1' || readLevel === 'PART2') && (
                  <span className="animate-pulse text-yellow-500 font-black mt-2 block">{t.denied}</span>
                )}
              </div>

              {signElement && (
                <ArtifactRecommender 
                  room="ZODIAC"
                  element={signElement} 
                  lang={lang} 
                  onPurchase={(price) => handleOpenPayModal({ id: 'ELITE', price }, true)} 
                />
              )}
            </div>

            {readLevel === 'PART1' && !isWaitingForFriend && (
              <div className="space-y-4 text-center">
                <p className="text-yellow-400 font-black tracking-[0.2em] text-xs">{t.shareTip}</p>
                <button onClick={handleShareAndTrack} className="w-full py-5 rounded-2xl bg-yellow-600 text-white font-black uppercase shadow-[0_0_30px_rgba(202,138,4,0.4)] hover:scale-[1.02] transition-transform">{t.btnShare}</button>
              </div>
            )}

            {readLevel === 'PART1' && isWaitingForFriend && (
              <div className="p-8 bg-yellow-900/10 border border-yellow-500/30 rounded-3xl text-center space-y-4 animate-in zoom-in">
                <div className="animate-spin text-4xl mb-4 text-yellow-500">⌛</div>
                <p className="text-yellow-400 font-black text-sm animate-pulse">{t.waiting}</p>
                <button onClick={() => handleCalculate('FREE_PART2')} className="w-full py-3 rounded-xl border border-gray-700 text-gray-500 text-[10px] uppercase font-bold hover:text-white transition-all">{t.btnManual}</button>
                <div className="pt-6 border-t border-yellow-900/30">
                  <button onClick={() => handleOpenPayModal({ id: 'LITE', price: '10' })} className="w-full py-4 rounded-xl border border-yellow-500 text-yellow-400 text-xs font-black uppercase hover:bg-yellow-500/10">{t.skipWait}</button>
                </div>
              </div>
            )}

            {readLevel === 'PART2' && (
              <div className="space-y-6 animate-in slide-in-from-bottom-4 mt-8">
                <div className="text-center">
                  <p className="text-red-400 font-black tracking-[0.2em] uppercase text-xs animate-pulse">{t.friendClicked}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {planCards.map(plan => (
                    <button key={plan.id} onClick={() => handleOpenPayModal({ id: plan.id, price: plan.price })} className={`p-6 rounded-[2.5rem] border cursor-pointer hover:scale-105 transition-all group ${plan.highlight ? 'border-yellow-500 bg-yellow-500/5 shadow-[0_0_30px_rgba(202,138,4,0.1)]' : 'border-gray-800 bg-gray-900/50'}`}>
                      <div className="text-center font-black">
                        <div className="text-[10px] text-yellow-400 uppercase mb-1">{plan.id} READ</div>
                        <div className="text-3xl font-black mb-1">${plan.price}</div>
                        <div className="text-[10px] text-gray-500 font-bold">{plan.name}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {showPayModal && (
        <PayModal
          show={showPayModal}
          selectedPlan={selectedPlan}
          TRC20_ADDR={TRC20_ADDR}
          currentOrderId={currentOrderId}
          walletTail={walletTail}
          setWalletTail={setWalletTail}
          isChecking={isChecking}
          onVerify={verifyPayment}
          onPayPalPay={handlePayPalPay}
          onClose={handleCloseModal}
          paymentMethod={paymentMethod}
          onSwitchMethod={handleSwitchPaymentMethod}
          payoneerPaymentId={payoneerPaymentId}
          paypalProcessing={paypalProcessing}
          artifactMode={artifactMode}
          t={t}
        />
      )}
    </div>
  );
}