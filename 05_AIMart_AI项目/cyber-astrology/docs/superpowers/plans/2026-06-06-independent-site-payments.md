# Independent Site Payments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reliable payment and entitlement flow for FateMatrices independent-site purchases, starting with PayPal Checkout and USDT TRC20, while keeping Payoneer Checkout as a parallel application path.

**Architecture:** The server is the only source of truth for orders, payment status, refund-policy acceptance, and report entitlement. Client pages can request payment creation and display checkout UI, but `/api/chat` must unlock paid content only after reading a verified paid order from Redis or a later database.

**Tech Stack:** Next.js App Router 16, React 19, TypeScript, Upstash Redis, PayPal Checkout REST API, TronGrid TRC20 verification, Vercel environment variables.

---

## 1. Current Decision

The Payoneer receiving account shown in the dashboard is not suitable for direct FateMatrices website checkout.

Reasons:
- It is a Payoneer USD receiving account for business/platform transfers.
- The Payoneer guide says personal bank-account payments will be rejected.
- The supported platform list is for marketplace/e-commerce platform payouts, not ordinary website buyers.
- It does not provide card checkout, hosted payment page, payment capture API, or automatic webhook unlocks for independent-site customers.

Recommended payment stack:
- Primary near-term method: PayPal Checkout.
- Backup near-term method: USDT TRC20.
- Long-term method to apply for: Payoneer Checkout.
- Not recommended for website checkout: Payoneer receiving account / Citibank ACH or SWIFT details.

## 2. Business Positioning

Use this business description consistently when applying for processors:

```text
FateMatrices sells AI-generated astrology, tarot, and personality entertainment reports.
Reports are delivered digitally after payment. The service is for entertainment and personal insight only.
It does not provide financial, legal, medical, investment, or guaranteed life-decision advice.
```

Avoid these descriptions:
- Guaranteed fortune prediction.
- Wealth prediction service.
- Investment or financial decision guidance.
- Medical, legal, or psychological diagnosis.
- Gambling or betting-related wording.

## 3. Refund Policy Position

Use a clear no-refund digital-content policy, with required exceptions.

Recommended customer-facing wording:

```text
This service provides AI-generated personalized astrology, tarot, zodiac, and personality entertainment reports.
Reports are generated and delivered digitally after payment.

By paying, you confirm that you understand this service is for entertainment and personal insight only.
It is not financial, legal, medical, investment, or life-decision advice, and it does not guarantee real-world outcomes.

Once a report has started generating or has been delivered, all sales are final.
Refunds are not provided for dissatisfaction, changed mind, or disagreement with the interpretation.
Exceptions may apply for duplicate charges, failed delivery, technical issues we cannot reasonably fix, unauthorized transactions, or requirements under applicable law or payment-network rules.
```

Required checkout checkbox:

```text
I have read and agree to the Terms of Service and Refund Policy.
I understand that my personalized digital report will begin generating after payment and is non-refundable once generated or delivered, except where required by law or for payment/technical errors.
```

Store this evidence for every order:
- `policyVersion`
- `policyAcceptedAt`
- `policyAcceptedIp`
- `policyAcceptedUserAgent`
- `orderId`
- `planId`
- `amount`
- `currency`
- `provider`
- `reportGenerationStartedAt`
- `reportDeliveredAt`

## 4. Phase Plan

### Phase 0: Do Not Use Payoneer Receiving Account for Website Buyers

Outcome: Remove or hide Payoneer bank-transfer checkout from the public payment modal unless it is explicitly marked as manual/admin-only.

Acceptance criteria:
- Public customers are not instructed to wire money to the Citibank receiving account.
- Existing Payoneer receiving details are treated only as platform payout details.
- Website copy does not imply instant Payoneer bank-transfer unlock.

### Phase 1: Add Legal and Trust Pages

Files:
- Create: `app/terms/page.tsx`
- Create: `app/privacy/page.tsx`
- Create: `app/refund/page.tsx`
- Create: `app/contact/page.tsx`
- Create: `app/disclaimer/page.tsx`
- Modify: `app/layout.tsx`
- Modify: `app/page.tsx`

Content requirements:
- Terms must describe digital entertainment reports and user responsibilities.
- Refund page must include the non-refundable digital-content policy above.
- Disclaimer must say reports are entertainment only and not professional advice.
- Contact page must include a support email or contact method.
- Footer or payment modal must link to Terms and Refund Policy before payment.

Verification:
- Run `npm run lint`.
- Run `npm run build`.
- Visit `/terms`, `/privacy`, `/refund`, `/contact`, and `/disclaimer`.
- Confirm no page claims guaranteed prediction results.

### Phase 2: Introduce Server-Side Order and Entitlement Model

Files:
- Create: `lib/orders.ts`
- Create: `lib/entitlements.ts`
- Modify: `lib/payment.ts`
- Modify: `app/api/chat/route.ts`

Order fields:

```ts
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
  expiresAt: number;
  policyVersion: string;
  policyAcceptedAt: number;
  policyAcceptedIp: string;
  policyAcceptedUserAgent: string;
  providerOrderId?: string;
  providerCaptureId?: string;
  paidAt?: number;
  refundedAt?: number;
}
```

Entitlement fields:

```ts
export interface ReportEntitlement {
  entitlementId: string;
  orderId: string;
  planId: PlanId;
  reportType: 'bazi' | 'tarot' | 'zodiac';
  status: 'active' | 'revoked';
  createdAt: number;
  revokedAt?: number;
}
```

Rules:
- The client never decides paid status.
- The client never decides paid amount.
- `/api/chat` must reject paid/full plans unless a paid entitlement exists.
- Free teaser requests may continue without entitlement, but should still be rate limited.

Verification:
- Unit-test order creation, paid update, entitlement creation, and entitlement lookup.
- Manually call `/api/chat` with `plan: "ELITE"` but no paid order; expected: no paid unlock.
- Manually call `/api/chat` with a paid entitlement; expected: paid unlock allowed.

### Phase 3: Add PayPal Checkout

Files:
- Create: `app/api/paypal/create-order/route.ts`
- Create: `app/api/paypal/capture-order/route.ts`
- Create: `app/api/paypal/webhook/route.ts`
- Create: `lib/paypal.ts`
- Modify: `app/components/PayModal.tsx`
- Modify: `app/bazi/page.tsx`
- Modify: `app/tarot/page.tsx`
- Modify: `app/zodiac/page.tsx`

Environment variables:

```text
PAYPAL_ENV=sandbox
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_WEBHOOK_ID=...
NEXT_PUBLIC_PAYPAL_CLIENT_ID=...
```

Create-order flow:
- Validate `planId`.
- Validate refund-policy checkbox was accepted.
- Create internal order in Redis.
- Create PayPal order for the server-defined amount and currency.
- Save PayPal order id on the internal order.
- Return PayPal order id to the client.

Capture flow:
- Receive PayPal order id and internal order id.
- Call PayPal capture API server-side.
- Confirm status is completed.
- Confirm amount and currency match the internal order.
- Mark internal order as paid.
- Create entitlement for the selected report type and plan.
- Return unlock success to the client.

Webhook flow:
- Verify webhook signature.
- Handle completed capture by marking paid if not already paid.
- Handle denied or refunded events by marking failed/refunded and revoking entitlement.
- Make webhook handling idempotent.

Verification:
- Use PayPal Sandbox buyer and seller accounts.
- Complete a `$10` LITE payment.
- Complete a `$29.90` ELITE payment.
- Confirm paid orders exist in Redis.
- Confirm `/api/chat` only unlocks full report after payment.
- Confirm replaying the same webhook does not duplicate entitlement.

### Phase 4: Harden USDT TRC20 Backup

Files:
- Modify: `app/api/verify-payment/route.ts`
- Modify: `app/components/PayModal.tsx`
- Modify: `app/bazi/page.tsx`
- Modify: `app/tarot/page.tsx`
- Modify: `app/zodiac/page.tsx`

Rules:
- The server owns the merchant TRC20 address.
- The server owns required amount and selected plan.
- The client sends only `orderId`, `walletTail`, and policy acceptance evidence.
- The order must include `planId`, `amount`, `currency`, `merchantAddress`, and `expiresAt`.
- A transaction hash can be used only once.
- Verification must require either memo/reference code or a unique amount strategy.

Verification:
- Create TRC20 order and confirm Redis stores server-defined amount/address.
- Try sending a lower amount; expected: no unlock.
- Try verifying without `orderId`; expected: rejected.
- Try reusing the same transaction hash for a second order; expected: rejected.
- Confirm paid TRC20 order creates entitlement just like PayPal.

### Phase 5: Rate Limit and Abuse Protection

Files:
- Modify: `app/api/chat/route.ts`
- Modify: `app/api/share/route.ts`
- Modify: `app/api/paypal/create-order/route.ts`
- Modify: `app/api/paypal/capture-order/route.ts`
- Modify: `app/api/verify-payment/route.ts`

Rules:
- Add IP-based rate limits for teaser generation.
- Add stricter rate limits for payment creation and capture.
- Add schema validation for request bodies.
- Limit max prompt/input lengths.
- Do not expose provider errors or secrets in production responses.

Verification:
- Call free teaser endpoint more than the configured limit; expected: `429`.
- Send invalid request body; expected: `400`.
- Confirm production errors do not include API secrets or raw provider responses.

### Phase 6: Apply for Payoneer Checkout in Parallel

Application message:

```text
I want to apply for Payoneer Checkout for my independent website https://www.fatematrices.com.
We sell AI-generated astrology, tarot, zodiac, and personality entertainment reports delivered digitally after payment.
The service is for entertainment and personal insight only and does not provide financial, legal, medical, or investment advice.
We need hosted checkout or API integration with webhook payment confirmation.
```

Prepare:
- Website URL.
- Terms of Service URL.
- Privacy Policy URL.
- Refund Policy URL.
- Contact URL.
- Product descriptions and prices.
- Delivery method: instant digital report generation.
- Expected monthly volume and average order value.
- Business identity and bank/payout information.

Decision:
- If Payoneer approves Checkout, add it as another provider behind the same order and entitlement model.
- If Payoneer does not approve Checkout, continue with PayPal + USDT.
- Do not use Payoneer receiving account details for public website checkout.

## 5. Discussion Questions Before Implementation

1. Should the first processor be PayPal Checkout, or should we evaluate another provider before building?
2. Do you want the legal/trust pages in English only first, or Chinese and English from day one?
3. What support email should be shown on Contact, Terms, Refund, and payment receipts?
4. Should paid reports unlock in the same browser session only, or should we also support email/order-code recovery?
5. Should USDT remain visible as a primary option, or move behind an "Alternative payment" toggle?

## 6. Recommended Next Step

Start with Phase 1 and Phase 2 together:
- Phase 1 makes the site review-ready for PayPal, Payoneer Checkout, and other payment processors.
- Phase 2 fixes the current paid-content bypass risk before any new payment provider is connected.

After Phase 1 and Phase 2 pass, add PayPal Checkout as Phase 3.

## 7. Verification Checklist

- [ ] `npm run lint` passes.
- [ ] `npm run build` passes.
- [ ] Legal/trust pages are visible from checkout.
- [ ] Payment modal requires refund-policy acceptance before creating an order.
- [ ] `/api/chat` rejects paid unlocks without a paid entitlement.
- [ ] PayPal Sandbox payment creates one paid order and one entitlement.
- [ ] Refunded/denied payments revoke entitlement.
- [ ] TRC20 backup no longer trusts client-provided amount or address.
- [ ] Mobile checkout fits within viewport.
- [ ] No public page asks ordinary customers to pay into the Payoneer receiving account.

