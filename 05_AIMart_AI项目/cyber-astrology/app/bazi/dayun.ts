// ==========================================
// 大运趋势计算
// ==========================================

import { BaziPillars } from './wangshuai';

const GAN_WUXING: Record<string, string> = {
  '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
  '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
};

const ZHI_WUXING: Record<string, string> = {
  '子': '水', '丑': '土', '寅': '木', '卯': '木',
  '辰': '土', '巳': '火', '午': '火', '未': '土',
  '申': '金', '酉': '金', '戌': '土', '亥': '水'
};

const WUXING_RELATION: Record<string, Record<string, number>> = {
  '木': { '木': 1.0, '火': 0.8, '土': 0.6, '金': 0.4, '水': 1.2 },
  '火': { '木': 1.2, '火': 1.0, '土': 0.8, '金': 0.6, '水': 0.4 },
  '土': { '木': 0.4, '火': 1.2, '土': 1.0, '金': 0.8, '水': 0.6 },
  '金': { '木': 0.6, '火': 0.4, '土': 1.2, '金': 1.0, '水': 0.8 },
  '水': { '木': 0.8, '火': 0.6, '土': 0.4, '金': 1.2, '水': 1.0 }
};

export interface DayunData {
  startAge: number;
  pillars: Array<{ gan: string; zhi: string }>;
}

export interface TrendPoint {
  age: number;
  energy: number;
}

export function calculateDayunSequence(
  bazi: BaziPillars,
  gender: 'male' | 'female',
  lunarMonth: number,
  lunarYearGan: string
): DayunData {
  const isYangYear = ['甲', '丙', '戊', '庚', '壬'].includes(lunarYearGan);
  const isShunPai = (isYangYear && gender === 'male') || (!isYangYear && gender === 'female');
  const startAge = Math.floor((lunarMonth * 3 + (isShunPai ? 1 : -1) * 2) / 12) + 1;
  
  const ganSequence = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
  const zhiSequence = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
  
  const ganIndex = ganSequence.indexOf(bazi.month.gan);
  const zhiIndex = zhiSequence.indexOf(bazi.month.zhi);
  
  const pillars: Array<{ gan: string; zhi: string }> = [];
  for (let i = 1; i <= 8; i++) {
    const offset = isShunPai ? i : -i;
    const newGanIndex = (ganIndex + offset + 10) % 10;
    const newZhiIndex = (zhiIndex + offset + 12) % 12;
    pillars.push({ gan: ganSequence[newGanIndex], zhi: zhiSequence[newZhiIndex] });
  }
  
  return { startAge, pillars };
}

export function calculateDayunTrend(bazi: BaziPillars, dayun: DayunData): TrendPoint[] {
  const dayElement = GAN_WUXING[bazi.day.gan] || '木';
  const trend: TrendPoint[] = [];
  
  for (let age = 1; age <= 100; age++) {
    let dayunIndex = Math.floor((age - dayun.startAge) / 10);
    if (dayunIndex < 0) dayunIndex = 0;
    if (dayunIndex >= dayun.pillars.length) dayunIndex = dayun.pillars.length - 1;
    
    const currentDayun = dayun.pillars[dayunIndex];
    const dayunZhiElement = ZHI_WUXING[currentDayun.zhi] || '土';
    const dayunEffect = WUXING_RELATION[dayElement]?.[dayunZhiElement] || 1.0;
    
    const yearInDayun = (age - dayun.startAge) % 10;
    const ganWeight = yearInDayun < 5 ? 0.6 : 0.4;
    
    const dayunGanElement = GAN_WUXING[currentDayun.gan] || '木';
    const ganEffect = WUXING_RELATION[dayElement]?.[dayunGanElement] || 1.0;
    const combinedEffect = ganEffect * ganWeight + dayunEffect * (1 - ganWeight);
    
    const baseEnergy = 50;
    const ageWave = Math.sin(age / 10) * 8;
    const dayunBonus = (combinedEffect - 1.0) * 30;
    let energy = baseEnergy + ageWave + dayunBonus;
    
    const yearPillar = 60 + ((age - 1) % 60);
    const yearSeed = (yearPillar * 7) % 15;
    energy += (yearSeed - 7) * 0.5;
    
    energy = Math.max(5, Math.min(95, energy));
    trend.push({ age, energy: Math.round(energy) });
  }
  
  return trend;
}