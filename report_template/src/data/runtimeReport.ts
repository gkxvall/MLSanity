import { mockReport, type Report } from "@/data/mockReport";

declare global {
  interface Window {
    __MLSANITY_REPORT__?: Partial<Report>;
  }
}

export const getRuntimeReport = (): Report => {
  if (typeof window !== "undefined" && window.__MLSANITY_REPORT__) {
    return {
      ...mockReport,
      ...window.__MLSANITY_REPORT__,
      checks: window.__MLSANITY_REPORT__.checks ?? mockReport.checks,
      class_counts: window.__MLSANITY_REPORT__.class_counts ?? mockReport.class_counts,
      split_counts: window.__MLSANITY_REPORT__.split_counts ?? mockReport.split_counts,
      splits_available: window.__MLSANITY_REPORT__.splits_available ?? mockReport.splits_available,
    };
  }
  return mockReport;
};

