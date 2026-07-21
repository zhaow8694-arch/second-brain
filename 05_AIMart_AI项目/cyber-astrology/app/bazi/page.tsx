'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Solar } from 'lunar-javascript';

// 动态导入重型组件
const RadarChartComponent = dynamic(() => import('recharts').then(mod => mod.RadarChart), { ssr: false });
const RadarComponent = dynamic(() => import('recharts').then(mod => mod.Radar), { ssr: false });
const PolarGridComponent = dynamic(() => import('recharts').then(mod => mod.PolarGrid), { ssr: false });
const PolarAngleAxisComponent = dynamic(() => import('recharts').then(mod => mod.PolarAngleAxis), { ssr: false });
const PolarRadiusAxisComponent = dynamic(() => import('recharts').then(mod => mod.PolarRadiusAxis), { ssr: false });
const ResponsiveContainerComponent = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });
const LineChartComponent = dynamic(() => import('recharts').then(mod => mod.LineChart), { ssr: false });
const LineComponent = dynamic(() => import('recharts').then(mod => mod.Line), { ssr: false });

const PayModal = dynamic(() => import('../components/PayModal').then(mod => mod.PayModal), { ssr: false });
const ArtifactRecommender = dynamic(() => import('../components/ArtifactRecommender').then(mod => mod.ArtifactRecommender), { ssr: false });
const LoadingSkeleton = dynamic(() => import('../components/LoadingSkeleton').then(mod => mod.LoadingSkeleton), { ssr: false });

type PlanType = { id: 'LITE' | 'ELITE'; price: string };
type ReadLevel = 'NONE' | 'PART1' | 'PART2' | 'PAID';
type Gender = 'male' | 'female';

interface RadarData {
  subject: string;
  A: number;
}

interface TrendPoint {
  age: number;
  energy: number;
}

export default function BaziRoomPage() {
  const router = useRouter();
  const [isMounted, setIsMounted] = useState(false);
  const [lang, setLang] = useState<'EN' | 'CN'>('CN');
  const [isNavigating, setIsNavigating] = useState(false);

  const [formData, setFormData] = useState({
    year: '1993',
    month: '9',
    day: '27',
    hour: '20',
    gender: 'male' as Gender
  });

  const [bazi, setBazi] = useState('');
  const [interpretation, setInterpretation] = useState('');
  const [chartData, setChartData] = useState<TrendPoint[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [readLevel, setReadLevel] = useState<ReadLevel>('NONE');

  const [radarData, setRadarData] = useState<RadarData[]>([]);
  const [luckyTags, setLuckyTags] = useState({ color: '', dir: '', element: '', rawElement: '' });

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
  const [artifactMode, setArtifactMode] = useState(false); // 周边商品模式：只显示 TRC20

  const TRC20_ADDR = process.env.NEXT_PUBLIC_TRC20_ADDR || "TY2E8XcYbdX6ZsBbU166EbWowGusBP9Aw1";

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

  const t = useMemo(() => ({
    back: lang === 'EN' ? '← Back' : '← 返回大厅',
    title: lang === 'EN' ? 'Eastern Matrix' : '东方能量罗盘',
    y: lang === 'EN' ? 'Year' : '年',
    m: lang === 'EN' ? 'Month' : '月',
    d: lang === 'EN' ? 'Day' : '日',
    h: lang === 'EN' ? 'Hour' : '时',
    male: lang === 'EN' ? 'Male' : '男',
    female: lang === 'EN' ? 'Female' : '女',
    btnGen1: lang === 'EN' ? 'Generate Teaser' : '提取天机预告',
    btnWait: lang === 'EN' ? 'Decoding...' : '天机解码中...',
    matrixTitle: lang === 'EN' ? 'Energy Matrix' : '命理能量矩阵',
    denied: lang === 'EN' ? '... (Access Denied / Signal Encrypted)' : '... (权限不足，核心天机已加密)',
    shareTip: lang === 'EN' ? 'Share link to unlock Part 2' : '【分享链接给好友，点开即可解锁第二段天机】',
    btnShare: lang === 'EN' ? '🔗 Share to Unlock' : '🔗 分享并解锁下文',
    waiting: lang === 'EN' ? 'Resonance Monitoring...' : '正在监测量子共振...',
    btnManual: lang === 'EN' ? 'I have shared, unlock now' : '我已分享，立即解锁',
    skipWait: lang === 'EN' ? 'Pay 10U to Unlock All' : '直接支付 10U 立即解锁全部天机',
    friendClicked: lang === 'EN' ? 'Unlocked! Pay for final report:' : '下文已解锁。核心破局天机请支付查看：',
    liteName: lang === 'EN' ? '10-Year Wealth Path' : '十年财运深度解析',
    eliteName: lang === 'EN' ? 'Ultimate Prosperity' : '终极财富与避坑指南',
    modalTitle: lang === 'EN' ? 'Offer Sacrifice' : '扫码献祭',
    modalCopy: lang === 'EN' ? 'COPY ADDRESS' : '复制付款地址',
    modalVerify: lang === 'EN' ? 'Verify Paid' : '我已支付，立即解锁',
    modalVerifying: lang === 'EN' ? 'Scanning...' : '核对账款中...',
    modalCancel: lang === 'EN' ? 'Cancel' : '取消支付',
    walletTailHint: lang === 'EN' ? 'Wallet Last 4 Chars' : '付款钱包尾号(后4位)',
    alertWait: lang === 'EN' ? 'Payment not found. Ensure transfer is complete and memo is correct.' : '未扫描到账单，请确认转账已完成且备注正确。',
    lineTitle: lang === 'EN' ? '100-Year Matrix' : '百年大运轨迹',
    invalidTime: lang === 'EN' ? 'Invalid hour (0–23)' : '小时必须为 0–23',
    invalidDate: lang === 'EN' ? 'Invalid date' : '日期格式不合法',
    walletTip: lang === 'EN' ? 'Enter last 4 digits' : '请输入钱包后4位',
    copied: lang === 'EN' ? 'Copied!' : '已复制！',
    syncFailed: lang === 'EN' ? 'Error connecting to server.' : '服务器连接失败。',
    linkCopied: lang === 'EN' ? '🔗 Link copied!' : '🔗 链接已复制！',
    copyFailed: lang === 'EN' ? 'Copy failed' : '复制失败',
    langEN: lang === 'EN' ? 'Switch to English' : '切换到英文',
    langCN: lang === 'EN' ? 'Switch to Chinese' : '切换到中文',
    loading: lang === 'EN' ? 'Loading Bazi Room...' : '正在加载八字房间...',
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

  const handleCalculate = useCallback(async (pType: string, orderId?: string) => {
    const y = parseInt(formData.year) || 1993;
    const m = parseInt(formData.month) || 1;
    const d = parseInt(formData.day) || 1;
    const h = parseInt(formData.hour) || 12;

    if (h < 0 || h > 23) {
      alert(t.invalidTime);
      return;
    }
    
    const currentYear = new Date().getFullYear();
    
    if (y < 1900 || y > currentYear) {
      alert(lang === 'EN' ? 'Year must be between 1900 and current year' : '年份必须在1900年至当前年份之间');
      return;
    }
    
    if (m < 1 || m > 12) {
      alert(lang === 'EN' ? 'Month must be 1-12' : '月份必须在1-12之间');
      return;
    }
    
    if (d < 1 || d > 31) {
      alert(lang === 'EN' ? 'Day must be 1-31' : '日期必须在1-31之间');
      return;
    }
    
    const daysInMonth = new Date(y, m, 0).getDate();
    if (d > daysInMonth) {
      alert(lang === 'EN' ? `Invalid day for month ${m}` : `${m}月没有${d}号`);
      return;
    }

    setIsAnalyzing(true);

    try {
      const solar = Solar.fromYmdHms(y, m, d, h, 0, 0);
      const lunar = solar.getLunar();
      const baziObj = lunar.getEightChar();
      setBazi(baziObj.toString());

      const { calculateWangShuai, calculateDayunSequence, calculateDayunTrend, getYongShen } = await import('./index');
      
      const baziPillars = {
        year: { gan: baziObj.getYearGan(), zhi: baziObj.getYearZhi() },
        month: { gan: baziObj.getMonthGan(), zhi: baziObj.getMonthZhi() },
        day: { gan: baziObj.getDayGan(), zhi: baziObj.getDayZhi() },
        hour: { gan: baziObj.getTimeGan(), zhi: baziObj.getTimeZhi() }
      };
      
      const wangshuai = calculateWangShuai(baziPillars);
      
      setRadarData([
        { subject: lang === 'EN' ? 'Metal' : '金(Jin)', A: wangshuai.金 },
        { subject: lang === 'EN' ? 'Wood' : '木(Mu)', A: wangshuai.木 },
        { subject: lang === 'EN' ? 'Water' : '水(Shui)', A: wangshuai.水 },
        { subject: lang === 'EN' ? 'Fire' : '火(Huo)', A: wangshuai.火 },
        { subject: lang === 'EN' ? 'Earth' : '土(Tu)', A: wangshuai.土 },
      ]);
      
      const lunarYearGan = lunar.getYearGan();
      const lunarMonth = lunar.getMonth();
      const gender = formData.gender;
      
      const dayun = calculateDayunSequence(baziPillars, gender, lunarMonth, lunarYearGan);
      const trend = calculateDayunTrend(baziPillars, dayun);
      setChartData(trend);
      
      const dayElement = wangshuai.dayMasterElement;
      const elementColors: Record<string, string> = {
        '木': '#4ade80', '火': '#ef4444', '土': '#eab308', '金': '#94a3b8', '水': '#06b6d4'
      };
      
      const yongShen = getYongShen(wangshuai);
      
      const dirMap: Record<string, { EN: string; CN: string }> = {
        '木': { EN: 'East', CN: '正东(震)' },
        '火': { EN: 'South', CN: '正南(离)' },
        '土': { EN: 'Center', CN: '中央' },
        '金': { EN: 'West', CN: '正西(兑)' },
        '水': { EN: 'North', CN: '正北(坎)' }
      };

      const elementNames: Record<string, { EN: string; CN: string }> = {
        '木': { EN: 'Jia Wood', CN: '甲木' },
        '火': { EN: 'Ding Fire', CN: '丁火' },
        '土': { EN: 'Wu Earth', CN: '戊土' },
        '金': { EN: 'Geng Metal', CN: '庚金' },
        '水': { EN: 'Ren Water', CN: '壬水' }
      };
      
      setLuckyTags({
        color: elementColors[dayElement] || '#06b6d4',
        dir: lang === 'EN' ? dirMap[yongShen.direction].EN : dirMap[yongShen.direction].CN,
        element: lang === 'EN' ? elementNames[yongShen.direction].EN : elementNames[yongShen.direction].CN,
        rawElement: yongShen.direction
      });

      setIsAnalyzing(true);
      setInterpretation(''); // 流式输出前清空旧内容

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'bazi',
          bazi: bazi,
          gender: formData.gender,
          lang,
          plan: pType,
          orderId: orderId || null
        })
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

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

    } catch (err) {
      console.error('Calculation failed:', err);
      // 更加鲁棒的演示模式逻辑
      const isDev = process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost';
      
      if (isDev) {
        setInterpretation(lang === 'EN' 
          ? " [DEMO MODE] The cosmic matrix reveals a strong resonance in your destiny. Your core element is vibrant, and the path of fortune is opening. (This is mock text because API key might be missing in this environment)"
          : "【演示模式】星图矩阵显示你的命盘存在强烈的能量共振。你的核心用神充满活力，财富之门正徐徐开启。（此为模拟文本，因为系统未检测到有效的 API 调用环境）"
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
  }, [formData, lang, t, bazi]);

  const startPolling = useCallback((trackId: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    
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
          window.localStorage.removeItem('pending_track_id');
          setIsWaitingForFriend(false);
          handleCalculate('FREE_PART2');
        }
      } catch (error) {
        console.warn('Polling check failed:', error);
      }
    }, 3000);
  }, [handleCalculate]);

  const hasInitialized = useRef(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || hasInitialized.current) return;
    hasInitialized.current = true;
    
    const params = new URLSearchParams(window.location.search);
    const l = params.get('lang');
    if (l === 'EN' || l === 'CN') setLang(l);

    const y = params.get('y');
    const m = params.get('m');
    const d = params.get('d');
    const h = params.get('h');
    const g = params.get('g');
    const refId = params.get('ref');

    if (y && m && d && h && g) {
      setFormData({
        year: y,
        month: m,
        day: d,
        hour: h,
        gender: g as Gender
      });
      // 只有在第一次加载且有参数时自动触发
      const hasAutoTriggered = window.sessionStorage.getItem('bazi_auto_triggered');
      if (!hasAutoTriggered) {
        window.sessionStorage.setItem('bazi_auto_triggered', 'true');
        setTimeout(() => handleCalculate('FREE_PART1'), 500);
      }
    }

    // 恢复分享追踪轮询
    const savedTrackId = window.localStorage.getItem('pending_track_id');
    if (savedTrackId && !pollIntervalRef.current) {
      setIsWaitingForFriend(true);
      startPolling(savedTrackId);
    }

    if (refId) {
      fetch(`/api/share?id=${refId}&action=click`).catch(() => {});
    }

    setShareUrl(window.location.origin + window.location.pathname);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [isMounted, handleCalculate, startPolling]);

  const handleShareAndTrack = useCallback(async () => {
    if (isSharing) return;
    setIsSharing(true);
    
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    
    const trackId = Math.random().toString(36).slice(2, 10);
    const baseUrl = shareUrl || (typeof window !== 'undefined' ? window.location.origin + window.location.pathname : '');
    if (!baseUrl) {
      setIsSharing(false);
      return;
    }

    const url = new URL(baseUrl);
    url.searchParams.set('ref', trackId);
    url.searchParams.set('lang', lang);
    url.searchParams.set('y', formData.year);
    url.searchParams.set('m', formData.month);
    url.searchParams.set('d', formData.day);
    url.searchParams.set('h', formData.hour);
    url.searchParams.set('g', formData.gender);
    
    const trackableUrl = url.toString();
    const isMobile = typeof navigator !== 'undefined' && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    let shared = false;
    try {
      if (isMobile && navigator.share) {
        await navigator.share({
          title: 'FateMatrices',
          text: lang === 'EN' ? 'Check my destiny!' : '来看我的赛博命盘！',
          url: trackableUrl
        });
        shared = true;
      }
    } catch (error) {
      console.warn('Native share failed:', error);
    }

    if (!shared) {
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(trackableUrl);
          alert(t.linkCopied);
        } else {
          // 降级处理
          const textArea = document.createElement("textarea");
          textArea.value = trackableUrl;
          document.body.appendChild(textArea);
          textArea.select();
          document.execCommand('copy');
          document.body.removeChild(textArea);
          alert(t.linkCopied);
        }
      } catch (error) {
        console.error('Copy failed:', error);
        alert(t.copyFailed);
        setIsSharing(false);
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
    setIsSharing(false);
    window.localStorage.setItem('pending_track_id', trackId);

    startPolling(trackId);
  }, [shareUrl, lang, formData, t, startPolling, isSharing]);

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
      if (!data.success || !data.approvalUrl) {
        alert(data.error || t.networkError);
        setPaypalProcessing(false);
        return;
      }

      // Store orderId for later capture
      setCurrentOrderId(data.orderId);

      // Open PayPal approval page in a new tab
      const paypalWindow = window.open(data.approvalUrl, '_blank', 'width=600,height=700');

      if (!paypalWindow) {
        // Popup blocked — fallback to full-page redirect
        window.location.href = data.approvalUrl;
        return;
      }

      // Poll for popup close, then capture
      const pollTimer = setInterval(async () => {
        if (paypalWindow.closed) {
          clearInterval(pollTimer);
          // User came back — capture the order
          try {
            const captureRes = await fetch('/api/paypal/capture-order', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ paypalOrderId: data.paypalOrderId, orderId: data.orderId }),
            });
            const captureData = await captureRes.json();
            if (captureData.success) {
              setShowPayModal(false);
              setWalletTail('');
              setPaymentMethod('TRC20');
              setPaypalProcessing(false);
              await handleCalculate(selectedPlan.id, data.orderId);
            } else {
              alert(t.alertWait);
              setPaypalProcessing(false);
            }
          } catch {
            alert(t.networkError);
            setPaypalProcessing(false);
          }
        }
      }, 1000);

      // Safety timeout — stop polling after 5 min
      setTimeout(() => {
        clearInterval(pollTimer);
        setPaypalProcessing(false);
      }, 300000);

    } catch {
      alert(t.networkError);
      setPaypalProcessing(false);
    }
  }, [selectedPlan, isChecking, t, handleCalculate]);

  const verifyPayoneerPayment = useCallback(async () => {
    if (!selectedPlan || isChecking) return;
    setIsChecking(true);
    try {
      const res = await fetch('/api/payoneer-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create',
          planId: selectedPlan.id,
        })
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

  const formFields = [
    { k: 'year' as const, label: t.y },
    { k: 'month' as const, label: t.m },
    { k: 'day' as const, label: t.d },
    { k: 'hour' as const, label: t.h }
  ];

  if (!isMounted) {
    return <LoadingSkeleton type="BAZI" lang={lang} />;
  }

  return (
    <div className="min-h-screen bg-transparent text-white p-4 font-sans selection:bg-cyan-500/30 overflow-x-hidden relative">
      {/* Room Specific Glow */}
      <div className="fixed top-[20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-500/10 blur-[120px] pointer-events-none z-[-1]"></div>
      <div className="fixed bottom-[10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-500/5 blur-[100px] pointer-events-none z-[-1]"></div>
      <div className="absolute top-4 right-4 flex gap-2 z-50">
        <button 
          onClick={() => setLang('EN')}
          aria-label={t.langEN}
          aria-pressed={lang === 'EN'}
          className={`px-3 py-1 rounded text-[10px] border transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-[#030712] ${
            lang === 'EN' ? 'bg-cyan-500 text-black border-cyan-500 font-bold' : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-gray-300'
          }`}
        >
          EN
        </button>
        <button 
          onClick={() => setLang('CN')}
          aria-label={t.langCN}
          aria-pressed={lang === 'CN'}
          className={`px-3 py-1 rounded text-[10px] border transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-[#030712] ${
            lang === 'CN' ? 'bg-cyan-500 text-black border-cyan-500 font-bold' : 'border-gray-800 text-gray-400 hover:border-gray-600 hover:text-gray-300'
          }`}
        >
          中文
        </button>
      </div>

      <div className="absolute top-4 left-4 z-50">
        <button
          onClick={navigateBack}
          disabled={isNavigating}
          aria-label={t.back}
          className="px-4 py-2 rounded-xl text-[10px] border border-gray-800 text-gray-400 uppercase tracking-widest transition-all hover:border-gray-600 hover:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-[#030712] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isNavigating ? '...' : t.back}
        </button>
      </div>

      <div className="max-w-4xl mx-auto py-16 space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <header className="text-center space-y-2">
          <h1 className="text-5xl font-black italic tracking-tighter uppercase">
            {lang === 'EN' ? 'Eastern' : '东方能量'}
            <span className="text-cyan-500">{lang === 'EN' ? 'Matrix' : '罗盘'}</span>
          </h1>
        </header>

        <div className="bg-[#0a0f1d] p-6 rounded-[2.5rem] border border-gray-800 shadow-xl">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {formFields.map(item => (
              <div key={item.k} className="bg-black/40 border border-gray-800 rounded-2xl p-3 flex flex-col items-center">
                <span className="text-[9px] text-gray-500 uppercase mb-1 font-bold">{item.label}</span>
                <input
                  type="text"
                  inputMode="numeric"
                  value={formData[item.k]}
                  onChange={e => {
                    const val = e.target.value.replace(/[^0-9]/g, '');
                    setFormData(prev => ({ ...prev, [item.k]: val }));
                  }}
                  className="bg-transparent text-white text-center text-xl font-bold w-full outline-none focus:text-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-[#0a0f1d]"
                  aria-label={item.label}
                  maxLength={item.k === 'year' ? 4 : 2}
                />
              </div>
            ))}
          </div>

          <div className="mt-4 flex gap-3">
            <button
              onClick={() => setFormData({ ...formData, gender: 'male' })}
              aria-label={t.male}
              aria-pressed={formData.gender === 'male'}
              className={`flex-1 py-4 rounded-2xl font-black text-xs transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-[#0a0f1d] ${
                formData.gender === 'male' ? 'bg-cyan-500 text-black' : 'bg-gray-800 hover:bg-gray-700'
              }`}
            >
              {t.male}
            </button>
            <button
              onClick={() => setFormData({ ...formData, gender: 'female' })}
              aria-label={t.female}
              aria-pressed={formData.gender === 'female'}
              className={`flex-1 py-4 rounded-2xl font-black text-xs transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-[#0a0f1d] ${
                formData.gender === 'female' ? 'bg-cyan-500 text-black' : 'bg-gray-800 hover:bg-gray-700'
              }`}
            >
              {t.female}
            </button>
          </div>

          {readLevel === 'NONE' && (
            <button
              onClick={() => handleCalculate('FREE_PART1')}
              disabled={isAnalyzing}
              aria-label={t.btnGen1}
              aria-busy={isAnalyzing}
              className="w-full mt-6 py-5 bg-gradient-to-r from-blue-700 to-cyan-500 rounded-2xl font-black uppercase transition-all shadow-[0_0_30px_rgba(37,99,235,0.3)] hover:scale-[1.02] focus:outline-none focus:ring-4 focus:ring-cyan-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? t.btnWait : t.btnGen1}
            </button>
          )}
        </div>

        {(interpretation || isAnalyzing) && (
          <div className="space-y-8 animate-in fade-in duration-700">
            <div className="bg-[#0a0f1d] p-8 rounded-[2.5rem] border border-cyan-900/30 space-y-8 relative">
              <div className="flex flex-col md:flex-row gap-8 items-center border-b border-gray-800 pb-8">
                <div className="w-full md:w-1/2 h-64">
                  <ResponsiveContainerComponent width="100%" height="100%">
                    <RadarChartComponent cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                      <PolarGridComponent stroke="#374151" />
                      <PolarAngleAxisComponent dataKey="subject" tick={{ fill: '#06b6d4', fontSize: 10, fontWeight: 'bold' }} />
                      <PolarRadiusAxisComponent angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                      <RadarComponent name="WuXing" dataKey="A" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} isAnimationActive={true} />
                    </RadarChartComponent>
                  </ResponsiveContainerComponent>
                </div>

                <div className="w-full md:w-1/2 space-y-4">
                  <div className="bg-black/50 p-4 rounded-2xl border border-gray-800 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{lang === 'EN' ? 'Auspicious Color' : '本命开运色'}</p>
                      <p className="text-sm font-black font-mono" style={{ color: luckyTags.color }}>{luckyTags.color}</p>
                    </div>
                    <div className="w-6 h-6 rounded-full" style={{ backgroundColor: luckyTags.color }}></div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-black/50 p-4 rounded-2xl border border-gray-800">
                      <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{lang === 'EN' ? 'Wealth Dir' : '财富吉方'}</p>
                      <p className="text-sm font-black text-cyan-400">{luckyTags.dir}</p>
                    </div>
                    <div className="bg-black/50 p-4 rounded-2xl border border-gray-800">
                      <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{lang === 'EN' ? 'Core Element' : '核心用神'}</p>
                      <p className="text-sm font-black text-white">{luckyTags.element}</p>
                    </div>
                  </div>
                </div>
              </div>

              <h3 className="text-2xl font-black text-cyan-500 italic uppercase tracking-tighter mt-8">{t.lineTitle}</h3>
              <div className="h-48 w-full">
                <ResponsiveContainerComponent width="100%" height="100%">
                  <LineChartComponent data={chartData}>
                    <LineComponent 
                      type="monotone" 
                      dataKey="energy" 
                      stroke="#06b6d4" 
                      strokeWidth={4} 
                      dot={false} 
                      isAnimationActive={true}
                      animationDuration={2000}
                      animationEasing="ease-in-out"
                    />
                  </LineChartComponent>
                </ResponsiveContainerComponent>
              </div>

              <div className="bg-black/40 p-8 rounded-[2rem] border border-gray-800 italic text-gray-200 text-sm leading-relaxed whitespace-pre-line tracking-wide mt-8 relative overflow-hidden">
                {isAnalyzing && (
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-10 animate-in fade-in duration-300">
                    <div className="flex flex-col items-center space-y-4">
                      <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
                      <p className="text-cyan-500 font-black text-xs tracking-widest uppercase animate-pulse">{t.btnWait}</p>
                    </div>
                  </div>
                )}
                {interpretation}
                {(readLevel === 'PART1' || readLevel === 'PART2') && (
                  <span className="animate-pulse text-cyan-500 font-black mt-2 block">{t.denied}</span>
                )}
              </div>

              {luckyTags.rawElement && (
                <ArtifactRecommender 
                  room="BAZI"
                  element={luckyTags.rawElement} 
                  lang={lang} 
                  onPurchase={(price) => handleOpenPayModal({ id: 'ELITE', price }, true)} 
                />
              )}
            </div>

            {readLevel === 'PART1' && !isWaitingForFriend && (
              <div className="space-y-4 text-center">
                <p className="text-cyan-400 font-black tracking-[0.2em] text-xs">{t.shareTip}</p>
                <button 
                  onClick={handleShareAndTrack} 
                  className="w-full py-5 rounded-2xl bg-cyan-600 text-white font-black uppercase shadow-[0_0_30px_rgba(6,182,212,0.4)] hover:scale-[1.02] transition-transform focus:outline-none focus:ring-4 focus:ring-cyan-500/50"
                  aria-label={t.btnShare}
                >
                  {t.btnShare}
                </button>
              </div>
            )}

            {readLevel === 'PART1' && isWaitingForFriend && (
              <div className="p-8 bg-cyan-900/10 border border-cyan-500/30 rounded-3xl text-center space-y-4 animate-in zoom-in">
                <div className="animate-spin text-4xl mb-4 text-cyan-500">⌛</div>
                <p className="text-cyan-400 font-black text-sm animate-pulse">{t.waiting}</p>
                <button 
                  onClick={() => handleCalculate('FREE_PART2')} 
                  className="w-full py-3 rounded-xl border border-gray-700 text-gray-500 text-[10px] uppercase font-bold hover:text-white transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  aria-label={t.btnManual}
                >
                  {t.btnManual}
                </button>
                <div className="pt-6 border-t border-cyan-900/30">
                  <button
                    onClick={() => handleOpenPayModal({ id: 'LITE', price: '10' })}
                    className="w-full py-4 rounded-xl border border-cyan-500 text-cyan-400 text-xs font-black uppercase hover:bg-cyan-500/10 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    aria-label={t.skipWait}
                  >
                    {t.skipWait}
                  </button>
                </div>
              </div>
            )}

            {readLevel === 'PART2' && (
              <div className="space-y-6 animate-in slide-in-from-bottom-4 mt-8">
                <div className="text-center">
                  <p className="text-red-400 font-black tracking-[0.2em] uppercase text-xs animate-pulse">{t.friendClicked}</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { id: 'LITE' as const, price: '10', name: t.liteName, highlight: false },
                    { id: 'ELITE' as const, price: '29.9', name: t.eliteName, highlight: true }
                  ].map(plan => (
                    <button
                      key={plan.id}
                      onClick={() => handleOpenPayModal({ id: plan.id, price: plan.price })}
                      className={`p-6 rounded-[2.5rem] border cursor-pointer hover:scale-105 transition-all group focus:outline-none focus:ring-4 focus:ring-cyan-500/50 ${
                        plan.highlight
                          ? 'border-cyan-500 bg-cyan-500/5 shadow-[0_0_30px_rgba(6,182,212,0.1)]'
                          : 'border-gray-800 bg-gray-900/50'
                      }`}
                      aria-label={`Select ${plan.name} plan for $${plan.price}`}
                    >
                      <div className="text-center font-black">
                        <div className="text-[10px] text-cyan-400 uppercase mb-1">{plan.id} READ</div>
                        <div className="text-3xl mb-1">${plan.price}</div>
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