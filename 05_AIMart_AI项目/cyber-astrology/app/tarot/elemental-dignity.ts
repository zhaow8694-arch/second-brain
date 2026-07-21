import { ElementType, getCardElement } from './card-element-map';

interface ElementalStrengthResult {
  fire: number;
  water: number;
  air: number;
  earth: number;
  spirit: number;
}

interface CardInfo {
  name: string;
  index: number;
}

const ELEMENT_RELATIONS: Record<ElementType, { friendly: ElementType[]; hostile: ElementType[] }> = {
  fire: { friendly: ['air'], hostile: ['water'] },
  water: { friendly: ['earth'], hostile: ['fire'] },
  air: { friendly: ['fire'], hostile: ['earth'] },
  earth: { friendly: ['water'], hostile: ['air'] },
  spirit: { friendly: ['fire', 'water', 'air', 'earth'], hostile: [] }
};

export function calculateElementalStrength(cards: CardInfo[]): ElementalStrengthResult {
  const elements = cards.map(card => getCardElement(card.name, card.index));
  
  const baseScores: Record<ElementType, number> = {
    fire: 0, water: 0, air: 0, earth: 0, spirit: 0
  };
  
  elements.forEach(el => { baseScores[el] += 20; });
  
  const multiplier: Record<ElementType, number> = {
    fire: 1.0, water: 1.0, air: 1.0, earth: 1.0, spirit: 1.0
  };
  
  const [e1, e2, e3] = elements;
  
  if (e1 === e2 && e2 === e3) {
    multiplier[e1] = 1.5;
  } else if (e1 === e2 || e2 === e3 || e1 === e3) {
    const sameEl = e1 === e2 ? e1 : (e2 === e3 ? e2 : e1);
    const otherEl = elements.find(el => el !== sameEl)!;
    multiplier[sameEl] = 1.2;
    if (ELEMENT_RELATIONS[sameEl].friendly.includes(otherEl)) {
      multiplier[otherEl] = 1.1;
    } else if (ELEMENT_RELATIONS[sameEl].hostile.includes(otherEl)) {
      multiplier[sameEl] = 0.9;
      multiplier[otherEl] = 0.8;
    }
  }
  
  const majorCount = cards.filter(c => c.index >= 0 && c.index <= 21).length;
  if (majorCount >= 2) {
    Object.keys(multiplier).forEach(k => { multiplier[k as ElementType] *= 1.1; });
  }
  
  const result: ElementalStrengthResult = { fire: 0, water: 0, air: 0, earth: 0, spirit: 0 };
  let maxScore = 0;
  
  Object.keys(baseScores).forEach(k => {
    const el = k as ElementType;
    const raw = baseScores[el] * multiplier[el];
    result[el] = raw;
    maxScore = Math.max(maxScore, raw);
  });
  
  if (maxScore > 0) {
    Object.keys(result).forEach(k => {
      const el = k as ElementType;
      result[el] = Math.min(100, Math.round((result[el] / maxScore) * 100));
    });
  }
  
  return result;
}

export function generateLuckyTags(cards: CardInfo[], lang: 'EN' | 'CN'): {
  freq: string;
  karma: string;
  guide: string;
} {
  const elements = cards.map(card => getCardElement(card.name, card.index));
  const majorCount = cards.filter(c => c.index >= 0 && c.index <= 21).length;
  
  const uniqueElements = new Set(elements).size;
  const baseFreq = 300 + uniqueElements * 100 + majorCount * 50;
  const freq = baseFreq.toFixed(2);
  
  let conflictScore = 0;
  for (let i = 0; i < elements.length; i++) {
    for (let j = i + 1; j < elements.length; j++) {
      if (ELEMENT_RELATIONS[elements[i]].hostile.includes(elements[j])) {
        conflictScore++;
      }
    }
  }
  const karmaPercent = 40 + (3 - conflictScore) * 20;
  
  const elementCount: Record<string, number> = { fire: 0, water: 0, air: 0, earth: 0 };
  elements.forEach(el => { if (el !== 'spirit') elementCount[el]++; });
  const dominant = Object.entries(elementCount).sort((a, b) => b[1] - a[1])[0][0];
  
  const guidesEN: Record<string, string> = {
    fire: 'The Magus', water: 'The Empress', air: 'The Fool', earth: 'The Emperor'
  };
  const guidesCN: Record<string, string> = {
    fire: '魔术师之影', water: '女皇意志', air: '愚者之心', earth: '帝王之盾'
  };
  
  return {
    freq,
    karma: `${karmaPercent}%`,
    guide: lang === 'EN' ? guidesEN[dominant] : guidesCN[dominant]
  };
}