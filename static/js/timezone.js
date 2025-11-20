/**
 * Timezone utilities for displaying times in user's local timezone
 */

// Get the user's timezone
function getUserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

// Get timezone abbreviation (e.g., "EST", "PST")
function getTimezoneAbbreviation() {
  const date = new Date();
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZoneName: 'short'
  });
  const parts = formatter.formatToParts(date);
  const timeZonePart = parts.find(part => part.type === 'timeZoneName');
  return timeZonePart ? timeZonePart.value : '';
}

// Get UTC offset (e.g., "UTC-05:00")
function getUTCOffset() {
  const offset = -new Date().getTimezoneOffset();
  const hours = Math.floor(Math.abs(offset) / 60);
  const minutes = Math.abs(offset) % 60;
  const sign = offset >= 0 ? '+' : '-';
  return `UTC${sign}${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

// Format a date in user's local timezone
function formatInLocalTimezone(date, options = {}) {
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    ...options
  };

  return new Intl.DateTimeFormat('en-US', defaultOptions).format(dateObj);
}

// Format date with timezone info
function formatWithTimezone(date) {
  const formatted = formatInLocalTimezone(date);
  const tz = getTimezoneAbbreviation();
  return `${formatted} ${tz}`;
}

// Format date for short display (time only)
function formatTimeOnly(date) {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(dateObj);
}

// Convert all timestamps on page to local timezone
function convertTimestampsToLocal() {
  // Find all elements with data-timestamp attribute
  const timestampElements = document.querySelectorAll('[data-timestamp]');

  timestampElements.forEach(element => {
    const isoTimestamp = element.getAttribute('data-timestamp');
    if (isoTimestamp) {
      const formattedTime = formatWithTimezone(isoTimestamp);
      element.textContent = formattedTime;
    }
  });
}

// Update page footer with timezone information
function updateTimezoneFooter() {
  const footerEl = document.getElementById('timezone-footer');
  if (footerEl) {
    const timezone = getUserTimezone();
    const abbreviation = getTimezoneAbbreviation();
    const offset = getUTCOffset();
    footerEl.innerHTML = `
      <div style="text-align: center; padding: 20px; border-top: 1px solid #e7e5e4; margin-top: 30px;">
        <p style="color: #78716c; font-size: 13px; margin: 0;">
          <strong>Timezone:</strong> ${timezone} (${abbreviation}) • ${offset}
        </p>
        <p style="color: #a8a29e; font-size: 11px; margin-top: 8px;">
          All times displayed in your local timezone
        </p>
      </div>
    `;
  }
}

// Initialize timezone utilities when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    convertTimestampsToLocal();
    updateTimezoneFooter();
  });
} else {
  convertTimestampsToLocal();
  updateTimezoneFooter();
}
