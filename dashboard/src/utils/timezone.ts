/**
 * Timezone utilities for displaying times in user's local timezone
 */

/**
 * Get the user's timezone
 * @returns IANA timezone string (e.g., "America/Toronto", "America/New_York")
 */
export function getUserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/**
 * Get timezone abbreviation (e.g., "EST", "PST")
 */
export function getTimezoneAbbreviation(): string {
  const date = new Date();
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZoneName: 'short',
  });
  const parts = formatter.formatToParts(date);
  const timeZonePart = parts.find(part => part.type === 'timeZoneName');
  return timeZonePart?.value || '';
}

/**
 * Format a date in user's local timezone
 * @param date Date object or ISO string
 * @param options Intl.DateTimeFormatOptions
 */
export function formatInLocalTimezone(
  date: Date | string,
  options?: Intl.DateTimeFormatOptions
): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    ...options,
  };

  return new Intl.DateTimeFormat('en-US', defaultOptions).format(dateObj);
}

/**
 * Format a date for display with timezone info
 * @param date Date object or ISO string
 */
export function formatWithTimezone(date: Date | string): string {
  const formatted = formatInLocalTimezone(date);
  const tz = getTimezoneAbbreviation();
  return `${formatted} ${tz}`;
}

/**
 * Get UTC offset in hours
 */
export function getUTCOffset(): string {
  const offset = -new Date().getTimezoneOffset();
  const hours = Math.floor(Math.abs(offset) / 60);
  const minutes = Math.abs(offset) % 60;
  const sign = offset >= 0 ? '+' : '-';
  return `UTC${sign}${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

/**
 * Format date for chart labels (short format)
 */
export function formatForChart(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(dateObj);
}
