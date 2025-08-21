/**
 * Logger utility for production-safe logging
 * Only logs in development mode unless explicitly enabled
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  enabled: boolean;
  level: LogLevel;
}

class Logger {
  private config: LoggerConfig;
  private levels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  constructor() {
    // In production, logging is disabled by default
    // In development (when import.meta.env exists), logging is enabled
    let isDev = false;
    let enableLogging = false;
    let logLevel: LogLevel = 'info';

    try {
      // This will only work in development
      isDev = import.meta.env.DEV === true;
      enableLogging = import.meta.env.VITE_ENABLE_LOGGING === 'true';
      logLevel = (import.meta.env.VITE_LOG_LEVEL as LogLevel) || 'info';
    } catch {
      // In production, import.meta.env doesn't exist, so we catch the error
      // and use default values (logging disabled)
    }

    this.config = {
      enabled: isDev || enableLogging,
      level: logLevel,
    };
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;
    return this.levels[level] >= this.levels[this.config.level];
  }

  debug(...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.log('[DEBUG]', ...args);
    }
  }

  info(...args: any[]): void {
    if (this.shouldLog('info')) {
      console.info('[INFO]', ...args);
    }
  }

  warn(...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn('[WARN]', ...args);
    }
  }

  error(...args: any[]): void {
    if (this.shouldLog('error')) {
      console.error('[ERROR]', ...args);
    }
  }

  // Generic log method for compatibility with external libraries
  log(...args: any[]): void {
    if (this.shouldLog('info')) {
      console.log('[LOG]', ...args);
    }
  }

  // Group logging for better organization
  group(label: string): void {
    if (this.config.enabled) {
      console.group(label);
    }
  }

  groupEnd(): void {
    if (this.config.enabled) {
      console.groupEnd();
    }
  }

  // Table logging for structured data
  table(data: any): void {
    if (this.config.enabled && this.shouldLog('debug')) {
      console.table(data);
    }
  }

  // Time measurement
  time(label: string): void {
    if (this.config.enabled && this.shouldLog('debug')) {
      console.time(label);
    }
  }

  timeEnd(label: string): void {
    if (this.config.enabled && this.shouldLog('debug')) {
      console.timeEnd(label);
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export for typing
export type { LogLevel, LoggerConfig };
