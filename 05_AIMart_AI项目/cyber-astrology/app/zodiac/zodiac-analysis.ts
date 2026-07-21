// ==========================================
// 星座数据库
// ==========================================

export interface ZodiacInfo {
  name: string;
  element: 'fire' | 'earth' | 'air' | 'water';
  modality: 'cardinal' | 'fixed' | 'mutable';
  polarity: 'masculine' | 'feminine';
  rulingPlanet: string;
  exaltedPlanet?: string;
  detrimentPlanet?: string;
  fallPlanet?: string;
}

export const ZODIAC_DATABASE: Record<string, ZodiacInfo> = {
  '白羊座': { name: '白羊座', element: 'fire', modality: 'cardinal', polarity: 'masculine', rulingPlanet: 'Mars', exaltedPlanet: 'Sun', detrimentPlanet: 'Venus', fallPlanet: 'Saturn' },
  'Aries': { name: 'Aries', element: 'fire', modality: 'cardinal', polarity: 'masculine', rulingPlanet: 'Mars', exaltedPlanet: 'Sun', detrimentPlanet: 'Venus', fallPlanet: 'Saturn' },
  '金牛座': { name: '金牛座', element: 'earth', modality: 'fixed', polarity: 'feminine', rulingPlanet: 'Venus', exaltedPlanet: 'Moon', detrimentPlanet: 'Pluto', fallPlanet: 'Uranus' },
  'Taurus': { name: 'Taurus', element: 'earth', modality: 'fixed', polarity: 'feminine', rulingPlanet: 'Venus', exaltedPlanet: 'Moon', detrimentPlanet: 'Pluto', fallPlanet: 'Uranus' },
  '双子座': { name: '双子座', element: 'air', modality: 'mutable', polarity: 'masculine', rulingPlanet: 'Mercury', detrimentPlanet: 'Jupiter', fallPlanet: 'Venus' },
  'Gemini': { name: 'Gemini', element: 'air', modality: 'mutable', polarity: 'masculine', rulingPlanet: 'Mercury', detrimentPlanet: 'Jupiter', fallPlanet: 'Venus' },
  '巨蟹座': { name: '巨蟹座', element: 'water', modality: 'cardinal', polarity: 'feminine', rulingPlanet: 'Moon', exaltedPlanet: 'Jupiter', detrimentPlanet: 'Saturn', fallPlanet: 'Mars' },
  'Cancer': { name: 'Cancer', element: 'water', modality: 'cardinal', polarity: 'feminine', rulingPlanet: 'Moon', exaltedPlanet: 'Jupiter', detrimentPlanet: 'Saturn', fallPlanet: 'Mars' },
  '狮子座': { name: '狮子座', element: 'fire', modality: 'fixed', polarity: 'masculine', rulingPlanet: 'Sun', detrimentPlanet: 'Uranus', fallPlanet: 'Neptune' },
  'Leo': { name: 'Leo', element: 'fire', modality: 'fixed', polarity: 'masculine', rulingPlanet: 'Sun', detrimentPlanet: 'Uranus', fallPlanet: 'Neptune' },
  '处女座': { name: '处女座', element: 'earth', modality: 'mutable', polarity: 'feminine', rulingPlanet: 'Mercury', exaltedPlanet: 'Mercury', detrimentPlanet: 'Neptune', fallPlanet: 'Venus' },
  'Virgo': { name: 'Virgo', element: 'earth', modality: 'mutable', polarity: 'feminine', rulingPlanet: 'Mercury', exaltedPlanet: 'Mercury', detrimentPlanet: 'Neptune', fallPlanet: 'Venus' },
  '天秤座': { name: '天秤座', element: 'air', modality: 'cardinal', polarity: 'masculine', rulingPlanet: 'Venus', exaltedPlanet: 'Saturn', detrimentPlanet: 'Mars', fallPlanet: 'Sun' },
  'Libra': { name: 'Libra', element: 'air', modality: 'cardinal', polarity: 'masculine', rulingPlanet: 'Venus', exaltedPlanet: 'Saturn', detrimentPlanet: 'Mars', fallPlanet: 'Sun' },
  '天蝎座': { name: '天蝎座', element: 'water', modality: 'fixed', polarity: 'feminine', rulingPlanet: 'Pluto', exaltedPlanet: 'Uranus', detrimentPlanet: 'Venus', fallPlanet: 'Moon' },
  'Scorpio': { name: 'Scorpio', element: 'water', modality: 'fixed', polarity: 'feminine', rulingPlanet: 'Pluto', exaltedPlanet: 'Uranus', detrimentPlanet: 'Venus', fallPlanet: 'Moon' },
  '射手座': { name: '射手座', element: 'fire', modality: 'mutable', polarity: 'masculine', rulingPlanet: 'Jupiter', detrimentPlanet: 'Mercury', fallPlanet: 'Ceres' },
  'Sagittarius': { name: 'Sagittarius', element: 'fire', modality: 'mutable', polarity: 'masculine', rulingPlanet: 'Jupiter', detrimentPlanet: 'Mercury', fallPlanet: 'Ceres' },
  '摩羯座': { name: '摩羯座', element: 'earth', modality: 'cardinal', polarity: 'feminine', rulingPlanet: 'Saturn', exaltedPlanet: 'Mars', detrimentPlanet: 'Moon', fallPlanet: 'Jupiter' },
  'Capricorn': { name: 'Capricorn', element: 'earth', modality: 'cardinal', polarity: 'feminine', rulingPlanet: 'Saturn', exaltedPlanet: 'Mars', detrimentPlanet: 'Moon', fallPlanet: 'Jupiter' },
  '水瓶座': { name: '水瓶座', element: 'air', modality: 'fixed', polarity: 'masculine', rulingPlanet: 'Uranus', detrimentPlanet: 'Sun', fallPlanet: 'Neptune' },
  'Aquarius': { name: 'Aquarius', element: 'air', modality: 'fixed', polarity: 'masculine', rulingPlanet: 'Uranus', detrimentPlanet: 'Sun', fallPlanet: 'Neptune' },
  '双鱼座': { name: '双鱼座', element: 'water', modality: 'mutable', polarity: 'feminine', rulingPlanet: 'Neptune', exaltedPlanet: 'Venus', detrimentPlanet: 'Mercury', fallPlanet: 'Mercury' },
  'Pisces': { name: 'Pisces', element: 'water', modality: 'mutable', polarity: 'feminine', rulingPlanet: 'Neptune', exaltedPlanet: 'Venus', detrimentPlanet: 'Mercury', fallPlanet: 'Mercury' }
};

// ==========================================
// MBTI 认知功能映射
// ==========================================

interface MBTIProfile {
  dominant: string;
  auxiliary: string;
  elementBias: Record<string, number>;
  decisionFactor: number;
  innovationFactor: number;
  practicalFactor: number;
}

export const MBTI_DATABASE: Record<string, MBTIProfile> = {
  'INTJ': { dominant: 'Ni', auxiliary: 'Te', elementBias: { air: 1.3, fire: 1.1 }, decisionFactor: 1.5, innovationFactor: 1.4, practicalFactor: 0.9 },
  'INTP': { dominant: 'Ti', auxiliary: 'Ne', elementBias: { air: 1.4, fire: 1.0 }, decisionFactor: 1.1, innovationFactor: 1.5, practicalFactor: 0.8 },
  'ENTJ': { dominant: 'Te', auxiliary: 'Ni', elementBias: { fire: 1.4, air: 1.2 }, decisionFactor: 1.6, innovationFactor: 1.1, practicalFactor: 1.1 },
  'ENTP': { dominant: 'Ne', auxiliary: 'Ti', elementBias: { air: 1.5, fire: 1.1 }, decisionFactor: 1.2, innovationFactor: 1.6, practicalFactor: 0.7 },
  'INFJ': { dominant: 'Ni', auxiliary: 'Fe', elementBias: { water: 1.3, air: 1.1 }, decisionFactor: 1.2, innovationFactor: 1.3, practicalFactor: 1.0 },
  'INFP': { dominant: 'Fi', auxiliary: 'Ne', elementBias: { water: 1.4, air: 1.0 }, decisionFactor: 0.9, innovationFactor: 1.4, practicalFactor: 0.9 },
  'ENFJ': { dominant: 'Fe', auxiliary: 'Ni', elementBias: { fire: 1.3, water: 1.2 }, decisionFactor: 1.3, innovationFactor: 1.2, practicalFactor: 1.0 },
  'ENFP': { dominant: 'Ne', auxiliary: 'Fi', elementBias: { fire: 1.4, water: 1.0 }, decisionFactor: 1.0, innovationFactor: 1.5, practicalFactor: 0.8 },
  'ISTJ': { dominant: 'Si', auxiliary: 'Te', elementBias: { earth: 1.4, air: 1.0 }, decisionFactor: 1.4, innovationFactor: 0.7, practicalFactor: 1.5 },
  'ISFJ': { dominant: 'Si', auxiliary: 'Fe', elementBias: { earth: 1.3, water: 1.1 }, decisionFactor: 1.2, innovationFactor: 0.7, practicalFactor: 1.4 },
  'ESTJ': { dominant: 'Te', auxiliary: 'Si', elementBias: { earth: 1.4, fire: 1.1 }, decisionFactor: 1.6, innovationFactor: 0.8, practicalFactor: 1.4 },
  'ESFJ': { dominant: 'Fe', auxiliary: 'Si', elementBias: { earth: 1.3, water: 1.2 }, decisionFactor: 1.3, innovationFactor: 0.8, practicalFactor: 1.4 },
  'ISTP': { dominant: 'Ti', auxiliary: 'Se', elementBias: { earth: 1.2, fire: 1.2 }, decisionFactor: 1.2, innovationFactor: 1.1, practicalFactor: 1.2 },
  'ISFP': { dominant: 'Fi', auxiliary: 'Se', elementBias: { earth: 1.2, water: 1.2 }, decisionFactor: 1.0, innovationFactor: 1.2, practicalFactor: 1.1 },
  'ESTP': { dominant: 'Se', auxiliary: 'Ti', elementBias: { fire: 1.4, earth: 1.1 }, decisionFactor: 1.4, innovationFactor: 1.1, practicalFactor: 1.1 },
  'ESFP': { dominant: 'Se', auxiliary: 'Fi', elementBias: { fire: 1.4, water: 1.0 }, decisionFactor: 1.1, innovationFactor: 1.2, practicalFactor: 1.0 }
};

// ==========================================
// 行星力量计算
// ==========================================

function calculatePlanetPower(zodiac: ZodiacInfo, planet: string): number {
  let power = 1.0;
  
  if (zodiac.rulingPlanet === planet) power *= 1.5;
  if (zodiac.exaltedPlanet === planet) power *= 1.2;
  if (zodiac.detrimentPlanet === planet) power *= 0.7;
  if (zodiac.fallPlanet === planet) power *= 0.5;
  
  return power;
}

// ==========================================
// 伴侣合盘计算
// ==========================================

function calculateSynastryBonus(self: ZodiacInfo, partner: ZodiacInfo | null): number {
  if (!partner) return 1.0;
  
  let bonus = 1.0;
  
  // 元素关系
  if (self.element === partner.element) {
    bonus += 0.25;
  } else if (
    (self.element === 'fire' && partner.element === 'air') ||
    (self.element === 'air' && partner.element === 'fire') ||
    (self.element === 'water' && partner.element === 'earth') ||
    (self.element === 'earth' && partner.element === 'water')
  ) {
    bonus += 0.15;
  } else if (
    (self.element === 'fire' && partner.element === 'water') ||
    (self.element === 'water' && partner.element === 'fire') ||
    (self.element === 'air' && partner.element === 'earth') ||
    (self.element === 'earth' && partner.element === 'air')
  ) {
    bonus -= 0.10;
  }
  
  // 特质关系
  if (self.modality === partner.modality) {
    bonus += 0.05;
  } else if (
    (self.modality === 'cardinal' && partner.modality === 'mutable') ||
    (self.modality === 'mutable' && partner.modality === 'cardinal') ||
    (self.modality === 'fixed' && partner.modality === 'mutable')
  ) {
    bonus += 0.15;
  }
  
  return Math.max(0.5, Math.min(1.5, bonus));
}

// ==========================================
// 主分析函数
// ==========================================

export interface ZodiacAnalysisResult {
  radar: {
    wealth: number;
    love: number;
    career: number;
    health: number;
    cyber: number;
  };
  luckyTags: {
    color: string;
    freq: string;
    num: string;
    element: string;
  };
}

export function analyzeZodiacFull(
  selfSign: string,
  mbti: string | null,
  partnerSign: string | null,
  lang: 'EN' | 'CN'
): ZodiacAnalysisResult {
  const selfZodiac = ZODIAC_DATABASE[selfSign];
  if (!selfZodiac) {
    throw new Error(`Unknown zodiac sign: ${selfSign}`);
  }
  
  const partnerZodiac = partnerSign ? ZODIAC_DATABASE[partnerSign] : null;
  const mbtiProfile = mbti ? MBTI_DATABASE[mbti] : null;
  
  const elementBase: Record<string, number> = {
    fire: 40, earth: 40, air: 40, water: 40
  };
  
  elementBase[selfZodiac.element] += 30;
  
  if (selfZodiac.modality === 'cardinal') {
    elementBase[selfZodiac.element] += 10;
  } else if (selfZodiac.modality === 'fixed') {
    elementBase[selfZodiac.element] += 8;
  } else {
    elementBase[selfZodiac.element] += 6;
  }
  
  const sunPower = calculatePlanetPower(selfZodiac, 'Sun');
  const moonPower = calculatePlanetPower(selfZodiac, 'Moon');
  const mercuryPower = calculatePlanetPower(selfZodiac, 'Mercury');
  const venusPower = calculatePlanetPower(selfZodiac, 'Venus');
  const marsPower = calculatePlanetPower(selfZodiac, 'Mars');
  const jupiterPower = calculatePlanetPower(selfZodiac, 'Jupiter');
  const uranusPower = calculatePlanetPower(selfZodiac, 'Uranus');
  
  const synastryBonus = calculateSynastryBonus(selfZodiac, partnerZodiac);
  
  const mbtiElementBias = mbtiProfile?.elementBias || { fire: 1.0, earth: 1.0, air: 1.0, water: 1.0 };
  const decisionFactor = mbtiProfile?.decisionFactor || 1.0;
  const innovationFactor = mbtiProfile?.innovationFactor || 1.0;
  const practicalFactor = mbtiProfile?.practicalFactor || 1.0;
  
  const wealth = (elementBase.earth * 1.5 + venusPower * 30 * 1.2 + (selfZodiac.modality === 'fixed' ? 10 : 0)) * practicalFactor * mbtiElementBias.earth;
  const love = (elementBase.water * 1.5 + venusPower * 30 * 1.5 + (selfZodiac.modality === 'mutable' ? 10 : 0)) * synastryBonus * mbtiElementBias.water;
  const career = (elementBase.fire * 1.5 + (sunPower + marsPower) * 15 + (selfZodiac.modality === 'cardinal' ? 15 : 0)) * decisionFactor * mbtiElementBias.fire;
  const health = ((elementBase.earth + elementBase.fire) * 0.8 + moonPower * 30 * 1.2) + jupiterPower * 5;
  const cyber = (elementBase.air * 1.8 + (mercuryPower + uranusPower) * 20) * innovationFactor * mbtiElementBias.air;
  
  const normalize = (val: number): number => {
    return Math.min(95, Math.max(50, Math.round(val)));
  };
  
  const seed = selfZodiac.element.charCodeAt(0) + selfZodiac.modality.charCodeAt(0);
  const colorHue = (seed * 37) % 360;
  const freqBase = 300 + (selfZodiac.element === 'fire' ? 200 : selfZodiac.element === 'air' ? 150 : selfZodiac.element === 'water' ? 100 : 50) + (mbti ? 50 : 0);
  const luckyNum = (seed * 7) % 99;
  
  const colors = [
    `hsl(${colorHue}, 80%, 60%)`,
    `hsl(${(colorHue + 120) % 360}, 70%, 55%)`,
    `hsl(${(colorHue + 240) % 360}, 75%, 50%)`
  ];
  
  const elementLabel = lang === 'CN'
    ? (selfZodiac.element === 'fire' ? '火' : selfZodiac.element === 'earth' ? '土' : selfZodiac.element === 'air' ? '风' : '水')
    : selfZodiac.element;
  
  return {
    radar: {
      wealth: normalize(wealth),
      love: normalize(love),
      career: normalize(career),
      health: normalize(health),
      cyber: normalize(cyber)
    },
    luckyTags: {
      color: colors[0],
      freq: freqBase.toFixed(2),
      num: luckyNum.toString(),
      element: elementLabel
    }
  };
}