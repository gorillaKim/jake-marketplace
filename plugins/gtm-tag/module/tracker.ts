import type { ResolvedEvent, Tracker, TrackerConfig } from './types';
import { validateParams } from './validation';

/**
 * GTM Tracker 인스턴스를 생성한다.
 *
 * @example
 * const tracker = createTracker({ debug: true });
 * tracker.trackEvent(EVENTS.report.click_download, { report_id: '123' });
 */
export function createTracker(config: TrackerConfig = {}): Tracker {
  let globalParams: Record<string, unknown> = {};

  function trackEvent(event: ResolvedEvent, params?: Record<string, unknown>): void {
    const mergedParams = params ?? {};

    validateParams(event, mergedParams);

    const payload: Record<string, unknown> = {
      event: event.eventName,
      ...globalParams,
      ...mergedParams,
    };

    if (config.debug) {
      console.log(`[GTM Tracker] ${event.eventName}`, payload);
    }

    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(payload);
  }

  function setGlobalParams(params: Record<string, unknown>): void {
    globalParams = { ...globalParams, ...params };
  }

  return { trackEvent, setGlobalParams };
}
