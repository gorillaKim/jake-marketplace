/** 이벤트 파라미터 정의 */
export interface EventParamDef {
  type: 'string' | 'number' | 'boolean';
  required?: boolean;
  description?: string;
}

/** 단일 이벤트 정의 (사용자 작성용) */
export interface EventDef {
  description?: string;
  params?: Record<string, EventParamDef>;
}

/** 도메인별 이벤트 맵 (사용자 작성용) */
export type EventsSchema = Record<string, Record<string, EventDef>>;

/** 런타임에 사용되는 resolved 이벤트 */
export interface ResolvedEvent {
  eventName: string;
  description?: string;
  params?: Record<string, EventParamDef>;
}

/** Tracker 설정 */
export interface TrackerConfig {
  /** true면 console.log로 이벤트 출력 */
  debug?: boolean;
}

/** Tracker 인스턴스 */
export interface Tracker {
  trackEvent: (event: ResolvedEvent, params?: Record<string, unknown>) => void;
  setGlobalParams: (params: Record<string, unknown>) => void;
}
