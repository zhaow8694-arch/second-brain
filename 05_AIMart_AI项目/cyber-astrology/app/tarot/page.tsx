'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// 动态导入重型组件
const RadarChartComponent = dynamic(() => import('recharts').then(mod => mod.RadarChart), { ssr: false });
const RadarComponent = dynamic(() => import('recharts').then(mod => mod.Radar), { ssr: false });
const PolarGridComponent = dynamic(() => import('recharts').then(mod => mod.PolarGrid), { ssr: false });
const PolarAngleAxisComponent = dynamic(() => import('recharts').then(mod => mod.PolarAngleAxis), { ssr: false });
const ResponsiveContainerComponent = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });

const PayModal = dynamic(() => import('../components/PayModal').then(mod => mod.PayModal), { ssr: false });
const ArtifactRecommender = dynamic(() => import('../components/ArtifactRecommender').then(mod => mod.ArtifactRecommender), { ssr: false });
const LoadingSkeleton = dynamic(() => import('../components/LoadingSkeleton').then(mod => mod.LoadingSkeleton), { ssr: false });

const MAJOR_ARCANA_CN = [
  "愚者", "魔术师", "女祭司", "女皇", "皇帝", "教皇",
  "恋人", "战车", "力量", "隐士", "命运之轮", "正义",
  "倒吊人", "死神", "节制", "恶魔", "高塔", "星星",
  "月亮", "太阳", "审判", "世界"
];
const MAJOR_ARCANA_EN = [
  "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor", "The Hierophant",
  "The Lovers", "The Chariot", "Strength", "The Hermit", "Wheel of Fortune", "Justice",
  "The Hanged Man", "Death", "Temperance", "The Devil", "The Tower", "The Star",
  "The Moon", "The Sun", "Judgement", "The World"
];

type PlanType = { id: 'LITE' | 'ELITE'; price: string };
type ReadLevel = 'NONE' | 'PART1' | 'PART2' | 'PAID';

export default function TarotRoomPage() {
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);
  const [lang, setLang] = useState<'EN' | 'CN'>('CN');
  const [isNavigating, setIsNavigating] = useState(false);

  const [drawnCards, setDrawnCards] = useState<number[]>([]);
  const [cardsRevealed, setCardsRevealed] = useState([false, false, false]);
  const [focusArea, setFocusArea] = useState('General');
  const [isDrawing, setIsDrawing] = useState(false);

  const [interpretation, setInterpretation] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [readLevel, setReadLevel] = useState<ReadLevel>('NONE');

  const [radarData, setRadarData] = useState<Array<{ subject: string; A: number }>>([]);
  const [luckyTags, setLuckyTags] = useState({ freq: '', karma: '', guide: '' });
  const [topElement, setTopElement] = useState('');

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

  const TRC20_ADDR = process.env.NEXT_PUBLIC_TRC20_ADDR || 'TY2E8XcYbdX6ZsBbU166EbWowGusBP9Aw1';

  useEffect(() => {
    setIsMounted(true);
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const l = params.get('lang');
      if (l === 'EN' || l === 'CN') setLang(l);

      const c = params.get('c');
      const refId = params.get('ref');
      
      if (c) {
        const indices = c.split('|')
          .map(Number)
          .filter(idx => idx >= 0 && idx < 22 && !isNaN(idx));
        
        if (indices.length === 3) {
          setDrawnCards(indices);
          setCardsRevealed([true, true, true]);
        }
      }
      
      if (refId) {
        fetch(`/api/share?id=${refId}&action=click`).catch(() => {});
      }
      setShareUrl(window.location.origin + window.location.pathname);
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const t = useMemo(() => ({
    back: lang === 'EN' ? '← Back' : '← 返回',
    focus: lang === 'EN' ? 'Focus Area' : '专注领域',
    f1: lang === 'EN' ? 'General / Life' : '综合运势 / 生命轨迹',
    f2: lang === 'EN' ? 'Love / Relationships' : '爱情 / 宿命羁绊',
    f3: lang === 'EN' ? 'Wealth / Career' : '财富 / 事业版图',
    btnDraw: lang === 'EN' ? 'Draw 3 Cards' : '抽取 3 张牌',
    btnDrawing: lang === 'EN' ? 'Drawing...' : '正在抽取...',
    btnGen1: lang === 'EN' ? 'Generate Teaser' : '提取神谕预告',
    btnWait: lang === 'EN' ? 'Connecting...' : '量子连接中...',
    denied: lang === 'EN' ? '... (Access Denied / Signal Encrypted)' : '... (权限不足，核心神谕已加密)',
    shareTip: lang === 'EN' ? 'Share link to unlock Part 2' : '【分享链接给好友，点开即可解锁第二段神谕】',
    btnShare: lang === 'EN' ? '🔗 Share to Unlock' : '🔗 分享并解锁下文',
    waiting: lang === 'EN' ? 'Monitoring Resonance...' : '正在监测量子共振...',
    btnManual: lang === 'EN' ? 'I have shared, unlock now' : '我已分享，立即解锁',
    skipWait: lang === 'EN' ? 'Pay 10U to Unlock All' : '直接支付 10U 立即解锁全部',
    friendClicked: lang === 'EN' ? 'Unlocked! Pay for final truth:' : '神谕已解锁。核心破局真相请支付查看：',
    liteName: lang === 'EN' ? 'Basic 3-Card Reading' : '三牌阵基础解析',
    eliteName: lang === 'EN' ? 'Deep Subconscious Decode' : '潜意识深度破局',
    modalTitle: lang === 'EN' ? 'Offer Sacrifice' : '扫码献祭',
    modalCopy: lang === 'EN' ? 'COPY ADDRESS' : '复制付款地址',
    modalVerify: lang === 'EN' ? 'Verify Paid' : '我已支付，立即解锁',
    modalVerifying: lang === 'EN' ? 'Scanning...' : '核对账款中...',
    modalCancel: lang === 'EN' ? 'Cancel' : '取消支付',
    walletTailHint: lang === 'EN' ? 'Wallet Last 4 Chars' : '付款钱包尾号(后4位)',
    alertWait: lang === 'EN' ? 'Payment not found. Ensure transfer is complete and memo is correct.' : '未扫描到账单，请确认转账已完成且备注正确。',
    titleDecode: lang === 'EN' ? "Oracle's Decode" : '神谕解码',
    noCards: lang === 'EN' ? 'Please draw cards first' : '请先抽取塔罗牌',
    walletTip: lang === 'EN' ? 'Enter last 4 digits' : '请输入钱包后4位',
    copied: lang === 'EN' ? 'Copied!' : '已复制！',
    syncFailed: lang === 'EN' ? 'Error connecting to server.' : '服务器连接失败。',
    linkCopied: lang === 'EN' ? '🔗 Link copied!' : '🔗 链接已复制！',
    copyFailed: lang === 'EN' ? 'Copy failed' : '复制失败',
    langEN: lang === 'EN' ? 'Switch to English' : '切换到英文',
    langCN: lang === 'EN' ? 'Switch to Chinese' : '切换到中文',
    loading: lang === 'EN' ? 'Loading Tarot Room...' : '正在加载塔罗房间...',
    networkError: lang === 'EN' ? 'Network or Server Error.' : '网络或服务器错误。',
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
    try { await router.push(`/?lang=${lang}`); } catch (e) { console.error(e); } finally { setIsNavigating(false); }
  }, [isNavigating, router, lang]);

  const drawCards = useCallback(() => {
    if (isDrawing) return;
    setIsDrawing(true);
    setInterpretation('');
    setReadLevel('NONE');
    setIsWaitingForFriend(false);
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    
    setCardsRevealed([false, false, false]);
    const indices: number[] = [];
    const available = Array.from({ length: 22 }, (_, i) => i);
    while(indices.length < 3) {
      indices.push(available.splice(Math.floor(Math.random() * available.length), 1)[0]);
    }
    setDrawnCards(indices);

    setTimeout(() => setCardsRevealed([true, false, false]), 500);
    setTimeout(() => setCardsRevealed([true, true, false]), 1000);
    setTimeout(() => {
      setCardsRevealed([true, true, true]);
      setIsDrawing(false);
    }, 1500);

    if (typeof window !== 'undefined') {
      const url = new URL(window.location.origin + window.location.pathname);
      url.searchParams.set('c', indices.join('|'));
      url.searchParams.set('lang', lang);
      setShareUrl(url.toString());
    }
  }, [lang, isDrawing]);

  const handleCalculate = useCallback(async (pType: string, orderId?: string) => {
    if (drawnCards.length === 0) { alert(t.noCards); return; }
    setIsAnalyzing(true);
    setInterpretation('');

    if (pType === 'FREE_PART1') {
      const { calculateElementalStrength, generateLuckyTags } = await import('./elemental-dignity');
      
      const cardInfos = drawnCards.map(idx => ({
        name: lang === 'EN' ? MAJOR_ARCANA_EN[idx] : MAJOR_ARCANA_CN[idx],
        index: idx
      }));
      
      const strength = calculateElementalStrength(cardInfos);
      
      const radar = [
        { subject: lang === 'EN' ? 'Fire' : '火', A: strength.fire },
        { subject: lang === 'EN' ? 'Water' : '水', A: strength.water },
        { subject: lang === 'EN' ? 'Air' : '风', A: strength.air },
        { subject: lang === 'EN' ? 'Earth' : '土', A: strength.earth },
        { subject: lang === 'EN' ? 'Spirit' : '灵', A: strength.spirit },
      ];
      setRadarData(radar);

      // 找到最强的元素用于推荐饰品
      const elements = [
        { key: '火', val: strength.fire },
        { key: '水', val: strength.water },
        { key: '金', val: strength.air }, // 风对应金
        { key: '土', val: strength.earth },
        { key: '木', val: strength.spirit } // 灵对应木
      ];
      const sorted = elements.sort((a, b) => b.val - a.val);
      setTopElement(sorted[0].key);
      
      const tags = generateLuckyTags(cardInfos, lang as 'EN' | 'CN');
      setLuckyTags(tags);
    }

    try {
      const deck = lang === 'EN' ? MAJOR_ARCANA_EN : MAJOR_ARCANA_CN;
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'tarot',
          cards: drawnCards.map(i => deck[i]),
          focus: focusArea,
          plan: pType,
          lang,
          orderId: orderId || null,
        }),
      });
      if (!res.ok) throw new Error('API error');

      // 处理流式响应
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulatedText = '';

      while (!done) {
        const { value, done: doneReading } = await reader!.read();
        done = doneReading;
        const chunkValue = decoder.decode(value);
        accumulatedText += chunkValue;
        setInterpretation(accumulatedText);
      }

      if (pType === 'FREE_PART1') setReadLevel('PART1');
      else if (pType === 'FREE_PART2') setReadLevel('PART2');
      else setReadLevel('PAID');
    } catch (e) {
      console.error('Calculation failed:', e);
      const isDev = process.env.NODE_ENV === 'development' || (typeof window !== 'undefined' && window.location.hostname === 'localhost');
      if (isDev) {
        setInterpretation(lang === 'EN' 
          ? " [DEMO MODE] The cards resonate with your spirit frequency. A new path is manifesting before you. (Mock text)"
          : "【演示模式】牌阵与你的灵魂频率产生了强烈的量子共振。一条全新的命运路径正从虚无中显现。（模拟文本）"
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
  }, [drawnCards, focusArea, t, lang]);

  const handleShareAndTrack = useCallback(async () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    
    const trackId = Math.random().toString(36).slice(2, 10);
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
          text: lang === 'EN' ? 'Check my Tarot!' : '来看我的塔罗占卜！',
          url: trackableUrl
        });
        shared = true;
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.warn('Share failed:', error);
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
        const res = await fetch(`/api/share?id=${trackId}&action=check`);
        const data = await res.json();
        if (data.clicked) {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setIsWaitingForFriend(false);
          handleCalculate('FREE_PART2');
        }
      } catch {}
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
    if (!/^[0-9A-Za-z]{4}$/.test(trimmedTail)) { alert(t.walletTip); return; }
    setIsChecking(true);
    try {
      const res = await fetch('/api/verify-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: TRC20_ADDR, amount: selectedPlan.price, walletTail: trimmedTail, orderId: currentOrderId })
      });
      const data = await res.json();
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
      } else { alert(t.alertWait); }
    } catch { alert(t.networkError); } finally { setIsChecking(false); }
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
    } catch { alert(t.networkError); } finally { setIsChecking(false); }
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

  const renderCardName = useCallback((idx: number) => {
    if (idx < 0 || idx >= 22) return lang === 'EN' ? 'Unknown' : '未知';
    return lang === 'EN' ? MAJOR_ARCANA_EN[idx] : MAJOR_ARCANA_CN[idx];
  }, [lang]);

  if (!isMounted) return <LoadingSkeleton type="TAROT" lang={lang} />;

  return (
    <div className="min-h-screen bg-transparent text-white p-4 font-sans selection:bg-purple-500/30 overflow-x-hidden relative">
      {/* Room Specific Glow */}
      <div className="fixed top-[20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-purple-500/10 blur-[120px] pointer-events-none z-[-1]"></div>
      <div className="fixed bottom-[10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-pink-500/5 blur-[100px] pointer-events-none z-[-1]"></div>
      <div className="absolute top-4 right-4 flex gap-2 z-50">
        <button onClick={() => setLang('EN')} className={`px-3 py-1 rounded text-[10px] border transition-all ${lang === 'EN' ? 'bg-purple-500 text-black font-bold' : 'text-gray-400 border-gray-800'}`}>EN</button>
        <button onClick={() => setLang('CN')} className={`px-3 py-1 rounded text-[10px] border transition-all ${lang === 'CN' ? 'bg-purple-500 text-black font-bold' : 'text-gray-400 border-gray-800'}`}>中文</button>
      </div>

      <div className="absolute top-4 left-4 z-50">
        <button onClick={navigateBack} className="px-4 py-2 rounded-xl text-[10px] border border-gray-800 text-gray-400 uppercase tracking-widest hover:text-white transition-all">{t.back}</button>
      </div>

      <div className="max-w-4xl mx-auto py-16 space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <header className="text-center"><h1 className="text-5xl font-black italic uppercase">{lang === 'EN' ? 'Western' : '西方赛博'}<span className="text-purple-500">{lang === 'EN' ? 'Arcana' : '塔罗'}</span></h1></header>

        <div className="bg-[#0a0f1d] p-8 rounded-[2.5rem] border border-gray-800 shadow-xl flex flex-col items-center space-y-6">
          {drawnCards.length === 0 ? (
            <div className="w-full flex flex-col items-center space-y-8">
              <select value={focusArea} onChange={e => setFocusArea(e.target.value)} className="w-full max-w-sm bg-black/40 border border-gray-800 rounded-2xl p-4 text-white outline-none focus:border-purple-500 appearance-none text-center">
                <option value="General">{t.f1}</option>
                <option value="Love">{t.f2}</option>
                <option value="Wealth">{t.f3}</option>
              </select>
              <button onClick={drawCards} disabled={isDrawing} className="py-6 px-12 rounded-3xl bg-gradient-to-r from-purple-700 to-purple-500 font-black text-xl tracking-[0.3em] uppercase hover:scale-105 transition-all shadow-[0_0_40px_rgba(168,85,247,0.3)]">{isDrawing ? t.btnDrawing : t.btnDraw}</button>
            </div>
          ) : (
            <div className="w-full space-y-8">
              <div className="grid grid-cols-3 gap-2">
                {drawnCards.map((idx, i) => (
                  <div key={i} className="relative w-full aspect-[2/3]" style={{ perspective: '1000px' }}>
                    <div className="w-full h-full absolute transition-all duration-700" style={{ transformStyle: 'preserve-3d', transform: cardsRevealed[i] ? 'rotateY(180deg)' : 'rotateY(0deg)' }}>
                      <div className="absolute w-full h-full bg-gray-900 border-2 border-gray-800 rounded-xl flex items-center justify-center" style={{ backfaceVisibility: 'hidden' }}><span className="text-2xl">🔮</span></div>
                      <div className="absolute w-full h-full bg-gradient-to-b from-purple-900/40 to-black border-2 border-purple-500/50 rounded-xl flex items-center justify-center p-2 text-center" style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}><span className="font-black text-[10px] md:text-sm">{renderCardName(idx)}</span></div>
                    </div>
                  </div>
                ))}
              </div>
              {cardsRevealed[2] && readLevel === 'NONE' && (
                <button onClick={() => handleCalculate('FREE_PART1')} disabled={isAnalyzing} className="w-full py-5 bg-purple-600 rounded-2xl font-black uppercase hover:scale-[1.02] transition-transform">{isAnalyzing ? t.btnWait : t.btnGen1}</button>
              )}
            </div>
          )}
        </div>

        {(interpretation || isAnalyzing) && (
          <div className="space-y-8 animate-in fade-in duration-700">
            <div className="bg-[#0a0f1d] p-8 rounded-[2.5rem] border border-purple-900/30 space-y-8 relative">
              <h3 className="text-2xl font-black text-purple-500 italic uppercase tracking-tighter">{t.titleDecode}</h3>
              <div className="flex flex-col md:flex-row gap-8 items-center border-b border-gray-800 pb-8">
                <div className="w-full md:w-1/2 h-64">
                  <ResponsiveContainerComponent width="100%" height="100%">
                    <RadarChartComponent data={radarData}>
                      <PolarGridComponent stroke="#374151" />
                      <PolarAngleAxisComponent dataKey="subject" tick={{fill:'#A855F7',fontSize:10}} />
                      <RadarComponent dataKey="A" stroke="#A855F7" fill="#A855F7" fillOpacity={0.3} />
                    </RadarChartComponent>
                  </ResponsiveContainerComponent>
                </div>
                <div className="w-full md:w-1/2 space-y-4">
                  <div className="bg-black/50 p-4 rounded-2xl border border-gray-800"><p className="text-[10px] text-gray-500 uppercase mb-1">{lang==='EN'?'Soul Freq':'频率'}</p><p className="text-xl font-black">{luckyTags.freq} Hz</p></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-black/50 p-4 rounded-2xl border border-gray-800"><p className="text-[10px] text-gray-500 uppercase mb-1">Karma</p><p className="text-sm font-black text-purple-400">{luckyTags.karma}</p></div>
                    <div className="bg-black/50 p-4 rounded-2xl border border-gray-800"><p className="text-[10px] text-gray-500 uppercase mb-1">Guide</p><p className="text-sm font-black">{luckyTags.guide}</p></div>
                  </div>
                </div>
              </div>
              <div className="bg-black/40 p-8 rounded-[2rem] border border-gray-800 italic text-gray-200 text-sm leading-relaxed whitespace-pre-line relative">
                {isAnalyzing && (
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-10 animate-in fade-in duration-300">
                    <div className="flex flex-col items-center space-y-4">
                      <div className="w-10 h-10 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
                      <p className="text-purple-500 font-black text-xs tracking-widest uppercase animate-pulse">{t.btnWait}</p>
                    </div>
                  </div>
                )}
                {interpretation}
                {(readLevel==='PART1'||readLevel==='PART2')&&<span className="animate-pulse text-purple-500 font-black mt-2 block">{t.denied}</span>}
              </div>

              {topElement && (
                <ArtifactRecommender 
                  room="TAROT"
                  element={topElement} 
                  lang={lang} 
                  onPurchase={(price) => handleOpenPayModal({ id: 'ELITE', price }, true)} 
                />
              )}
            </div>

            {readLevel === 'PART1' && !isWaitingForFriend && (
              <div className="space-y-4 text-center">
                <p className="text-purple-400 font-black text-xs">{t.shareTip}</p>
                <button onClick={handleShareAndTrack} className="w-full py-5 rounded-2xl bg-purple-600 text-white font-black uppercase shadow-[0_0_30px_rgba(168,85,247,0.4)] hover:scale-[1.02] transition-transform">{t.btnShare}</button>
              </div>
            )}

            {readLevel === 'PART1' && isWaitingForFriend && (
              <div className="p-8 bg-purple-900/10 border border-purple-500/30 rounded-3xl text-center space-y-4 animate-in zoom-in">
                <div className="animate-spin text-4xl mb-4 text-purple-500">⌛</div>
                <p className="text-purple-400 font-black text-sm animate-pulse">{t.waiting}</p>
                <button onClick={() => handleCalculate('FREE_PART2')} className="w-full py-3 rounded-xl border border-gray-700 text-gray-500 text-[10px] uppercase font-bold hover:text-white transition-all">{t.btnManual}</button>
                <div className="pt-6 border-t border-purple-900/30">
                  <button onClick={() => handleOpenPayModal({ id: 'LITE', price: '10' })} className="w-full py-4 rounded-xl border border-purple-500 text-purple-400 text-xs font-black uppercase hover:bg-purple-500/10">{t.skipWait}</button>
                </div>
              </div>
            )}

            {readLevel === 'PART2' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                {[{ id: 'LITE' as const, price: '10', name: t.liteName, h: false }, { id: 'ELITE' as const, price: '29.9', name: t.eliteName, h: true }].map(p => (
                  <button key={p.id} onClick={() => handleOpenPayModal({ id: p.id, price: p.price })} className={`p-6 rounded-[2.5rem] border hover:scale-105 transition-all ${p.h ? 'border-purple-500 bg-purple-500/5' : 'border-gray-800 bg-gray-900/50'}`}>
                    <div className="text-center font-black"><div className="text-[10px] text-purple-400 uppercase mb-1">{p.id} READ</div><div className="text-3xl mb-1">${p.price}</div><div className="text-[10px] text-gray-500 font-bold">{p.name}</div></div>
                  </button>
                ))}
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