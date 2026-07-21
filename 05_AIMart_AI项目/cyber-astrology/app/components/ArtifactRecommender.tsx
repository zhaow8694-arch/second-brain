'use client';

import React from 'react';
import Image from 'next/image';

type RoomType = 'BAZI' | 'TAROT' | 'ZODIAC';

interface ArtifactRecommenderProps {
  room: RoomType;
  element: string; // '木' | '火' | '土' | '金' | '水' (对应八字/塔罗/星座元素)
  lang: 'EN' | 'CN';
  onPurchase: (price: string) => void;
}

export const ArtifactRecommender: React.FC<ArtifactRecommenderProps> = ({ room, element, lang, onPurchase }) => {
  
  // 1. 获取不同房间的文案与图片前缀
  const getRoomData = () => {
    switch (room) {
      case 'TAROT':
        return {
          tag: lang === 'EN' ? 'Soul Frequency Catalyst' : '量子共振·灵魂密钥',
          prefix: 'tarot_',
          suffix: '.webp',
          price: '66',
          descTemplate: lang === 'EN' 
            ? 'Embedded with NFC chip. Syncs your soul frequency and Arcana guide to the digital matrix.' 
            : '内置NFC感应芯片。将你的灵魂频率与大阿尔卡纳引导词同步至数字矩阵，永久存证。'
        };
      case 'ZODIAC':
        return {
          tag: lang === 'EN' ? 'Celestial Matrix Beacon' : '星云矩阵·守护信标',
          prefix: 'zodiac_',
          suffix: '.webp',
          price: '88',
          descTemplate: lang === 'EN' 
            ? 'Titanium matrix ring with NFC interstellar pass. Backup your birth chart data forever.' 
            : '钛金矩阵戒指，集成NFC星际通行证。将你的本命星盘数据备份于指尖，赛博永存。'
        };
      default: // BAZI
        return {
          tag: lang === 'EN' ? 'Elemental Resonance Artifact' : '量子共振·五行载体',
          prefix: 'bazi_',
          suffix: '.webp',
          price: '50',
          descTemplate: lang === 'EN' 
            ? 'Stabilize your elemental wave function. Physical carrier for quantum destiny alignment.' 
            : '稳固五行波函数。接入物理载体，实现量子维度的命运对齐与实时护身。'
        };
    }
  };

  const roomData = getRoomData();

  const artifactMap: Record<string, { name: string; imgKey: string }> = {
    '木': {
      name: lang === 'EN' ? 'Wood / Spirit Resonance' : '青龙·青木/灵性命格',
      imgKey: room === 'TAROT' ? 'spirit' : (room === 'ZODIAC' ? 'earth' : 'wood') // 逻辑映射
    },
    '火': {
      name: lang === 'EN' ? 'Fire / Passion Core' : '朱雀·离火能量矩阵',
      imgKey: 'fire'
    },
    '土': {
      name: lang === 'EN' ? 'Earth / Stability Charm' : '坤地·土之承载载体',
      imgKey: 'earth'
    },
    '金': {
      name: lang === 'EN' ? 'Metal / Air Matrix' : '白虎·庚金/风象矩阵',
      imgKey: room === 'TAROT' ? 'air' : (room === 'ZODIAC' ? 'air' : 'metal')
    },
    '水': {
      name: lang === 'EN' ? 'Water / Flow Catalyst' : '玄武·壬水流转信标',
      imgKey: 'water'
    }
  };

  // 处理塔罗/星座特有的 key 映射
  let finalElement = element;
  if (room === 'TAROT' && element === '灵') finalElement = '木';
  if (room === 'TAROT' && element === '风') finalElement = '金';
  if (room === 'ZODIAC' && (element === '风' || element === 'Air')) finalElement = '金';

  const itemInfo = artifactMap[finalElement] || artifactMap['木'];
  const imgSrc = `/items/${roomData.prefix}${itemInfo.imgKey}${roomData.suffix}`;

  return (
    <div className="mt-12 p-8 bg-gradient-to-br from-cyan-900/20 to-blue-900/20 rounded-[3rem] border border-cyan-500/30 backdrop-blur-md animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row items-center gap-8">
        <div className="relative group">
          <div className="absolute inset-0 bg-cyan-500/20 blur-2xl rounded-full group-hover:bg-cyan-500/40 transition-all duration-500"></div>
          <div className="relative w-48 h-48 md:w-56 md:h-56">
            <Image 
              src={imgSrc} 
              alt={itemInfo.name}
              fill
              className="object-contain drop-shadow-[0_0_20px_rgba(6,182,212,0.5)] group-hover:scale-110 transition-transform duration-700"
            />
          </div>
        </div>
        
        <div className="flex-1 text-center md:text-left space-y-4">
          <div className="inline-block px-4 py-1 bg-cyan-500/20 rounded-full border border-cyan-500/30 text-[10px] font-black uppercase tracking-[0.2em] text-cyan-400">
            {roomData.tag}
          </div>
          <h4 className="text-2xl md:text-3xl font-black italic text-white tracking-tight uppercase">
            {itemInfo.name}
          </h4>
          <p className="text-sm text-gray-400 font-medium leading-relaxed max-w-md">
            {roomData.descTemplate}
          </p>
          <div className="pt-4 flex flex-col md:flex-row items-center gap-6">
            <div className="text-3xl font-black text-cyan-500">${roomData.price} <span className="text-xs text-cyan-800">USDT</span></div>
            <button 
              onClick={() => onPurchase(roomData.price)}
              className="px-10 py-4 bg-cyan-500 hover:bg-cyan-400 text-black font-black uppercase tracking-widest text-xs rounded-2xl transition-all shadow-[0_0_30px_rgba(6,182,212,0.3)] hover:shadow-[0_0_50px_rgba(6,182,212,0.5)] transform active:scale-95"
            >
              {lang === 'EN' ? 'Sync & Deliver' : '同步共振·立即供奉'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
