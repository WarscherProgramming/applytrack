import type { DailyBriefingResponse, NotificationPriority } from './types';

export function downloadBriefing(data: DailyBriefingResponse) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `daily-briefing-${data.briefing_date}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

export function priorityLabel(priority: NotificationPriority) {
  return priority.charAt(0).toUpperCase() + priority.slice(1);
}

export function priorityBadge(priority: NotificationPriority) {
  if (priority === 'urgent') return 'destructive';
  if (priority === 'high') return 'default';
  return 'secondary';
}
