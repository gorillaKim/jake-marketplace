import { defineEvents } from '../registry';

describe('defineEvents', () => {
  it('should generate correct event names from prefix + domain + action', () => {
    const events = defineEvents('da', {
      report: {
        click_download: { description: '다운로드' },
        view_detail: { description: '상세 조회' },
      },
      campaign: {
        submit_filter: { description: '필터 제출' },
      },
    });

    expect(events.report.click_download.eventName).toBe('da_report_click_download');
    expect(events.report.view_detail.eventName).toBe('da_report_view_detail');
    expect(events.campaign.submit_filter.eventName).toBe('da_campaign_submit_filter');
  });

  it('should preserve description and params', () => {
    const events = defineEvents('da', {
      report: {
        click_download: {
          description: '리포트 다운로드',
          params: {
            report_id: { type: 'string', required: true },
          },
        },
      },
    });

    expect(events.report.click_download.description).toBe('리포트 다운로드');
    expect(events.report.click_download.params).toEqual({
      report_id: { type: 'string', required: true },
    });
  });

  it('should work with different prefixes', () => {
    const events = defineEvents('creative', {
      ad: {
        click_preview: { description: '미리보기' },
      },
    });

    expect(events.ad.click_preview.eventName).toBe('creative_ad_click_preview');
  });
});
