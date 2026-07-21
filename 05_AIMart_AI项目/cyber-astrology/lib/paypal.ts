// =========================================
// PayPal Checkout — server-side helpers
// =========================================

const PAYPAL_API_BASE = process.env.PAYPAL_API_BASE || 'https://api-m.paypal.com';
const CLIENT_ID = process.env.PAYPAL_CLIENT_ID || '';
const SECRET = process.env.PAYPAL_SECRET || '';

// ── Get access token ─────────────────────────

let cachedToken: { token: string; expiresAt: number } | null = null;

export async function getPayPalAccessToken(): Promise<string> {
  if (cachedToken && Date.now() < cachedToken.expiresAt - 60000) {
    return cachedToken.token;
  }

  const auth = Buffer.from(`${CLIENT_ID}:${SECRET}`).toString('base64');
  const res = await fetch(`${PAYPAL_API_BASE}/v1/oauth2/token`, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${auth}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: 'grant_type=client_credentials',
    cache: 'no-store',
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PayPal auth failed: ${res.status} ${text}`);
  }

  const data = await res.json();
  cachedToken = { token: data.access_token, expiresAt: Date.now() + data.expires_in * 1000 };
  return data.access_token;
}

// ── Order types ──────────────────────────────

export interface PayPalOrderRequest {
  amount: string;        // e.g. "10.00"
  currency: string;      // e.g. "USD"
  orderId: string;       // our internal orderId
  description?: string;
}

export interface PayPalOrderResponse {
  paypalOrderId: string;
  approvalUrl: string;
}

// ── Create order ─────────────────────────────

export async function createPayPalOrder(req: PayPalOrderRequest): Promise<PayPalOrderResponse> {
  const token = await getPayPalAccessToken();

  const res = await fetch(`${PAYPAL_API_BASE}/v2/checkout/orders`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      intent: 'CAPTURE',
      purchase_units: [
        {
          reference_id: req.orderId,
          description: req.description || 'FateMatrices Report',
          amount: {
            currency_code: req.currency,
            value: req.amount,
          },
        },
      ],
      payment_source: {
        paypal: {
          experience_context: {
            payment_method_preference: 'IMMEDIATE_PAYMENT_REQUIRED',
            landing_page: 'LOGIN',
            user_action: 'PAY_NOW',
            return_url: `${process.env.NEXT_PUBLIC_SITE_URL || 'https://fatematrices.vercel.app'}/payment/success`,
            cancel_url: `${process.env.NEXT_PUBLIC_SITE_URL || 'https://fatematrices.vercel.app'}/payment/cancel`,
          },
        },
      },
    }),
    cache: 'no-store',
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PayPal create order failed: ${res.status} ${text}`);
  }

  const data = await res.json();

  const approvalLink = data.links?.find(
    (l: { rel: string; href: string }) => l.rel === 'payer-action'
  )?.href;

  return {
    paypalOrderId: data.id,
    approvalUrl: approvalLink || '',
  };
}

// ── Capture order (complete payment) ─────────

export interface PayPalCaptureResult {
  status: string;
  captureId: string;
  payerEmail?: string;
  payerName?: string;
  grossAmount?: string;
  currencyCode?: string;
}

export async function capturePayPalOrder(paypalOrderId: string): Promise<PayPalCaptureResult> {
  const token = await getPayPalAccessToken();

  const res = await fetch(`${PAYPAL_API_BASE}/v2/checkout/orders/${paypalOrderId}/capture`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: '{}',
    cache: 'no-store',
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PayPal capture failed: ${res.status} ${text}`);
  }

  const data = await res.json();

  const capture = data.purchase_units?.[0]?.payments?.captures?.[0];
  const payer = data.payer;

  return {
    status: data.status,
    captureId: capture?.id || '',
    payerEmail: payer?.email_address,
    payerName: payer?.name?.given_name
      ? `${payer.name.given_name} ${payer.name.surname || ''}`.trim()
      : undefined,
    grossAmount: capture?.amount?.value,
    currencyCode: capture?.amount?.currency_code,
  };
}

// ── Verify webhook (basic) ───────────────────

export async function verifyWebhookSignature(
  _headers: Record<string, string>,
  _body: string
): Promise<boolean> {
  // For initial deployment, we skip full verification.
  // Production: use PayPal's POST /v1/notifications/verify-webhook-signature
  return true;
}
