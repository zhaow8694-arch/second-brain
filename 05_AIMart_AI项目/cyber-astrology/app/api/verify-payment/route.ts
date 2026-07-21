import { NextResponse } from 'next/server';
import { redis } from '@/lib/redis';
import { createOrder, markOrderPaid } from '@/lib/orders';
import { createEntitlement, markTxUsed } from '@/lib/entitlements';

const TRONGRID_API_KEY = process.env.TRONGRID_API_KEY;
const USDT_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t';
const MAX_TRANSACTION_AGE = 60 * 60 * 1000;  // 1 hour
const RATE_LIMIT_MAX = 10;
const RATE_LIMIT_WINDOW = 60;

// ══════════════════════════════════════════
// Helpers
// ══════════════════════════════════════════

function isValidTRC20Address(addr: string): boolean {
  return /^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(addr);
}

function isValidAmount(v: string): boolean {
  const n = parseFloat(v);
  return !isNaN(n) && n > 0 && n <= 1000000;
}

function decodeMemo(hexData: string): string {
  try {
    if (!hexData || hexData === '0x') return '';
    const hex = hexData.replace(/^0x/, '');
    let str = '';
    for (let i = 0; i < hex.length; i += 2) {
      const cc = parseInt(hex.substring(i, i + 2), 16);
      if (cc > 31 && cc < 127) str += String.fromCharCode(cc);
    }
    return str;
  } catch {
    return '';
  }
}

async function checkRateLimit(ip: string): Promise<boolean> {
  const key = `rate_limit:payment:${ip}`;
  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, RATE_LIMIT_WINDOW);
  return count <= RATE_LIMIT_MAX;
}

const PLAN_CONFIG: Record<string, { amount: number; planId: 'LITE' | 'ELITE' }> = {
  LITE:  { amount: 10,   planId: 'LITE' },
  ELITE: { amount: 29.9, planId: 'ELITE' },
};

// ══════════════════════════════════════════
// POST
// ══════════════════════════════════════════

export async function POST(req: Request) {
  try {
    const ip = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
    if (!(await checkRateLimit(ip))) {
      return NextResponse.json({ success: false, error: 'Rate limit exceeded' }, { status: 429 });
    }

    const body = await req.json();
    const { action, planId, address, amount, walletTail, orderId } = body;

    // ── action: create ────────────────────────
    // Server-side creates a PaymentOrder + a unique referenceCode
    if (action === 'create') {
      // Support both standard plans (PLAN_CONFIG) and artifacts (custom amount)
      const plan = PLAN_CONFIG[planId as string];
      const customAmount = body.amount ? parseFloat(body.amount) : null;
      const isArtifact = body.artifact === true;

      // Must have either a valid plan or a custom amount (for artifacts)
      if (!plan && !customAmount) {
        return NextResponse.json({ success: false, error: 'Invalid plan or missing amount' }, { status: 400 });
      }
      if (customAmount && (isNaN(customAmount) || customAmount <= 0 || customAmount > 1000000)) {
        return NextResponse.json({ success: false, error: 'Invalid amount' }, { status: 400 });
      }

      const resolvedPlanId = plan ? plan.planId : 'ELITE';
      const resolvedAmount = customAmount || plan!.amount;

      // Generate the TRC20 receive address from env (or use the default one)
      // This should be a server-owned address
      const merchantAddr = process.env.TRC20_ADDR || '';
      if (!merchantAddr || !isValidTRC20Address(merchantAddr)) {
        return NextResponse.json({ success: false, error: 'Merchant address not configured' }, { status: 500 });
      }

      const referenceCode = `FM${Date.now().toString(36).toUpperCase()}${Math.random().toString(36).slice(2, 6).toUpperCase()}`;

      const order = await createOrder({
        provider: 'trc20',
        planId: resolvedPlanId,
        amount: resolvedAmount,
        currency: 'USDT',
        policyVersion: '1.0',
        policyAcceptedAt: Date.now(),
        policyAcceptedIp: ip,
        policyAcceptedUserAgent: req.headers.get('user-agent') || '',
        merchantAddress: merchantAddr,
        referenceCode,
        metadata: isArtifact ? { artifact: true } : undefined,
      });

      return NextResponse.json({
        success: true,
        orderId: order.orderId,
        referenceCode,
        address: merchantAddr,
        amount: resolvedAmount,
        artifact: isArtifact || undefined,
      });
    }

    // ── action: verify ────────────────────────
    // Validate the TRC20 transaction on-chain, then mark paid + create entitlement
    if (!orderId || !address || !amount || !walletTail) {
      return NextResponse.json({ success: false, error: 'Missing parameters' }, { status: 400 });
    }

    if (!isValidTRC20Address(address) || !isValidAmount(amount) || !/^[0-9A-Za-z]{4}$/.test(walletTail.trim())) {
      return NextResponse.json({ success: false, error: 'Invalid parameters' }, { status: 400 });
    }

    // Check order exists and is pending
    const orderData = await redis.get(`order:${orderId}`);
    if (!orderData) {
      return NextResponse.json({ success: false, error: 'Order not found or expired' }, { status: 400 });
    }
    const order = typeof orderData === 'string' ? JSON.parse(orderData) : orderData;
    if (order.status !== 'pending') {
      return NextResponse.json({ success: false, error: 'Order already processed' }, { status: 400 });
    }

    const cleanTail = walletTail.trim().toLowerCase();
    const requiredAmount = parseFloat(amount);
    const minAmount = requiredAmount * 0.95; // allow 5% slippage

    // Fetch TRC20 transactions from TronGrid
    const headers: Record<string, string> = { 'Accept': 'application/json' };
    if (TRONGRID_API_KEY) headers['TRON-PRO-API-KEY'] = TRONGRID_API_KEY;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    let found = false;
    let matchingTx: { from: string; amount: number; hash: string } | null = null;

    try {
      const response = await fetch(
        `https://api.trongrid.io/v1/accounts/${address}/transactions/trc20?limit=50&token_address=${USDT_CONTRACT}`,
        { headers, cache: 'no-store', signal: controller.signal }
      );
      clearTimeout(timeoutId);

      if (!response.ok) {
        return NextResponse.json({ success: false, error: `Blockchain API error: ${response.status}` }, { status: 502 });
      }

      const data = await response.json();
      if (!data?.data || !Array.isArray(data.data)) {
        return NextResponse.json({ success: false, error: 'Invalid blockchain response' }, { status: 502 });
      }

      const now = Date.now();

      for (const tx of data.data) {
        if (!tx.to || !tx.from || !tx.value || !tx.block_timestamp) continue;

        // Filter: within time window, sent to our address
        if (now - parseInt(tx.block_timestamp) > MAX_TRANSACTION_AGE) continue;
        if (tx.to.toLowerCase() !== address.toLowerCase()) continue;

        // Filter: sender's wallet tail matches
        const fromAddr = tx.from.toLowerCase();
        if (!fromAddr.endsWith(cleanTail)) continue;

        // Filter: amount >= minimum
        const txAmount = parseInt(tx.value) / 1000000;
        if (txAmount < minAmount) continue;

        // Filter: memo must contain orderId (the referenceCode)
        const memo = decodeMemo(tx.data || '');
        if (!memo.includes(orderId)) continue;

        // Replay protection: check if this txHash was already used
        const txHash = tx.transaction_id;
        if (!txHash) continue;
        const fresh = await markTxUsed(txHash);
        if (!fresh) continue; // already redeemed

        found = true;
        matchingTx = { from: tx.from, amount: txAmount, hash: txHash };
        break;
      }

      if (!found || !matchingTx) {
        return NextResponse.json({ success: false, found: false, message: 'No matching transaction found' });
      }

      // ── Mark order paid + create entitlement ──
      await markOrderPaid(orderId, matchingTx.hash);
      const entitlement = await createEntitlement(orderId);

      return NextResponse.json({
        success: true,
        found: true,
        transaction: matchingTx,
        entitlement: entitlement
          ? { id: entitlement.entitlementId, plan: entitlement.planId, maxUsage: entitlement.maxUsage }
          : null,
      });

    } catch (fetchError: unknown) {
      clearTimeout(timeoutId);
      if (fetchError instanceof Error && fetchError.name === 'AbortError') {
        return NextResponse.json({ success: false, error: 'Blockchain query timeout' }, { status: 504 });
      }
      throw fetchError;
    }
  } catch (error) {
    console.error('[Payment Error]:', error);
    return NextResponse.json({ success: false, error: 'Internal error' }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({ status: 'ok', service: 'payment-verification', timestamp: Date.now() });
}
