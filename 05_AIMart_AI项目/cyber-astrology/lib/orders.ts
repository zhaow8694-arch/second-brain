// =========================================
// Order model & Redis operations
// Server is the ONLY source of truth for orders
// =========================================

import { redis } from './redis';

// ── Types ───────────────────────────────────

export type PaymentProvider = 'paypal' | 'trc20';
export type OrderStatus = 'pending' | 'paid' | 'failed' | 'refunded' | 'expired';
export type PlanId = 'LITE' | 'ELITE';

export interface PaymentOrder {
  orderId: string;
  provider: PaymentProvider;
  planId: PlanId;
  amount: number;
  currency: 'USD' | 'USDT';
  status: OrderStatus;
  createdAt: number;
  expiresAt: number;       // orders expire after 30 min
  policyVersion: string;
  policyAcceptedAt: number;
  policyAcceptedIp: string;
  policyAcceptedUserAgent: string;
  providerOrderId?: string;  // PayPal order ID / TRC20 txHash
  providerCaptureId?: string; // PayPal capture ID
  paidAt?: number;
  refundedAt?: number;
  metadata?: Record<string, unknown>; // extra data (e.g. artifact: true)
}

// ── Redis key helpers ────────────────────────

function orderKey(orderId: string): string {
  return `order:${orderId}`;
}

function entitlementByOrderKey(orderId: string): string {
  return `entitlement:by-order:${orderId}`;
}

// ── Create order (server-side only) ──────────

export async function createOrder(params: {
  provider: PaymentProvider;
  planId: PlanId;
  amount: number;
  currency: 'USD' | 'USDT';
  policyVersion: string;
  policyAcceptedAt: number;
  policyAcceptedIp: string;
  policyAcceptedUserAgent: string;
  merchantAddress?: string;   // TRC20 only: server-owned address
  referenceCode?: string;    // TRC20 only: unique code for user to include in memo
  metadata?: Record<string, unknown>; // extra data (e.g. artifact: true)
}): Promise<PaymentOrder> {
  const orderId = `ORD-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const now = Date.now();
  const expiresAt = now + 30 * 60 * 1000; // 30 min

  const order: PaymentOrder = {
    orderId,
    provider: params.provider,
    planId: params.planId,
    amount: params.amount,
    currency: params.currency,
    status: 'pending',
    createdAt: now,
    expiresAt,
    policyVersion: params.policyVersion,
    policyAcceptedAt: params.policyAcceptedAt,
    policyAcceptedIp: params.policyAcceptedIp,
    policyAcceptedUserAgent: params.policyAcceptedUserAgent,
    metadata: params.metadata,
  };

  await redis.set(orderKey(orderId), JSON.stringify(order), { ex: 60 * 60 * 24 * 7 }); // 7 days TTL
  return order;
}

// ── Get order ───────────────────────────────

export async function getOrder(orderId: string): Promise<PaymentOrder | null> {
  const raw = await redis.get(orderKey(orderId));
  if (!raw) return null;
  return typeof raw === 'string' ? JSON.parse(raw) : raw as unknown as PaymentOrder;
}

// ── Mark order as paid ─────────────────────

export async function markOrderPaid(
  orderId: string,
  providerOrderId: string,
  providerCaptureId?: string
): Promise<PaymentOrder | null> {
  const order = await getOrder(orderId);
  if (!order) return null;

  order.status = 'paid';
  order.paidAt = Date.now();
  order.providerOrderId = providerOrderId;
  if (providerCaptureId) order.providerCaptureId = providerCaptureId;

  await redis.set(orderKey(orderId), JSON.stringify(order), { ex: 60 * 60 * 24 * 30 }); // 30 days for paid
  return order;
}

// ── Mark order as failed ────────────────────

export async function markOrderFailed(orderId: string): Promise<void> {
  const order = await getOrder(orderId);
  if (!order) return;
  order.status = 'failed';
  await redis.set(orderKey(orderId), JSON.stringify(order), { ex: 60 * 60 * 24 * 7 });
}

// ── Mark order as refunded ──────────────────

export async function markOrderRefunded(orderId: string): Promise<void> {
  const order = await getOrder(orderId);
  if (!order) return;
  order.status = 'refunded';
  order.refundedAt = Date.now();
  await redis.set(orderKey(orderId), JSON.stringify(order), { ex: 60 * 60 * 24 * 30 });
}

// ── Check if order is paid ──────────────────

export async function isOrderPaid(orderId: string): Promise<boolean> {
  const order = await getOrder(orderId);
  return order?.status === 'paid';
}
