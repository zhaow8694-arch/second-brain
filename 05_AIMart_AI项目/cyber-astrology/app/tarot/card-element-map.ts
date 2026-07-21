// 塔罗牌元素类型
export type ElementType = 'fire' | 'water' | 'air' | 'earth' | 'spirit';

// 大阿卡纳元素映射（金色黎明体系）
export const MAJOR_ARCANA_ELEMENT: Record<number, ElementType> = {
  0: 'air',      // 愚者
  1: 'air',      // 魔术师
  2: 'water',    // 女祭司
  3: 'earth',    // 女皇
  4: 'fire',     // 皇帝
  5: 'earth',    // 教皇
  6: 'air',      // 恋人
  7: 'water',    // 战车
  8: 'fire',     // 力量
  9: 'earth',    // 隐士
  10: 'fire',    // 命运之轮
  11: 'air',     // 正义
  12: 'water',   // 倒吊人
  13: 'water',   // 死神
  14: 'fire',    // 节制
  15: 'earth',   // 恶魔
  16: 'fire',    // 高塔
  17: 'air',     // 星星
  18: 'water',   // 月亮
  19: 'fire',    // 太阳
  20: 'spirit',  // 审判
  21: 'spirit'   // 世界
};

// 小阿卡纳元素映射
export const MINOR_ARCANA_ELEMENT: Record<string, ElementType> = {
  'wands': 'fire',
  'cups': 'water',
  'swords': 'air',
  'pentacles': 'earth'
};

// 根据牌名获取元素
export function getCardElement(cardName: string, index?: number): ElementType {
  if (index !== undefined && index >= 0 && index <= 21) {
    return MAJOR_ARCANA_ELEMENT[index];
  }
  
  const lowerName = cardName.toLowerCase();
  if (lowerName.includes('wand') || lowerName.includes('权杖')) return 'fire';
  if (lowerName.includes('cup') || lowerName.includes('圣杯')) return 'water';
  if (lowerName.includes('sword') || lowerName.includes('宝剑')) return 'air';
  if (lowerName.includes('pentacle') || lowerName.includes('coin') || lowerName.includes('星币')) return 'earth';
  
  const chineseMap: Record<string, ElementType> = {
    '愚者': 'air', '魔术师': 'air', '女祭司': 'water', '女皇': 'earth', '皇帝': 'fire',
    '教皇': 'earth', '恋人': 'air', '战车': 'water', '力量': 'fire', '隐士': 'earth',
    '命运之轮': 'fire', '正义': 'air', '倒吊人': 'water', '死神': 'water', '节制': 'fire',
    '恶魔': 'earth', '高塔': 'fire', '星星': 'air', '月亮': 'water', '太阳': 'fire',
    '审判': 'spirit', '世界': 'spirit'
  };
  
  return chineseMap[cardName] || 'spirit';
}