// ==========================================
// 五行旺度计算（基于干支计分 + 月令乘气 + 通根）
// ==========================================

export interface BaziPillars {
  year: { gan: string; zhi: string };
  month: { gan: string; zhi: string };
  day: { gan: string; zhi: string };
  hour: { gan: string; zhi: string };
}

export interface WangShuaiResult {
  木: number;
  火: number;
  土: number;
  金: number;
  水: number;
  levels: Record<string, string>;
  dayMaster: string;
  dayMasterElement: string;
  dayMasterStrength: number;
}

// 天干五行映射
const GAN_WUXING: Record<string, string> = {
  '甲': '木', '乙': '木',
  '丙': '火', '丁': '火',
  '戊': '土', '己': '土',
  '庚': '金', '辛': '金',
  '壬': '水', '癸': '水'
};

// 天干力量基数（位置权重）
const GAN_POSITION_WEIGHT: Record<string, number> = {
  year: 1.0,
  month: 1.2,
  day: 1.5,
  hour: 1.0
};

// 地支藏干（本气/中气/余气）
const ZHI_CANGGAN: Record<string, { main: string; middle?: string; residual?: string }> = {
  '子': { main: '癸' },
  '丑': { main: '己', middle: '癸', residual: '辛' },
  '寅': { main: '甲', middle: '丙', residual: '戊' },
  '卯': { main: '乙' },
  '辰': { main: '戊', middle: '乙', residual: '癸' },
  '巳': { main: '丙', middle: '庚', residual: '戊' },
  '午': { main: '丁', middle: '己' },
  '未': { main: '己', middle: '丁', residual: '乙' },
  '申': { main: '庚', middle: '壬', residual: '戊' },
  '酉': { main: '辛' },
  '戌': { main: '戊', middle: '辛', residual: '丁' },
  '亥': { main: '壬', middle: '甲' }
};

// 藏干强度系数
const CANGGAN_STRENGTH: Record<string, number> = {
  main: 3.0,
  middle: 2.0,
  residual: 1.0
};

// 月令乘气系数
function getMonthMultiplier(dayGan: string, monthZhi: string): number {
  const dayElement = GAN_WUXING[dayGan];
  const monthMainGan = ZHI_CANGGAN[monthZhi].main;
  const monthElement = GAN_WUXING[monthMainGan];
  
  const relation: Record<string, Record<string, string>> = {
    '木': { '木': '比和', '火': '我生', '土': '我克', '金': '克我', '水': '生我' },
    '火': { '火': '比和', '土': '我生', '金': '我克', '水': '克我', '木': '生我' },
    '土': { '土': '比和', '金': '我生', '水': '我克', '木': '克我', '火': '生我' },
    '金': { '金': '比和', '水': '我生', '木': '我克', '火': '克我', '土': '生我' },
    '水': { '水': '比和', '木': '我生', '火': '我克', '土': '克我', '金': '生我' }
  };
  
  const rel = relation[dayElement]?.[monthElement] || '比和';
  
  const multiplierMap: Record<string, number> = {
    '比和': 1.5,
    '生我': 1.2,
    '我生': 0.8,
    '我克': 0.6,
    '克我': 0.5
  };
  
  return multiplierMap[rel] || 1.0;
}

// 通根判断
function hasRoot(gan: string, zhies: string[]): number {
  const element = GAN_WUXING[gan];
  let rootBonus = 0;
  
  zhies.forEach(zhi => {
    const canggan = ZHI_CANGGAN[zhi];
    if (!canggan) return;
    
    if (GAN_WUXING[canggan.main] === element) rootBonus += 0.5;
    if (canggan.middle && GAN_WUXING[canggan.middle] === element) rootBonus += 0.3;
    if (canggan.residual && GAN_WUXING[canggan.residual] === element) rootBonus += 0.2;
  });
  
  return rootBonus;
}

// 计算日主旺衰等级
function getStrengthLevel(strength: number): string {
  if (strength < 0.5) return '弱极';
  if (strength < 1.5) return '太弱';
  if (strength < 3.0) return '较弱';
  if (strength < 5.0) return '偏弱';
  if (strength < 8.0) return '中和';
  if (strength < 12.0) return '偏旺';
  if (strength < 18.0) return '较旺';
  if (strength < 25.0) return '太旺';
  return '旺极';
}

// 主函数：计算八字五行旺度
export function calculateWangShuai(bazi: BaziPillars): WangShuaiResult {
  const scores: Record<string, number> = {
    '木': 0, '火': 0, '土': 0, '金': 0, '水': 0
  };
  
  const pillars = [
    { pos: 'year', gan: bazi.year.gan, zhi: bazi.year.zhi },
    { pos: 'month', gan: bazi.month.gan, zhi: bazi.month.zhi },
    { pos: 'day', gan: bazi.day.gan, zhi: bazi.day.zhi },
    { pos: 'hour', gan: bazi.hour.gan, zhi: bazi.hour.zhi }
  ] as const;
  
  const allZhi = pillars.map(p => p.zhi);
  const monthMultiplier = getMonthMultiplier(bazi.day.gan, bazi.month.zhi);
  
  // 天干计分
  pillars.forEach(pillar => {
    const element = GAN_WUXING[pillar.gan];
    if (!element) return;
    
    let weight = GAN_POSITION_WEIGHT[pillar.pos];
    if (pillar.pos === 'month' || pillar.pos === 'hour') weight += 0.3;
    
    const rootBonus = hasRoot(pillar.gan, allZhi);
    weight *= (1 + rootBonus);
    
    scores[element] += weight;
  });
  
  // 地支藏干计分
  pillars.forEach(pillar => {
    const canggan = ZHI_CANGGAN[pillar.zhi];
    if (!canggan) return;
    
    const mainElement = GAN_WUXING[canggan.main];
    if (mainElement) scores[mainElement] += CANGGAN_STRENGTH.main;
    
    if (canggan.middle) {
      const middleElement = GAN_WUXING[canggan.middle];
      if (middleElement) scores[middleElement] += CANGGAN_STRENGTH.middle;
    }
    
    if (canggan.residual) {
      const residualElement = GAN_WUXING[canggan.residual];
      if (residualElement) scores[residualElement] += CANGGAN_STRENGTH.residual;
    }
  });
  
  // 应用月令乘气系数
  const dayElement = GAN_WUXING[bazi.day.gan];
  if (dayElement) {
    scores[dayElement] *= monthMultiplier;
  }
  
  const dayStrength = scores[dayElement] || 0;
  
  const levels: Record<string, string> = {};
  Object.entries(scores).forEach(([el, score]) => {
    levels[el] = getStrengthLevel(score);
  });
  
  const maxScore = Math.max(...Object.values(scores), 1);
  const normalized: Record<string, number> = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 };
  
  Object.keys(scores).forEach(el => {
    const raw = scores[el];
    const ratio = raw / maxScore;
    normalized[el] = Math.round(20 + ratio * 75);
  });
  
  return {
    木: normalized['木'],
    火: normalized['火'],
    土: normalized['土'],
    金: normalized['金'],
    水: normalized['水'],
    levels,
    dayMaster: bazi.day.gan,
    dayMasterElement: dayElement || '木',
    dayMasterStrength: dayStrength
  };
}

// 计算用神
export function getYongShen(wangshuai: WangShuaiResult): { element: string; direction: string } {
  const dayElement = wangshuai.dayMasterElement;
  const strength = wangshuai.dayMasterStrength;
  
  const keMap: Record<string, string> = { '木': '金', '火': '水', '土': '木', '金': '火', '水': '土' };
  const shengMap: Record<string, string> = { '木': '水', '火': '木', '土': '火', '金': '土', '水': '金' };
  const caiMap: Record<string, string> = { '木': '土', '火': '金', '土': '水', '金': '木', '水': '火' };
  
  let yongShenElement: string;
  
  if (strength < 3.0) {
    yongShenElement = shengMap[dayElement] || '水';
  } else if (strength > 12.0) {
    yongShenElement = keMap[dayElement] || '火';
  } else {
    yongShenElement = caiMap[dayElement] || '土';
  }
  
  const elementNames: Record<string, string> = { '木': '甲木', '火': '丁火', '土': '戊土', '金': '庚金', '水': '壬水' };
  
  return { element: elementNames[yongShenElement] || '甲木', direction: yongShenElement };
}