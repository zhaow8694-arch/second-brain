// ==========================================
// Payoneer 收款配置
// 等账户签发后，填入实际信息
// ==========================================

export const PAYONEER_CONFIG = {
  // Payoneer 美国收款账户信息
  // TODO: 账户签发后替换为实际信息
  accountName: process.env.PAYONEER_ACCOUNT_NAME || '',
  routingNumber: process.env.PAYONEER_ROUTING_NUMBER || '',
  accountNumber: process.env.PAYONEER_ACCOUNT_NUMBER || '',
  bankName: 'First Century Bank, NA',
  bankAddress: '1230 Peachtree Street, NE, Atlanta, GA 30309, USA',

  // 收款人信息
  beneficiaryName: process.env.PAYONEER_BENEFICIARY_NAME || '',
  beneficiaryAddress: process.env.PAYONEER_BENEFICIARY_ADDRESS || '',
};

// ==========================================
// 定价配置
// ==========================================

export const PRICING = {
  LITE: {
    id: 'LITE' as const,
    priceUSD: 10,
    priceUSDT: 10,
    description: '基础解读',
  },
  ELITE: {
    id: 'ELITE' as const,
    priceUSD: 29.9,
    priceUSDT: 29.9,
    description: '深度解锁',
  },
};

export type PlanId = 'LITE' | 'ELITE';

// ==========================================
// 支付方式枚举
// ==========================================

export type PaymentMethod = 'TRC20' | 'PAYONEER';

// ==========================================
// 获取当前启用的支付方式
// 当 Payoneer 配置完整时自动启用
// ==========================================

export function getAvailablePaymentMethods(): PaymentMethod[] {
  const methods: PaymentMethod[] = ['TRC20'];

  const payoneerReady =
    PAYONEER_CONFIG.accountName &&
    PAYONEER_CONFIG.routingNumber &&
    PAYONEER_CONFIG.accountNumber;

  if (payoneerReady) {
    methods.push('PAYONEER');
  }

  return methods;
}

// ==========================================
// 生成 Payoneer 支付订单
// TODO: 账户签发后实现实际逻辑
// ==========================================

export interface PayoneerPaymentRequest {
  planId: PlanId;
  amount: number;
  currency: string;
  customerEmail?: string;
  customerName?: string;
}

export interface PayoneerPaymentResponse {
  success: boolean;
  paymentId?: string;
  instructions?: PayoneerPaymentInstructions;
  error?: string;
}

export interface PayoneerPaymentInstructions {
  bankName: string;
  bankAddress: string;
  accountName: string;
  accountNumber: string;
  routingNumber: string;
  beneficiaryName: string;
  referenceCode: string;
  amount: number;
  currency: string;
}

export async function createPayoneerPayment(
  request: PayoneerPaymentRequest
): Promise<PayoneerPaymentResponse> {
  // TODO: 账户签发后实现
  // 1. 生成唯一支付参考号
  // 2. 存储订单到 Redis
  // 3. 返回电汇指令
  return {
    success: true,
    paymentId: `PAY-${Date.now()}`,
    instructions: {
      bankName: PAYONEER_CONFIG.bankName,
      bankAddress: PAYONEER_CONFIG.bankAddress,
      accountName: PAYONEER_CONFIG.accountName,
      accountNumber: PAYONEER_CONFIG.accountNumber,
      routingNumber: PAYONEER_CONFIG.routingNumber,
      beneficiaryName: PAYONEER_CONFIG.beneficiaryName,
      referenceCode: `REF-${Date.now().toString(36).toUpperCase()}`,
      amount: request.amount,
      currency: request.currency,
    },
  };
}

// ==========================================
// 验证 Payoneer 支付状态
// TODO: 账户签发后实现实际逻辑
// ==========================================

export async function verifyPayoneerPayment(
  _paymentId: string
): Promise<{ verified: boolean; transactionId?: string }> {
  // TODO: 账户签发后实现
  // 1. 查询 Redis 中的支付状态
  // 2. 或调用 Payoneer API 查询
  return { verified: false };
}
