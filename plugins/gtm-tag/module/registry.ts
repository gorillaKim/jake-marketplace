import type { EventDef, EventsSchema, ResolvedEvent } from './types';

/** defineEvents 반환 타입 */
export type ResolvedEventsMap = Record<string, Record<string, ResolvedEvent>>;

/**
 * 타입 안전한 이벤트 레지스트리를 정의한다.
 *
 * @param prefix - 팀 prefix (e.g. 'da')
 * @param schema - 도메인별 이벤트 정의
 * @returns 도메인.액션 구조의 resolved 이벤트 객체
 *
 * @example
 * const EVENTS = defineEvents('da', {
 *   report: {
 *     click_download: {
 *       description: '리포트 다운로드',
 *       params: { report_id: { type: 'string', required: true } },
 *     },
 *   },
 * });
 * // EVENTS.report.click_download.eventName === 'da_report_click_download'
 */
export function defineEvents(prefix: string, schema: EventsSchema): ResolvedEventsMap {
  const result: ResolvedEventsMap = {};

  for (const domain of Object.keys(schema)) {
    result[domain] = {};
    for (const action of Object.keys(schema[domain])) {
      const def: EventDef = schema[domain][action];
      result[domain][action] = {
        eventName: `${prefix}_${domain}_${action}`,
        description: def.description,
        params: def.params,
      };
    }
  }

  return result;
}
