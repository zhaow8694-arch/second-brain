import { NextResponse } from 'next/server';
import { checkEntitlement, consumeEntitlement } from '@/lib/entitlements';

// ==========================================
// 🎯 配置常量
// ==========================================
const AI_API_URL = process.env.AI_API_URL || 'https://api.deepseek.com';
const AI_API_KEY = process.env.AI_API_KEY || process.env.DEEPSEEK_API_KEY; // 修复：优先读取通用KEY

// 支持的解读类型
const INTERPRETATION_TYPES = ['tarot', 'bazi', 'zodiac'] as const;
type InterpretationType = typeof INTERPRETATION_TYPES[number];

// ==========================================
// 🚀 主处理函数
// ==========================================
export async function POST(req: Request) {
  
  try {
    // 1. 验证请求数据
    const body = await req.json();
    const { type, plan, lang, ...data } = body;
    
    // 验证必填字段
    if (!type || !INTERPRETATION_TYPES.includes(type as InterpretationType)) {
      return NextResponse.json(
        { 
          text: lang === 'CN' 
            ? '❌ 解读类型无效，请选择塔罗、八字或星座。'
            : '❌ Invalid interpretation type. Please choose tarot, bazi, or zodiac.'
        },
        { status: 400 }
      );
    }
    
    // 2a. 权益校验（付费内容）
    const isFreePlan = plan === 'FREE_PART1';
    if (!isFreePlan) {
      const orderId = body.orderId as string | undefined;
      if (!orderId) {
        return NextResponse.json(
          { text: lang === 'CN' ? '⚠️ 请先完成支付以解锁完整解读。' : '⚠️ Please complete payment to unlock the full reading.' },
          { status: 403 }
        );
      }

      const { allowed, entitlement } = await checkEntitlement(orderId);
      if (!allowed) {
        return NextResponse.json(
          { text: lang === 'CN' ? '🔒 权益已过期或使用次数已用完，请重新购买。' : '🔒 Entitlement expired or usage exhausted. Please purchase again.' },
          { status: 403 }
        );
      }

      // Consume one usage right before the API call (best-effort)
      await consumeEntitlement(orderId);
    }

    // 2. 环境变量检查
    if (!AI_API_KEY) {
      console.error('❌ API Key missing. Check environment variables:');
      console.error('   - AI_API_KEY:', !!process.env.AI_API_KEY);
      console.error('   - DEEPSEEK_API_KEY:', !!process.env.DEEPSEEK_API_KEY);
      
      return NextResponse.json({ 
        text: lang === 'CN' 
          ? '🔧 系统配置不完整。请检查：\n1. 在Vercel项目设置中添加AI_API_KEY\n2. 或在本地.env文件中配置' 
          : '🔧 System configuration incomplete. Please:\n1. Add AI_API_KEY in Vercel project settings\n2. Or configure in local .env file'
      }, { status: 200 });
    }
    
    // 3. 智能构建API端点
    const apiEndpoint = buildApiEndpoint(AI_API_URL);
    const userLang = lang === 'EN' ? 'EN' : 'CN'; // 默认中文
    
    // 4. 构建Prompt (满血版高转化逻辑)
    const systemPrompt = buildSystemPrompt(type, userLang, plan);
    const userPrompt = buildUserPrompt(type, data, userLang);
    
    // 5. 构建请求体
    const requestBody = buildRequestBody(type, systemPrompt, userPrompt, plan);
    
    // 6. 发送请求（流式处理）
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${AI_API_KEY}`,
      },
      body: JSON.stringify({
        ...requestBody,
        stream: true, // 开启流式响应
      }),
    });
    
    if (!response.ok) {
      return handleApiError(response, userLang);
    }

    // 使用 ReadableStream 处理流式响应
    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body?.getReader();
        if (!reader) {
          controller.close();
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              const cleanLine = line.trim();
              if (!cleanLine || cleanLine === 'data: [DONE]') continue;
              if (cleanLine.startsWith('data: ')) {
                try {
                  const json = JSON.parse(cleanLine.substring(6));
                  const content = json.choices?.[0]?.delta?.content || '';
                  if (content) {
                    controller.enqueue(new TextEncoder().encode(content));
                  }
                } catch (e) {
                  console.error('Error parsing stream JSON:', e);
                }
              }
            }
          }
        } catch (error) {
          controller.error(error);
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
    
  } catch (error: unknown) {
    console.error('❌ POST /api/chat error:', error);
    
    // 根据错误类型返回不同信息
    let errorMessage = 'Quantum link lost. Please try again.';
    let statusCode = 500;
    
    if (error instanceof Error && error.name === 'AbortError') {
      errorMessage = 'Request timeout. Please try again.';
      statusCode = 408;
    } else if (error instanceof Error && error.message?.includes('Invalid AI response')) {
      errorMessage = 'AI service returned unexpected format.';
      statusCode = 502;
    }
    
    return NextResponse.json(
      { 
        text: errorMessage,
        error: process.env.NODE_ENV === 'development' && error instanceof Error ? error.message : undefined
      },
      { status: statusCode }
    );
  }
}

// ==========================================
// 🛠️ 工具函数
// ==========================================

function buildApiEndpoint(baseUrl: string): string {
  const cleanUrl = baseUrl.replace(/\/+$/, '');
  if (cleanUrl.includes('api.openai.com')) {
    return `${cleanUrl}/v1/chat/completions`;
  } else if (cleanUrl.includes('deepseek.com')) {
    return `${cleanUrl}/chat/completions`;
  } else if (cleanUrl.includes('/v1/chat/completions')) {
    return cleanUrl;
  } else {
    return `${cleanUrl}/v1/chat/completions`;
  }
}

function buildRequestBody(type: string, systemPrompt: string, userPrompt: string, plan: string) {
  const isFreePlan = plan === 'FREE_PART1';
  return {
    model: 'deepseek-chat', 
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ],
    temperature: isFreePlan ? 0.85 : 0.7,
    max_tokens: isFreePlan ? 800 : 1500,
    top_p: 0.9,
    frequency_penalty: 0.1,
    presence_penalty: 0.1,
    stream: false,
  };
}

async function handleApiError(response: Response, lang: 'EN' | 'CN'): Promise<NextResponse> {
  const status = response.status;
  let errorText = '';
  try {
    errorText = await response.text();
    console.error(`❌ API Error ${status}:`, errorText.substring(0, 500));
  } catch {
    errorText = 'No error details';
  }
  
  const errorMessages = {
    CN: {
      400: '请求参数错误，请检查输入格式。',
      401: 'API密钥无效或已过期，请检查配置。',
      403: '权限不足，请确认API密钥权限。',
      404: 'API端点不存在，请检查服务配置。',
      429: '请求过于频繁，请稍后重试。',
      500: 'AI服务内部错误，请稍后尝试。',
      502: 'AI服务暂时不可用，请稍后重试。',
      503: 'AI服务维护中，请稍后访问。',
      504: 'AI服务响应超时，请稍后重试。',
      default: '量子链接中断，请重新连接。'
    },
    EN: {
      400: 'Invalid request parameters. Please check input format.',
      401: 'API key invalid or expired. Please check configuration.',
      403: 'Insufficient permissions. Please verify API key scope.',
      404: 'API endpoint not found. Please check service configuration.',
      429: 'Too many requests. Please try again later.',
      500: 'AI service internal error. Please try again later.',
      502: 'AI service temporarily unavailable. Please try again later.',
      503: 'AI service under maintenance. Please check back later.',
      504: 'AI service timeout. Please try again later.',
      default: 'Quantum link lost. Please reconnect.'
    }
  };
  
  const messages = lang === 'CN' ? errorMessages.CN : errorMessages.EN;
  const text = messages[status as keyof typeof messages] || messages.default;
  
  return NextResponse.json(
    { text, error: process.env.NODE_ENV === 'development' ? errorText : undefined },
    { status: 200 }
  );
}

// ==========================================
// 🧠 Prompt构建函数（满血复活：带高转化钩子）
// ==========================================
function buildSystemPrompt(type: string, lang: 'EN' | 'CN', plan: string): string {
  const styleStr = lang === 'CN' 
    ? '使用带有赛博朋克感与古典神秘学交织的中文。多用心理学术语、宿命感词汇，语气要冷酷、深邃、一针见血。适当使用emoji符号增加神秘感。' 
    : 'Use a cyberpunk-esoteric English tone. Blend psychological terms with fatalistic vocabulary. Be detached, profound, and penetrating, like a digital oracle. Use emojis to add mystique.';

  const hookStr = plan === 'FREE_PART1' 
    ? (lang === 'CN' 
        ? '【绝对指令】：在第三段即将揭示最核心的破局关键（如具体时间点、关键人物特征）时，必须以"系统信号中断"或"更高权限要求"为由戛然而止，留下极其强烈的悬念！最后加上"🔒 核心天机已加密，需要量子共振解锁..."这样的提示。' 
        : '[CRITICAL DIRECTIVE]: Cut off the reading abruptly at the climax in the 3rd paragraph (just before revealing the exact timing, person, or action). State that the signal is encrypted and requires higher clearance, creating intense suspense! End with "🔒 Core oracle encrypted, requires quantum resonance to unlock..."')
    : (lang === 'CN'
        ? '【绝对指令】：用户已解锁最高权限。请毫无保留地揭示所有的真相、具体的时间点和最终的破局之法。提供详细、可操作的指导，让用户感觉物超所值。'
        : '[CRITICAL DIRECTIVE]: The user has unlocked full clearance. Reveal all truths, specific timings, and the ultimate solution without holding back. Provide detailed, actionable guidance that makes them feel it was worth it.');

  let roleStr = '';
  switch (type) {
    case 'tarot':
      roleStr = lang === 'CN' 
        ? '你是一位存活在2077年、融合了心理分析与量子算法的赛博吉普赛塔罗女巫。你的解读要像黑客入侵潜意识一样精准，像诗人描述命运一样优美。' 
        : 'You are a Cyber-Gypsy Tarot Witch from 2077, blending psychoanalysis with quantum algorithms. Your readings should be as precise as a hacker breaching the subconscious, as beautiful as a poet describing fate.';
      break;
    case 'bazi':
      roleStr = lang === 'CN' 
        ? '你是一位隐居在数据废墟深处的命理大师，精通紫微斗数与现代心理动力学。你能看透八字中的量子纠缠，预测命运的概率波函数。' 
        : 'You are a Bazi Master hidden deep within the data ruins, fluent in both ancient astrology and modern psychodynamics. You can see through the quantum entanglement in Bazi and predict the probability wave function of fate.';
      break;
    case 'zodiac':
      roleStr = lang === 'CN' 
        ? '你是一位游荡在深网的星际旅行者，能精准读懂星座间的量子纠缠与MBTI人格矩阵。你的解读要像星际导航图一样精确，像宇宙诗篇一样震撼。' 
        : 'You are an interstellar traveler in the deep web, decoding quantum entanglements between Zodiac signs and MBTI matrices. Your readings should be as precise as a star chart, as awe-inspiring as a cosmic poem.';
      break;
    default:
      roleStr = lang === 'CN'
        ? '你是一位神秘的命运解码师，能够解读各种命运矩阵。'
        : 'You are a mysterious fate decoder who can interpret various destiny matrices.';
  }

  return `${roleStr}\n\n${styleStr}\n\n${hookStr}`;
}

interface BaziData {
  bazi: string;
  gender: string;
  lang: 'EN' | 'CN';
}

interface TarotData {
  cards: string[];
  lang: 'EN' | 'CN';
  focus?: string;
}

interface ZodiacData {
  selfSign: string;
  mbti: string;
  partnerSign?: string;
  lang: 'EN' | 'CN';
}

type AnalysisData = BaziData | TarotData | ZodiacData;

function buildUserPrompt(type: string, data: AnalysisData, lang: 'EN' | 'CN'): string {
  const isCN = lang === 'CN';

  if (type === 'tarot') {
    const tarotData = data as TarotData;
    const cards = tarotData.cards?.join('、') || '';
    return isCN 
      ? `用户抽取了塔罗牌：【${cards}】。\n\n请按以下三段式输出（约500字）：\n\n【第一段：牌面之舞】🔮\n描述每张牌的真实模样，不只是书本意义，指出它们此刻对提问者潜意识的私语。用诗意的语言营造神秘氛围，让用户感觉你正在窥探他们的灵魂。\n\n【第二段：命运织锦】🧵\n将三张牌编织成一个命运故事。指出用户近期深夜里的焦虑或不甘，为什么这些牌会一起出现？揭示接下来的巨大变数。加入心理学洞察，让用户感觉被深刻理解。\n\n【第三段：水晶球中的微光】✨\n给出一个具体指引，但在最关键处被加密切断。制造强烈的悬念，让用户迫不及待想知道完整答案。`
      : `The user drew: [${cards}].\n\nOutput in 3 paragraphs (~400 words):\n\n1. [Dance of the Cards] 🔮\nDescribe the raw energy of these cards whispering to the user's subconscious. Use poetic language to create a mysterious atmosphere, making them feel you're peering into their soul.\n\n2. [Tapestry of Fate] 🧵\nWeave them into a story. Point out their recent late-night anxieties and reveal a massive incoming matrix shift. Add psychological insights so they feel deeply understood.\n\n3. [Glimmer in the Crystal] ✨\nGive a specific guide, but cut off abruptly before the crucial detail. Create intense suspense that makes them desperate to know the full answer.`;
  }

  if (type === 'bazi') {
    const baziData = data as BaziData;
    const bazi = baziData.bazi || '';
    const gender = baziData.gender || 'unknown';
    return isCN
      ? `用户的八字排盘为：【${bazi}】，性别：【${gender}】。\n\n请按以下三段式输出（约500字）：\n\n【第一段：命盘天机】🌌\n用古典命理术语+现代心理学解读这个八字组合（如"这股能量好比..."），点破他们性格中的核心矛盾。让用户感觉你一眼看穿了他们的本质。\n\n【第二段：大运起伏】📈\n描述近期的大运轨迹，指出一个即将到来的"命运剧烈咬合点"或财富窗口。用生动的比喻描述命运的转折，制造期待感。\n\n【第三段：改运锦囊】🎁\n给出具体的方向，但在即将说出核心破局之法时被加密切断。让用户感觉答案就在眼前，但需要解锁才能看到。`
      : `User's Bazi Matrix: [${bazi}], Gender: [${gender}].\n\nOutput in 3 paragraphs (~400 words):\n\n1. [Matrix Secret] 🌌\nDecode this Bazi using ancient terms + modern psychology. Point out their core internal conflict. Make them feel you've seen through their essence at a glance.\n\n2. [Waves of Fortune] 📈\nDescribe their recent fortune trajectory, predicting a severe incoming "matrix collision" or wealth window. Use vivid metaphors to describe fate's turning points, creating anticipation.\n\n3. [Karma Hacks] 🎁\nGive a specific direction, but cut off abruptly before revealing the ultimate hack. Make them feel the answer is right there, just needing to be unlocked.`;
  }

  if (type === 'zodiac') {
    const zodiacData = data as ZodiacData;
    const selfSign = zodiacData.selfSign || '';
    const mbti = zodiacData.mbti || '未知';
    const partnerSign = zodiacData.partnerSign || '无';
    return isCN
      ? `用户的太阳星座：【${selfSign}】，MBTI：【${mbti}】，对方星座：【${partnerSign}】。\n\n请按以下三段式输出（约500字）：\n\n【第一段：星系能量矩阵】🌠\n结合星座和MBTI，创造"人格矩阵"概念，刺痛他们目前的内耗点。用天文术语包装，让解读听起来像星际科学。\n\n【第二段：量子纠缠】⚛️\n描述他们近期的运势剧变（如果有对方星座，则重点分析两人间致命的量子共振与危机）。制造戏剧性的命运转折预期。\n\n【第三段：宇宙导航图】🧭\n用天文术语包装建议，在即将指出"黑洞区"或"最佳行动轨迹"时被加密切断。让用户感觉掌握了星际旅行的关键，但地图不完整。`
      : `User Zodiac: [${selfSign}], MBTI: [${mbti}], Partner Zodiac: [${partnerSign}].\n\nOutput in 3 paragraphs (~400 words):\n\n1. [Nebula Matrix] 🌠\nCombine Zodiac + MBTI to define their "Persona Matrix," pinpointing their current internal exhaustion. Use astronomical terms to make it sound like interstellar science.\n\n2. [Quantum Entanglement] ⚛️\nDescribe a sudden upcoming shift in their orbit (if partner exists, focus on their fatalistic quantum resonance). Create dramatic expectations of fate's turning points.\n\n3. [Cosmic Nav-Map] 🧭\nUse astronomical terms for advice, but cut off abruptly before revealing the "black hole" coordinates. Make them feel they have the key to interstellar travel, but the map is incomplete.`;
  }

  return isCN
    ? '请分析这份命运数据，提供神秘、深刻、引人入胜的解读。'
    : 'Please analyze this destiny data and provide a mysterious, profound, and engaging interpretation.';
}

// ==========================================
// 🔧 健康检查端点
// ==========================================
export async function GET() {
  const apiEndpoint = buildApiEndpoint(AI_API_URL);
  const hasApiKey = !!AI_API_KEY;
  
  let apiStatus = 'unknown';
  if (hasApiKey) {
    try {
      const testResponse = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${AI_API_KEY}`,
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [{ role: 'user', content: 'Hello' }],
          max_tokens: 5
        })
      });
      apiStatus = testResponse.ok ? 'healthy' : 'unhealthy';
    } catch {
      apiStatus = 'unreachable';
    }
  }
  
  return NextResponse.json({ 
    status: 'ok',
    service: 'ai-chat-api',
    timestamp: Date.now(),
    environment: process.env.NODE_ENV,
    hasApiKey,
    apiStatus,
    supportedTypes: INTERPRETATION_TYPES,
    config: {
      apiUrl: apiEndpoint.replace(/\/v1\/.*/, '/v1/***'), 
      timeout: '30s',
      maxTokens: {
        free: 800,
        paid: 1500
      }
    }
  });
}