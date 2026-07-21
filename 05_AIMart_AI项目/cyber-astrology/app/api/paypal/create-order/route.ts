import { NextResponse } from 'next/server';
import { createOrder } from '@/lib/orders';
import { createPayPalOrder } from '@/lib/paypal';
import { PRICING } from '@/lib/payment';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { planId } = body;

    if (!planId || !PRICING[planId as keyof typeof PRICING]) {
      return NextResponse.json({ success: false, error: 'Invalid plan' }, { status: 400 });
    }

    const plan = PRICING[planId as keyof typeof PRICING];
    const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';

    // 1) Create our internal order
    const order = await createOrder({
      provider: 'paypal',
      planId: plan.id,
      amount: plan.priceUSD,
      currency: 'USD',
      policyVersion: '1.0',
      policyAcceptedAt: Date.now(),
      policyAcceptedIp: ip,
      policyAcceptedUserAgent: req.headers.get('user-agent') || '',
    });

    // 2) Create PayPal order
    const paypalOrder = await createPayPalOrder({
      amount: plan.priceUSD.toFixed(2),
      currency: 'USD',
      orderId: order.orderId,
      description: `FateMatrices ${plan.id} Report`,
    });

    return NextResponse.json({
      success: true,
      orderId: order.orderId,
      paypalOrderId: paypalOrder.paypalOrderId,
      approvalUrl: paypalOrder.approvalUrl,
    });
  } catch (error) {
    console.error('[PayPal Create Order Error]:', error);
    const message = error instanceof Error ? error.message : 'Internal error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}
