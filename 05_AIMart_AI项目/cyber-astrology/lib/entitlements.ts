// =========================================
// Entitlement model — what a paid order grants
// =========================================

import { redis } from './redis';

// ── Types ───────────────────────────────────

export interface ReportEntitlement {
  entitlementId: string;
  orderId: string;
  planId: 'LITE' | 'ELITE';
  createdAt: number;
  expiresAt: number | null;      // null = lifetime access
  usageCount: number;
  maxUsage: number;              // -1 = unlimited
}

// ── Redis key helpers ────────────────────────

function entitlementKey(orderId: string): string {
  return `entitlement:${orderId}`;
}

function usedTxKey(txHash: string): string {
  return `tx:used:${txHash}`;
}

// ── Create entitlement after payment ─────────

export async function createEntitlement(orderId: string): Promise<ReportEntitlement | null> {
  const raw = await redis.get(`order:${orderId}`);
  if (!raw) return null;

  const order = typeof raw === 'string' ? JSON.parse(raw) : raw;
  if (order.status !== 'paid') return null;

  const planId = order.planId as 'LITE' | 'ELITE';
  const maxUsage = planId === 'ELITE' ? -1 : 1;       // LITE = 1 use, ELITE = unlimited
  const expiresAt = planId === 'ELITE'
    ? Date.now() + 365 * 24 * 60 * 60 * 1000           // 1 year
    : Date.now() + 30 * 24 * 60 * 60 * 1000;            // 30 days

  const entitlement: ReportEntitlement = {
    entitlementId: `ENT-${orderId}`,
    orderId,
    planId,
    createdAt: Date.now(),
    expiresAt,
    usageCount: 0,
    maxUsage,
  };

  await redis.set(entitlementKey(orderId), JSON.stringify(entitlement), { ex: 60 * 60 * 24 * 365 });
  return entitlement;
}

// ── Check & use entitlement ──────────────────

export async function checkEntitlement(orderId: string): Promise<{
  allowed: boolean;
  entitlement: ReportEntitlement | null;
}> {
  const raw = await redis.get(entitlementKey(orderId));
  if (!raw) return { allowed: false, entitlement: null };

  const entitlement = typeof raw === 'string' ? JSON.parse(raw) : raw as ReportEntitlement;

  // Check expiry
  if (entitlement.expiresAt && Date.now() > entitlement.expiresAt) {
    return { allowed: false, entitlement };
  }

  // Check usage limit
  if (entitlement.maxUsage !== -1 && entitlement.usageCount >= entitlement.maxUsage) {
    return { allowed: false, entitlement };
  }

  return { allowed: true, entitlement };
}

// ── Consume one usage ────────────────────────

export async function consumeEntitlement(orderId: string): Promise<boolean> {
  const raw = await redis.get(entitlementKey(orderId));
  if (!raw) return false;

  const entitlement = typeof raw === 'string' ? JSON.parse(raw) : raw as ReportEntitlement;

  if (entitlement.maxUsage !== -1 && entitlement.usageCount >= entitlement.maxUsage) {
    return false;
  }

  entitlement.usageCount += 1;
  await redis.set(entitlementKey(orderId), JSON.stringify(entitlement), { ex: 60 * 60 * 24 * 365 });
  return true;
}

// ── TRC20 tx dedup — prevent replay ──────────

export async function markTxUsed(txHash: string): Promise<boolean> {
  const key = usedTxKey(txHash);
  const existed = await redis.setnx(key, '1');
  if (existed) {
    await redis.expire(key, 60 * 60 * 24 * 30); // 30 days
    return true;  // first time seeing this tx
  }
  return false;  // already used
}

export async function isTxUsed(txHash: string): Promise<boolean> {
  const key = usedTxKey(txHash);
  const exists = await redis.get(key);
  return exists !== null;
}
