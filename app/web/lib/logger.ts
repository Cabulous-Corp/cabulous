import pino from 'pino'

const isProduction = process.env.NODE_ENV === 'production'

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: !isProduction
    ? {
        target: 'pino-pretty',
        options: {
          colorize: true,
          ignore: 'pid,hostname',
          translateTime: 'SYS:standard',
          timestamp: true,
        },
      }
    : undefined,
  base: isProduction ? undefined : { pid: undefined, hostname: undefined },
})

export const logData = <T>(data: T): T => {
  logger.info(JSON.stringify(data, null, 2))
  return data
}
