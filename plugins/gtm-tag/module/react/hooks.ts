import { useContext } from 'react';
import { GTMTrackerContext } from './provider';
import type { Tracker } from '../types';

/**
 * GTMTrackerProvider 하위에서 trackEvent 함수를 가져온다.
 *
 * @example
 * const trackEvent = useTrackEvent();
 * trackEvent(EVENTS.report.click_download, { report_id: '123' });
 */
export function useTrackEvent(): Tracker['trackEvent'] {
  const tracker = useContext(GTMTrackerContext);
  if (!tracker) {
    throw new Error('useTrackEvent must be used within <GTMTrackerProvider>');
  }
  return tracker.trackEvent;
}

/**
 * GTMTrackerProvider 하위에서 tracker 인스턴스 전체를 가져온다.
 * trackEvent + setGlobalParams 모두 필요할 때 사용.
 */
export function useTracker(): Tracker {
  const tracker = useContext(GTMTrackerContext);
  if (!tracker) {
    throw new Error('useTracker must be used within <GTMTrackerProvider>');
  }
  return tracker;
}
