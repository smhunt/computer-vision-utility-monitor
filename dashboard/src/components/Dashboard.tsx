import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, RefreshCw } from 'lucide-react';
import { MeterCard } from './MeterCard';
import { MeterChart } from './MeterChart';
import { CostTracker } from './CostTracker';
import { fetchLatestReading, fetchHistoricalData } from '../api/influxdb';
import type { MeterData, CostData } from '../types/meter';
import { getUserTimezone, getTimezoneAbbreviation, getUTCOffset, formatWithTimezone } from '../utils/timezone';

// Cost rates (configurable)
const COST_RATES = {
  water: 0.005, // per gallon
  electric: 0.12, // per kWh
  gas: 0.85, // per CCF
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

  const waterData = calculateMeterData(waterReading, waterHistory || [], 'gal');
  const electricData = calculateMeterData(electricReading, electricHistory || [], 'kWh');
  const gasData = calculateMeterData(gasReading, gasHistory || [], 'CCF');

  // Calculate costs
  const costs: CostData[] = [
    {
      meterType: 'water',
      dailyCost: waterData.change24h * COST_RATES.water,
      monthlyCost: waterData.change24h * COST_RATES.water * 30,
      currency: 'USD',
    },
    {
      meterType: 'electric',
      dailyCost: electricData.change24h * COST_RATES.electric,
      monthlyCost: electricData.change24h * COST_RATES.electric * 30,
      currency: 'USD',
    },
    {
      meterType: 'gas',
      dailyCost: gasData.change24h * COST_RATES.gas,
      monthlyCost: gasData.change24h * COST_RATES.gas * 30,
      currency: 'USD',
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
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8 text-neutral-700" />
              <div>
                <h1 className="text-2xl font-semibold text-neutral-900">Utility Monitor Dashboard</h1>
                <p className="text-sm text-neutral-600">Real-time meter readings with AI vision</p>
              </div>
            </div>
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 px-4 py-2 bg-neutral-800 text-white rounded-md hover:bg-neutral-900 transition-colors shadow-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Meter Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <MeterCard type="water" data={waterData} />
          <MeterCard type="electric" data={electricData} />
          <MeterCard type="gas" data={gasData} />
        </div>

        {/* Cost Tracker */}
        <div className="mb-8">
          <CostTracker costs={costs} />
        </div>

        {/* Charts */}
        <div className="space-y-6">
          <MeterChart
            data={waterHistory || []}
            title="Water Usage (7 Days)"
            color="#3b82f6"
            unit="gal"
          />
          <MeterChart
            data={electricHistory || []}
            title="Electric Usage (7 Days)"
            color="#eab308"
            unit="kWh"
          />
          <MeterChart
            data={gasHistory || []}
            title="Gas Usage (7 Days)"
            color="#f97316"
            unit="CCF"
          />
        </div>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-neutral-200">
          <div className="text-center text-sm text-neutral-500 space-y-2">
            <p className="font-medium">Last updated: {formatWithTimezone(lastUpdate)}</p>
            <p>Timezone: {userTimezone} ({timezoneAbbr}) • {utcOffset}</p>
            <p className="text-xs text-neutral-400 mt-3">
              Powered by Claude Vision AI • InfluxDB • Grafana
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
