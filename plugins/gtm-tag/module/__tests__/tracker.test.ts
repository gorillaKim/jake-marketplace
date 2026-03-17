import { createTracker } from '../tracker';
import { defineEvents } from '../registry';

const EVENTS = defineEvents('da', {
  report: {
    click_download: {
      description: '리포트 다운로드',
      params: {
        report_id: { type: 'string', required: true },
        report_type: { type: 'string' },
      },
    },
  },
  page: {
    view_main: {
      description: '메인 페이지 진입',
    },
  },
});

describe('createTracker', () => {
  beforeEach(() => {
    window.dataLayer = [];
  });

  it('should push event to dataLayer with correct event name', () => {
    const tracker = createTracker();
    tracker.trackEvent(EVENTS.report.click_download, {
      report_id: '123',
    });

    expect(window.dataLayer).toHaveLength(1);
    expect(window.dataLayer![0]).toMatchObject({
      event: 'da_report_click_download',
      report_id: '123',
    });
  });

  it('should allow trackEvent without params for param-less events', () => {
    const tracker = createTracker();
    tracker.trackEvent(EVENTS.page.view_main);

    expect(window.dataLayer).toHaveLength(1);
    expect(window.dataLayer![0]).toMatchObject({
      event: 'da_page_view_main',
    });
  });

  it('should include global params in every event', () => {
    const tracker = createTracker();
    tracker.setGlobalParams({ workspace_id: 'ws-1' });
    tracker.trackEvent(EVENTS.report.click_download, {
      report_id: '456',
    });

    expect(window.dataLayer![0]).toMatchObject({
      event: 'da_report_click_download',
      report_id: '456',
      workspace_id: 'ws-1',
    });
  });

  it('should allow event params to override global params', () => {
    const tracker = createTracker();
    tracker.setGlobalParams({ report_id: 'global' });
    tracker.trackEvent(EVENTS.report.click_download, {
      report_id: 'local',
    });

    expect(window.dataLayer![0]).toMatchObject({
      report_id: 'local',
    });
  });

  it('should log to console in debug mode', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    const tracker = createTracker({ debug: true });
    tracker.trackEvent(EVENTS.report.click_download, { report_id: '1' });

    expect(consoleSpy).toHaveBeenCalledWith(
      '[GTM Tracker] da_report_click_download',
      expect.objectContaining({ event: 'da_report_click_download' }),
    );
    consoleSpy.mockRestore();
  });

  it('should initialize dataLayer if not exists', () => {
    delete (window as unknown as Record<string, unknown>).dataLayer;
    const tracker = createTracker();
    tracker.trackEvent(EVENTS.report.click_download, { report_id: '1' });

    expect(window.dataLayer).toHaveLength(1);
  });

  it('should warn on missing required params in dev', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation();
    const tracker = createTracker();
    tracker.trackEvent(EVENTS.report.click_download, {});

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('missing required params: report_id'),
    );
    warnSpy.mockRestore();
  });

  it('should warn on type mismatch in dev', () => {
    const warnSpy = jest.spyOn(console, 'warn').mockImplementation();
    const tracker = createTracker();
    tracker.trackEvent(EVENTS.report.click_download, { report_id: 123 });

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('type mismatch'),
    );
    warnSpy.mockRestore();
  });
});
