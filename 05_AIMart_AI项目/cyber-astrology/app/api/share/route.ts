import { NextResponse } from 'next/server';
import { redis } from '@/lib/redis';

// ==========================================
// 🔗 分享追踪逻辑 (使用 Redis 跨设备同步)
// ==========================================

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { id } = body;

    if (!id) {
      return NextResponse.json({ success: false, error: 'Missing ID' }, { status: 400 });
    }

    // 1. 初始化分享追踪记录，有效期 1 小时
    await redis.set(`share:${id}`, JSON.stringify({ clicked: false, createdAt: Date.now() }), { ex: 3600 });
    
    return NextResponse.json({ success: true, id });
  } catch (error) {
    console.error('[Share Track Error]:', error);
    return NextResponse.json({ success: false, error: 'Internal error' }, { status: 500 });
  }
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    const action = searchParams.get('action'); // 'click' | 'check'

    if (!id) {
      return NextResponse.json({ success: false, error: 'Missing ID' }, { status: 400 });
    }

    const key = `share:${id}`;
    const dataStr = await redis.get(key);
    
    if (!dataStr) {
      return NextResponse.json({ success: false, clicked: false, expired: true });
    }

    // 处理数据格式 (Upstash 可能返回 string 或 object)
    const data = typeof dataStr === 'string' ? JSON.parse(dataStr) : dataStr;

    // 2. 模拟好友点击行为
    if (action === 'click') {
      await redis.set(key, JSON.stringify({ ...data, clicked: true }), { ex: 3600 });
      return NextResponse.json({ success: true, clicked: true });
    }

    // 3. 前端轮询检查
    return NextResponse.json({ 
      success: true, 
      clicked: data.clicked || false 
    });

  } catch (error) {
    console.error('[Share Check Error]:', error);
    return NextResponse.json({ success: false, error: 'Internal error' }, { status: 500 });
  }
}
