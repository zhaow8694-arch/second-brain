import { NextResponse } from 'next/server';
import { capturePayPalOrder } from '@/lib/paypal';
import { markOrderPaid } from '@/lib/orders';
import { createEntitlement } from '@/lib/entitlements';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { paypalOrderId, orderId } = body;

    if (!paypalOrderId || !orderId) {
      return NextResponse.json({ success: false, error: 'Missing paypalOrderId or orderId' }, { status: 400 });
    }

    // 1) Capture payment on PayPal side
    const capture = await capturePayPalOrder(paypalOrderId);

    if (capture.status !== 'COMPLETED') {
      return NextResponse.json({ success: false, error: `PayPal capture status: ${capture.status}` });
    }

    // 2) Mark our order as paid
    const paidOrder = await markOrderPaid(orderId, paypalOrderId, capture.captureId);
    if (!paidOrder) {
      return NextResponse.json({ success: false, error: 'Order not found' }, { status: 404 });
    }

    // 3) Create entitlement
    const entitlement = await createEntitlement(orderId);

    return NextResponse.json({
      success: true,
      captureId: capture.captureId,
      payerEmail: capture.payerEmail,
      payerName: capture.payerName,
      grossAmount: capture.grossAmount,
      currency: capture.currencyCode,
      entitlement: entitlement
        ? { id: entitlement.entitlementId, plan: entitlement.planId, maxUsage: entitlement.maxUsage }
        : null,
    });
  } catch (error) {
    console.error('[PayPal Capture Error]:', error);
    const message = error instanceof Error ? error.message : 'Internal error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}
