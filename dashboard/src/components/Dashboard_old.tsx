import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, RefreshCw, Play, Pause } from 'lucide-react';
import { MeterCard } from './MeterCard';
import { MeterChart } from './MeterChart';
import { CostTracker } from './CostTracker';
import { ThemeToggle } from './ThemeToggle';
import { fetchLatestReading, fetchHistoricalData, fetchMeterConfig, fetchPricingConfig } from '../api/influxdb';
import type { MeterData, CostData, PricingConfig } from '../types/meter';
import { getUserTimezone, getTimezoneAbbreviation, getUTCOffset, formatWithTimezone } from '../utils/timezone';

// Calculate cost rate for a meter type from pricing configuration
const calculateCostRate = (meterType: 'water' | 'electric' | 'gas', pricing: PricingConfig | null): number => {
  if (!pricing) {
    // Fallback rates if pricing not loaded
    return meterType === 'water' ? 0.0013 : meterType === 'electric' ? 0.12 : 0.30;
  }

  try {
    if (meterType === 'water' && pricing.water) {
      // Water rate: water + wastewater + stormwater (per m³)
      const { water, wastewater, stormwater } = pricing.water.volumetric_rate;
      return water + wastewater + stormwater;
    }

    if (meterType === 'electric' && pricing.electricity) {
      // Electricity: Use average of TOU rates + delivery charges (convert cents to dollars)
      const { off_peak, mid_peak, on_peak } = pricing.electricity.time_of_use_rates;
      const avgEnergyRate = (off_peak.rate + mid_peak.rate + on_peak.rate) / 3 / 100; // cents to dollars
      const deliveryRate = (
        pricing.electricity.delivery_charges.distribution_volumetric_charge +
        pricing.electricity.delivery_charges.transmission_charge
      ) / 100; // cents to dollars
      return avgEnergyRate + deliveryRate;
    }

    if (meterType === 'gas' && pricing.natural_gas) {
      // Gas: supply + delivery + transportation + carbon (convert cents to dollars)
      const supply = pricing.natural_gas.gas_supply.total_effective_rate / 100;
      const delivery = pricing.natural_gas.delivery_charges.volumetric_charge / 100;
      const transport = pricing.natural_gas.transportation_charges.volumetric_charge / 100;
      const carbon = (
        pricing.natural_gas.carbon_charges.federal_carbon_charge.rate +
        pricing.natural_gas.carbon_charges.facility_carbon_charge.rate
      ) / 100;
      return supply + delivery + transport + carbon;
    }
  } catch (error) {
    console.warn(`Error calculating cost rate for ${meterType}:`, error);
  }

  // Fallback rates
  return meterType === 'water' ? 0.0013 : meterType === 'electric' ? 0.12 : 0.30;
};

export function Dashboard() {
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(() => {
    const stored = localStorage.getItem('auto-refresh-enabled');
    return stored === null ? true : stored === 'true'; // Default to true
  });

  // Save auto-refresh preference to localStorage
  useEffect(() => {
    localStorage.setItem('auto-refresh-enabled', autoRefreshEnabled.toString());
  }, [autoRefreshEnabled]);

  // Fetch meter configuration (will be used when dashboard becomes dynamic)
  const { data: _meterConfigs } = useQuery({
    queryKey: ['config', 'meters'],
    queryFn: fetchMeterConfig,
  });

  // Fetch pricing configuration
  const { data: pricingData } = useQuery({
    queryKey: ['config', 'pricing'],
    queryFn: fetchPricingConfig,
  });

  const pricing = pricingData?.pricing || null;

  // Fetch latest readings for all meters
  const { data: waterReading, refetch: refetchWater } = useQuery({
    queryKey: ['meter', 'water'],
    queryFn: () => fetchLatestReading('water'),
    refetchInterval: autoRefreshEnabled ? 60000 : false, // Refetch every minute if enabled
  });

  const { data: electricReading, refetch: refetchElectric } = useQuery({
    queryKey: ['meter', 'electric'],
    queryFn: () => fetchLatestReading('electric'),
    refetchInterval: autoRefreshEnabled ? 60000 : false,
  });

  const { data: gasReading, refetch: refetchGas } = useQuery({
    queryKey: ['meter', 'gas'],
    queryFn: () => fetchLatestReading('gas'),
    refetchInterval: autoRefreshEnabled ? 60000 : false,
  });

  // Fetch historical data for charts
  const { data: waterHistory, refetch: refetchWaterHistory } = useQuery({
    queryKey: ['history', 'water'],
    queryFn: () => fetchHistoricalData('water', '-7d'),
    refetchInterval: autoRefreshEnabled ? 300000 : false, // Refetch every 5 minutes if enabled
  });

  const { data: electricHistory, refetch: refetchElectricHistory } = useQuery({
    queryKey: ['history', 'electric'],
    queryFn: () => fetchHistoricalData('electric', '-7d'),
    refetchInterval: autoRefreshEnabled ? 300000 : false,
  });

  const { data: gasHistory, refetch: refetchGasHistory } = useQuery({
    queryKey: ['history', 'gas'],
    queryFn: () => fetchHistoricalData('gas', '-7d'),
    refetchInterval: autoRefreshEnabled ? 300000 : false,
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

  // Calculate costs using data-driven pricing
  const costs: CostData[] = [
    {
      meterType: 'water',
      dailyCost: waterData.change24h * calculateCostRate('water', pricing),
      monthlyCost: waterData.change24h * calculateCostRate('water', pricing) * 30,
      currency: pricing?.metadata?.currency || 'CAD',
    },
    {
      meterType: 'electric',
      dailyCost: electricData.change24h * calculateCostRate('electric', pricing),
      monthlyCost: electricData.change24h * calculateCostRate('electric', pricing) * 30,
      currency: pricing?.metadata?.currency || 'CAD',
    },
    {
      meterType: 'gas',
      dailyCost: gasData.change24h * calculateCostRate('gas', pricing),
      monthlyCost: gasData.change24h * calculateCostRate('gas', pricing) * 30,
      currency: pricing?.metadata?.currency || 'CAD',
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
                onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-all ${
                  autoRefreshEnabled
                    ? 'bg-green-600 hover:bg-green-500 text-white shadow-lg shadow-green-900/30'
                    : 'bg-slate-300 hover:bg-slate-400 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300'
                }`}
                title={autoRefreshEnabled ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
              >
                {autoRefreshEnabled ? (
                  <>
                    <Pause className="w-4 h-4" />
                    <span className="hidden sm:inline">Auto</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    <span className="hidden sm:inline">Manual</span>
                  </>
                )}
              </button>
              <button
                onClick={handleRefresh}
                className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-all shadow-lg shadow-blue-900/30"
              >
                <RefreshCw className="w-4 h-4" />
                <span className="hidden sm:inline">Refresh</span>
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
