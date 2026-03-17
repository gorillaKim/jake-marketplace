import type { EventParamDef, ResolvedEvent } from './types';

const TYPE_MAP: Record<EventParamDef['type'], string> = {
  string: 'string',
  number: 'number',
  boolean: 'boolean',
};

/**
 * dev 환경에서 필수 파라미터 누락 및 타입 불일치를 검증한다.
 * production에서는 아무 동작도 하지 않는다.
 */
export function validateParams(
  event: ResolvedEvent,
  params: Record<string, unknown>,
): void {
  if (process.env.NODE_ENV === 'production') return;
  if (!event.params) return;

  const missing: string[] = [];
  const typeMismatch: string[] = [];

  for (const [key, def] of Object.entries(event.params) as [string, EventParamDef][]) {
    const value = params[key];

    if (def.required && (value === undefined || value === null)) {
      missing.push(key);
      continue;
    }

    if (value !== undefined && value !== null && typeof value !== TYPE_MAP[def.type]) {
      typeMismatch.push(`${key} (expected ${def.type}, got ${typeof value})`);
    }
  }

  if (missing.length > 0) {
    console.warn(
      `[GTM Tracker] Event "${event.eventName}" missing required params: ${missing.join(', ')}`,
    );
  }

  if (typeMismatch.length > 0) {
    console.warn(
      `[GTM Tracker] Event "${event.eventName}" type mismatch: ${typeMismatch.join(', ')}`,
    );
  }
}
