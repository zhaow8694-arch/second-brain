import { Redis } from '@upstash/redis'

let redisInstance: Redis | null = null

export function getRedis(): Redis {
  if (!redisInstance) {
    redisInstance = Redis.fromEnv()
  }
  return redisInstance
}

export const redis = getRedis()