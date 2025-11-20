import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, RefreshCw } from 'lucide-react';
import { MeterCard } from './MeterCard';
import { MeterChart } from './MeterChart';
import { CostTracker } from './CostTracker';
import { ThemeToggle } from './ThemeToggle';
import { fetchLatestReading, fetchHistoricalData } from '../api/influxdb';
import type { MeterData, CostData } from '../types/meter';
import { getUserTimezone, getTimezoneAbbreviation, getUTCOffset, formatWithTimezone } from '../utils/timezone';

// Cost rates (configurable) - Canadian rates
const COST_RATES = {
  water: 0.0013, // per litre (approx $1.30 per cubic meter)
  electric: 0.12, // per kWh
  gas: 0.30, // per cubic meter
};

export function Dashboard() {
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Fetch latest readings for all meters
  const { data: waterReading, refetch: refetchWater } = useQuery({
    queryKey: ['meter', 'water'],
    queryFn: () => fetchLatestReading('water'),
    refetchInterval: 60000, // Refetch every minute
  });

  const { data: electricReading, refetch: refetchElectric } = useQuery({
    queryKey: ['meter', 'electric'],
    queryFn: () => fetchLatestReading('electric'),
    refetchInterval: 60000,
  });

  const { data: gasReading, refetch: refetchGas } = useQuery({
    queryKey: ['meter', 'gas'],
    queryFn: () => fetchLatestReading('gas'),
    refetchInterval: 60000,
  });

  // Fetch historical data for charts
  const { data: waterHistory, refetch: refetchWaterHistory } = useQuery({
    queryKey: ['history', 'water'],
    queryFn: () => fetchHistoricalData('water', '-7d'),
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  const { data: electricHistory, refetch: refetchElectricHistory } = useQuery({
    queryKey: ['history', 'electric'],
    queryFn: () => fetchHistoricalData('electric', '-7d'),
    refetchInterval: 300000,
  });

  const { data: gasHistory, refetch: refetchGasHistory } = useQuery({
    queryKey: ['history', 'gas'],
    queryFn: () => fetchHistoricalData('gas', '-7d'),
    refetchInterval: 300000,
  });

  // Calculate meter data
  const calculateMeterData = (
    reading: any,
    history: any[],
    unit: string
  ): MeterData => {
    if (!reading || !history || history.length === 0) {
      return {
        current: 0,
        unit,
        lastUpdated: new Date().toISOString(),
        confidence: 'low',
        change24h: 0,
        trend: 'stable',
      };
    }

    const current = reading.value;
    const yesterday = history.find(
      h => new Date(h.timestamp).getTime() < Date.now() - 24 * 60 * 60 * 1000
    );
    const change24h = yesterday ? current - yesterday.value : 0;

    return {
      current,
      unit,
      lastUpdated: reading.time,
      confidence: reading.confidence,
      change24h,
      trend: change24h > 10 ? 'up' : change24h < -10 ? 'down' : 'stable',
    };
  };

  const waterData = calculateMeterData(waterReading, waterHistory || [], 'L');
  const electricData = calculateMeterData(electricReading, electricHistory || [], 'kWh');
  const gasData = calculateMeterData(gasReading, gasHistory || [], 'm³');

  // Calculate costs
  const costs: CostData[] = [
    {
      meterType: 'water',
      dailyCost: waterData.change24h * COST_RATES.water,
      monthlyCost: waterData.change24h * COST_RATES.water * 30,
      currency: 'CAD',
    },
    {
      meterType: 'electric',
      dailyCost: electricData.change24h * COST_RATES.electric,
      monthlyCost: electricData.change24h * COST_RATES.electric * 30,
      currency: 'CAD',
    },
    {
      meterType: 'gas',
      dailyCost: gasData.change24h * COST_RATES.gas,
      monthlyCost: gasData.change24h * COST_RATES.gas * 30,
      currency: 'CAD',
    },
  ];

  const handleRefresh = () => {
    // Pull latest cards and charts together so the page stays in sync
    refetchWater();
    refetchElectric();
    refetchGas();
    refetchWaterHistory();
    refetchElectricHistory();
    refetchGasHistory();
    setLastUpdate(new Date());
  };

  // Get user timezone information
  const userTimezone = getUserTimezone();
  const timezoneAbbr = getTimezoneAbbreviation();
  const utcOffset = getUTCOffset();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Header */}
      <header className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-b border-slate-300/50 dark:border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2.5 bg-blue-500/20 rounded-xl border border-blue-500/30">
                <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Utility Monitor</h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">Real-time meter readings</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <button
                onClick={handleRefresh}
                className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-all shadow-lg shadow-blue-900/30"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8">

        {/* Current Readings Section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
            <div className="w-1 h-5 bg-blue-500 rounded-full"></div>
            Current Readings
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <MeterCard type="water" data={waterData} />
            <MeterCard type="electric" data={electricData} />
            <MeterCard type="gas" data={gasData} />
          </div>
        </section>

        {/* Cost Tracking Section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
            <div className="w-1 h-5 bg-green-500 rounded-full"></div>
            Cost Tracking
          </h2>
          <CostTracker costs={costs} />
        </section>

        {/* Usage History Section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
            <div className="w-1 h-5 bg-purple-500 rounded-full"></div>
            Usage History (7 Days)
          </h2>
          <div className="space-y-5">
            <MeterChart
              data={waterHistory || []}
              title="Water Usage"
              color="#3b82f6"
              unit="L"
            />
            <MeterChart
              data={electricHistory || []}
              title="Electric Usage"
              color="#eab308"
              unit="kWh"
            />
            <MeterChart
              data={gasHistory || []}
              title="Gas Usage"
              color="#f97316"
              unit="m³"
            />
          </div>
        </section>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-slate-300/50 dark:border-slate-700/50">
          <div className="text-center space-y-2">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Last updated: {formatWithTimezone(lastUpdate)}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-500">
              {userTimezone} ({timezoneAbbr}) • {utcOffset}
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-600 mt-3">
              Powered by Claude Vision AI • Flask • React
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
