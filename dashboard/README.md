# Utility Monitor Dashboard

A modern React dashboard for viewing real-time utility meter readings powered by Claude Vision AI.

## Features

- **Real-time Monitoring**: Live updates of water, electric, and gas meter readings
- **Historical Charts**: 7-day historical data visualization using Chart.js
- **Cost Tracking**: Automatic cost calculation based on usage
- **Confidence Scoring**: Visual indicators for AI reading confidence (high/medium/low)
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Chart.js** (react-chartjs-2) for data visualization
- **TanStack Query** for data fetching and caching
- **Lucide React** for icons
- **Axios** for API calls
- **date-fns** for date formatting

## Prerequisites

- Node.js 20.x or higher
- npm or yarn
- InfluxDB running (see parent project's docker-compose.yml)

## Installation

1. **Install dependencies**:
   ```bash
   cd dashboard
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file** with your InfluxDB credentials:
   ```env
   VITE_INFLUXDB_URL=http://localhost:8086
   VITE_INFLUXDB_TOKEN=your-influxdb-token
   VITE_INFLUXDB_ORG=ecoworks
   VITE_INFLUXDB_BUCKET=utility_meters
   ```

## Development

Start the development server:

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Building for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

To preview the production build:

```bash
npm run preview
```

## Project Structure

```
dashboard/
├── src/
│   ├── api/
│   │   └── influxdb.ts          # InfluxDB API client
│   ├── components/
│   │   ├── Dashboard.tsx        # Main dashboard component
│   │   ├── MeterCard.tsx        # Individual meter card
│   │   ├── MeterChart.tsx       # Historical data chart
│   │   └── CostTracker.tsx      # Cost tracking component
│   ├── types/
│   │   └── meter.ts             # TypeScript types
│   ├── App.tsx                  # Root component
│   ├── main.tsx                 # Application entry point
│   └── index.css                # Global styles
├── public/                      # Static assets
├── .env.example                 # Environment variables template
├── tailwind.config.js           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
├── vite.config.ts               # Vite configuration
└── package.json                 # Dependencies
```

## Configuration

### Cost Rates

Edit the `COST_RATES` object in `src/components/Dashboard.tsx`:

```typescript
const COST_RATES = {
  water: 0.005,   // per gallon
  electric: 0.12, // per kWh
  gas: 0.85,      // per CCF
};
```

### Refresh Intervals

Data refresh intervals can be adjusted in `src/components/Dashboard.tsx`:

- Latest readings: `refetchInterval: 60000` (1 minute)
- Historical data: `refetchInterval: 300000` (5 minutes)

## Troubleshooting

### Dashboard shows no data

1. **Check InfluxDB is running**:
   ```bash
   docker-compose ps
   ```

2. **Verify InfluxDB token**:
   - Log into InfluxDB UI at `http://localhost:8086`
   - Generate a new token if needed
   - Update `.env` file

3. **Check browser console** for API errors

### CORS issues

If you see CORS errors, you may need to configure InfluxDB CORS settings or use a proxy server.

## Development with Mock Data

The API client includes mock data generation for development. If InfluxDB is unavailable, the dashboard will automatically use mock data.

## License

MIT
