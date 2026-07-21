import { NextResponse } from 'next/server';
import { redis } from '@/lib/redis';
import {
  createPayoneerPayment,
  verifyPayoneerPayment,
  PRICING,
  type PlanId,
} from '@/lib/payment';

const RATE_LIMIT_MAX = 10;
const RATE_LIMIT_WINDOW = 60;

async function checkRateLimit(ip: string): Promise<boolean> {
  const key = `rate_limit:payoneer:${ip}`;
  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, RATE_LIMIT_WINDOW);
  return count <= RATE_LIMIT_MAX;
}

// ==========================================
// POST /api/payoneer-payment
// 创建 Payoneer 电汇支付订单
// ==========================================

export async function POST(req: Request) {
  try {
    const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
    if (!(await checkRateLimit(ip))) {
      return NextResponse.json({ success: false, error: 'Rate limit exceeded' }, { status: 429 });
    }

    const body = await req.json();
    const { action, planId, customerEmail, customerName } = body;

    // 创建支付订单
    if (action === 'create') {
      if (!planId || !PRICING[planId as PlanId]) {
        return NextResponse.json({ success: false, error: 'Invalid plan' }, { status: 400 });
      }

      const plan = PRICING[planId as PlanId];

      const result = await createPayoneerPayment({
        planId: planId as PlanId,
        amount: plan.priceUSD,
        currency: 'USD',
        customerEmail,
        customerName,
      });

      if (!result.success || !result.paymentId) {
        return NextResponse.json({ success: false, error: 'Failed to create payment' }, { status: 500 });
      }

      // 存储支付订单到 Redis
      await redis.set(
        `payoneer_order:${result.paymentId}`,
        JSON.stringify({
          planId: plan.id,
          amount: plan.priceUSD,
          status: 'pending',
          createdAt: Date.now(),
        }),
        { ex: 86400 }
      );

      return NextResponse.json({
        success: true,
        paymentId: result.paymentId,
        instructions: result.instructions,
      });
    }

    // 验证支付状态
    if (action === 'verify') {
      const { paymentId } = body;
      if (!paymentId) {
        return NextResponse.json({ success: false, error: 'Missing paymentId' }, { status: 400 });
      }

      const result = await verifyPayoneerPayment(paymentId);

      if (result.verified) {
        await redis.set(
          `payoneer_order:${paymentId}`,
          JSON.stringify({ status: 'completed', completedAt: Date.now() }),
          { ex: 86400 }
        );
      }

      return NextResponse.json({ success: true, ...result });
    }

    return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 });
  } catch (error) {
    console.error('[Payoneer Payment Error]:', error);
    return NextResponse.json({ success: false, error: 'Internal error' }, { status: 500 });
  }
}

// ==========================================
// GET /api/payoneer-payment
// 健康检查
// ==========================================

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'payoneer-payment',
    timestamp: Date.now(),
  });
}
