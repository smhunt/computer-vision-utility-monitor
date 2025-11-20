# Project TODOs

## High Priority

### Link Meters to Database (Data-Driven Dashboard)
**Status**: ✅ Completed (2025-11-20)
**Description**: Replace fake/mock data with real database connections
- [x] Link water meter readings from InfluxDB to dashboard display
- [x] Link electric meter readings from InfluxDB to dashboard display
- [x] Link gas meter readings from InfluxDB to dashboard display
- [x] Ensure meter metadata (unit, type, location) is data-driven from DB
- [x] Replace hardcoded cost rates with data-driven pricing from config
- [x] Test with real meter snapshots from cameras

**Completed**:
- Created Flask API endpoints: `/api/config/meters` and `/api/config/pricing`
- Added TypeScript types for meter and pricing configuration
- Updated Dashboard to use data-driven pricing rates from [config/pricing.json](file:///Users/seanhunt/Code/computer-vision-utility-monitor/config/pricing.json)
- Dashboard now calculates costs using real utility rates for Ontario (water, electricity, natural gas)
- Meter readings are fetched from InfluxDB via Flask backend (with mock data fallback)

**Notes**: The dashboard is now fully data-driven! Costs are calculated using real pricing data from [config/pricing.json](file:///Users/seanhunt/Code/computer-vision-utility-monitor/config/pricing.json), and the system falls back to mock data only when the Flask API is unavailable.

## Future Enhancements

### shadcn/ui Component Integration
- [ ] Explore adding shadcn/ui components to enhance dashboard UI
- [ ] Consider Card component for meter displays
- [ ] Consider Button component for actions
- [ ] Consider Badge component for status indicators

---
*This file tracks ongoing development tasks and future enhancements.*
