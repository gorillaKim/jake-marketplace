import { createContext, type ReactNode, useRef } from 'react';
import type { Tracker } from '../types';

export const GTMTrackerContext = createContext<Tracker | null>(null);

interface GTMTrackerProviderProps {
  tracker: Tracker;
  children: ReactNode;
}

/**
 * tracker 인스턴스를 최초 전달값으로 고정하여 불필요한 리렌더를 방지한다.
 */
export function GTMTrackerProvider({ tracker, children }: GTMTrackerProviderProps) {
  const trackerRef = useRef(tracker);

  return (
    <GTMTrackerContext.Provider value={trackerRef.current}>
      {children}
    </GTMTrackerContext.Provider>
  );
}
