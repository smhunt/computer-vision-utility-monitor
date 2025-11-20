# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Hourly Consumption Graph**: Interactive Chart.js bar chart showing water usage by hour on meter detail page
  - New API endpoint `/api/consumption/<meter_type>` for fetching hourly data
  - Displays last 24 hours of consumption data
  - Hover tooltips with exact m³ values
  - Graceful handling of empty data with friendly message

- **Auto-Capture Toggle**: Automated meter reading capture every 60 seconds
  - Toggle switch UI with ON/OFF visual state
  - Live countdown timer showing seconds until next capture
  - Immediate capture on toggle enable
  - Manual capture resets the auto-capture timer
  - Countdown delays until first capture completes

- **Enhanced Progress Feedback**: Step-by-step progress indicators during capture and reprocess
  - 📡 Connecting to camera (10%)
  - 📸 Capturing image from meter (20%)
  - 🤖 Analyzing meter reading with AI (30-75%, animated)
  - 📦 Archiving snapshot (80%)
  - 📝 Logging data (90%)
  - ✅ Complete (100%)
  - Smooth animated transitions between stages
  - Visual feedback helps users understand processing time

- **Custom Modal Dialogs**: Beautiful animated modals replace browser confirm() dialogs
  - Slide-down entrance animation
  - Semi-transparent overlay with fade-in
  - Custom styling matching app design
  - Promise-based API for clean async/await usage
  - Cancel and Confirm buttons with hover effects

- **Capture Button Feedback**: Visual feedback on successful capture
  - Changes to "✅ Captured Successfully" with green background
  - Resets to "📸 Capture Now" after success message fades
  - Better user confirmation of successful operations

- **Snapshot Card Auto-Refresh**: Snapshots refresh automatically without page reload
  - Refreshes after both manual capture and reprocess operations
  - Skeleton loading animation during refresh
  - Smooth fade-in of new snapshot cards

- **5-Second Auto-Fade**: Success messages automatically fade out after 5 seconds
  - Prevents UI clutter
  - Smooth CSS transitions
  - Progress container and results fade together

### Changed
- Progress bar now shows realistic step-by-step progress instead of jumping to completion
- AI analysis progress animates smoothly from 30% to 75% during actual processing
- Improved timing: initial steps show for 500-600ms for better visibility

### Technical
- Added Chart.js CDN for consumption graph rendering
- New `/api/snapshots/<meter_name>` endpoint for fetching snapshot metadata
- Consumption calculation uses max-min per hour from JSONL readings
- Modal system uses Promise-based confirmation flow
- Auto-capture uses setInterval with countdown synchronization

## [2025-11-19] - Vision Model Integration

### Added
- Gemini 2.5 Flash integration as primary vision model (free tier)
- Claude Sonnet 4.5 as fallback vision model
- Multi-model support with automatic fallback
- Vision model tracking in all readings
- API usage tracking for cost monitoring

### Changed
- Primary vision model changed from Claude to Gemini (saving ~$400/month)
- All meter readings now include `vision_model` and `vision_provider` fields

## Earlier Changes

See git history for changes prior to 2025-11-19.
