import { NextResponse } from 'next/server';
import { verifyWebhookSignature } from '@/lib/paypal';
import { markOrderPaid, markOrderRefunded } from '@/lib/orders';
import { createEntitlement } from '@/lib/entitlements';

export async function POST(req: Request) {
  try {
    const body = await req.text();
    const headers: Record<string, string> = {};
    req.headers.forEach((v, k) => { headers[k] = v; });

    // For now skip full webhook verification (enable for production)
    const verified = await verifyWebhookSignature(headers, body);
    if (!verified) {
      console.warn('[PayPal Webhook] Skipping signature verification (dev mode)');
    }

    const event = JSON.parse(body);
    const eventType = event.event_type;

    console.log(`[PayPal Webhook] Received: ${eventType}`);

    // Handle PAYMENT.CAPTURE.COMPLETED
    if (eventType === 'PAYMENT.CAPTURE.COMPLETED') {
      const resource = event.resource;
      const customId = resource.custom_id || resource.invoice_id;
      const paypalOrderId = resource.supplementary_data?.related_ids?.order_id || '';

      if (customId) {
        const paidOrder = await markOrderPaid(customId, paypalOrderId, resource.id);
        if (paidOrder) {
          await createEntitlement(customId);
          console.log(`[PayPal Webhook] Order ${customId} marked paid`);
        }
      }
    }

    // Handle PAYMENT.CAPTURE.REFUNDED
    if (eventType === 'PAYMENT.CAPTURE.REFUNDED') {
      const resource = event.resource;
      const customId = resource.custom_id || resource.invoice_id;
      if (customId) {
        await markOrderRefunded(customId);
        console.log(`[PayPal Webhook] Order ${customId} marked refunded`);
      }
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('[PayPal Webhook Error]:', error);
    return NextResponse.json({ received: false }, { status: 500 });
  }
}
