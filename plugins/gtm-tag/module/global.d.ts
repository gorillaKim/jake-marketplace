/** GTM dataLayer 전역 타입 */
export {};

declare global {
  interface Window {
    dataLayer?: Record<string, unknown>[];
  }
}
