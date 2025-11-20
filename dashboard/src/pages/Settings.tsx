import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Settings as SettingsIcon, FileCode } from 'lucide-react';
import { fetchMeterConfig, fetchPricingConfig } from '../api/influxdb';
import type { MeterConfig } from '../types/meter';

export function Settings() {
  const { data: meterConfigs, isLoading: metersLoading } = useQuery({
    queryKey: ['config', 'meters'],
    queryFn: fetchMeterConfig,
  });

  const { data: pricingData, isLoading: pricingLoading } = useQuery({
    queryKey: ['config', 'pricing'],
    queryFn: fetchPricingConfig,
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Header */}
      <header className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-b border-slate-300/50 dark:border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <a
                href="/"
                className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </a>
              <div className="p-2.5 bg-purple-500/20 rounded-xl border border-purple-500/30">
                <SettingsIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Settings</h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">Manage your meter and pricing configuration</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8">

        {/* Configuration Files Info */}
        <section className="mb-8">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <FileCode className="w-6 h-6 text-blue-600 dark:text-blue-400 mt-1" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">Configuration Files</h3>
                <p className="text-sm text-blue-800 dark:text-blue-300 mb-4">
                  Your system is configured through two files. You can edit these files using the configuration editor:
                </p>
                <div className="space-y-2 mb-4">
                  <div className="bg-white/50 dark:bg-slate-800/50 rounded-lg p-3">
                    <code className="text-sm font-mono text-purple-600 dark:text-purple-400">config/meters.yaml</code>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Meter hardware configuration (cameras, intervals, etc.)</p>
                  </div>
                  <div className="bg-white/50 dark:bg-slate-800/50 rounded-lg p-3">
                    <code className="text-sm font-mono text-purple-600 dark:text-purple-400">config/pricing.json</code>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Utility pricing rates and household information</p>
                  </div>
                </div>
                <a
                  href="/config"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  <FileCode className="w-4 h-4" />
                  Edit Configuration
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Meters Configuration */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
            <div className="w-1 h-5 bg-blue-500 rounded-full"></div>
            Configured Meters
          </h2>

          {metersLoading ? (
            <div className="text-center py-8 text-slate-500">Loading meters...</div>
          ) : meterConfigs && meterConfigs.length > 0 ? (
            <div className="grid gap-4">
              {meterConfigs.map((meter: MeterConfig) => (
                <div
                  key={meter.name}
                  className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <div
                          className="w-12 h-12 rounded-xl flex items-center justify-center"
                          style={{ backgroundColor: meter.display.color + '20', borderColor: meter.display.color + '40', borderWidth: '1px' }}
                        >
                          <span className="text-2xl">{meter.display.icon === 'droplets' ? '💧' : meter.display.icon === 'zap' ? '⚡' : '🔥'}</span>
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{meter.display.label}</h3>
                          <p className="text-sm text-slate-600 dark:text-slate-400">{meter.name}</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-slate-500 dark:text-slate-400">Camera IP:</span>
                          <span className="ml-2 font-mono text-slate-900 dark:text-white">{meter.camera_ip}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 dark:text-slate-400">Reading Interval:</span>
                          <span className="ml-2 text-slate-900 dark:text-white">{meter.reading_interval}s</span>
                        </div>
                        <div>
                          <span className="text-slate-500 dark:text-slate-400">Unit:</span>
                          <span className="ml-2 text-slate-900 dark:text-white">{meter.display.unit}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 dark:text-slate-400">Type:</span>
                          <span className="ml-2 text-slate-900 dark:text-white capitalize">{meter.type}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">No meters configured</div>
          )}
        </section>

        {/* Pricing Configuration */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
            <div className="w-1 h-5 bg-green-500 rounded-full"></div>
            Pricing Configuration
          </h2>

          {pricingLoading ? (
            <div className="text-center py-8 text-slate-500">Loading pricing...</div>
          ) : pricingData?.pricing ? (
            <div className="space-y-4">
              {/* Metadata */}
              <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
                <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Location & Currency</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Location:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">{pricingData.pricing.metadata.location}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Currency:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">{pricingData.pricing.metadata.currency}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Effective Date:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">{pricingData.pricing.metadata.effective_date}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 dark:text-slate-400">Last Updated:</span>
                    <span className="ml-2 text-slate-900 dark:text-white">{pricingData.pricing.metadata.last_updated}</span>
                  </div>
                </div>
              </div>

              {/* Water Pricing */}
              {pricingData.pricing.water && (
                <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">💧 Water - {pricingData.pricing.water.provider}</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Water Rate:</span>
                      <span className="font-semibold">${pricingData.pricing.water.volumetric_rate.water.toFixed(2)}/m³</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Wastewater Rate:</span>
                      <span className="font-semibold">${pricingData.pricing.water.volumetric_rate.wastewater.toFixed(2)}/m³</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Stormwater Rate:</span>
                      <span className="font-semibold">${pricingData.pricing.water.volumetric_rate.stormwater.toFixed(2)}/m³</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-slate-200 dark:border-slate-700">
                      <span className="text-slate-600 dark:text-slate-400">Monthly Service Charge:</span>
                      <span className="font-semibold">${pricingData.pricing.water.fixed_charges.monthly_service_charge.toFixed(2)}/month</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Electricity Pricing */}
              {pricingData.pricing.electricity && (
                <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">⚡ Electricity - {pricingData.pricing.electricity.provider}</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Off-Peak Rate:</span>
                      <span className="font-semibold">{pricingData.pricing.electricity.time_of_use_rates.off_peak.rate}¢/kWh</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Mid-Peak Rate:</span>
                      <span className="font-semibold">{pricingData.pricing.electricity.time_of_use_rates.mid_peak.rate}¢/kWh</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">On-Peak Rate:</span>
                      <span className="font-semibold">{pricingData.pricing.electricity.time_of_use_rates.on_peak.rate}¢/kWh</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-slate-200 dark:border-slate-700">
                      <span className="text-slate-600 dark:text-slate-400">Monthly Service Charge:</span>
                      <span className="font-semibold">${pricingData.pricing.electricity.delivery_charges.monthly_service_charge.toFixed(2)}/month</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Gas Pricing */}
              {pricingData.pricing.natural_gas && (
                <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">🔥 Natural Gas - {pricingData.pricing.natural_gas.provider}</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Gas Supply Rate:</span>
                      <span className="font-semibold">{pricingData.pricing.natural_gas.gas_supply.total_effective_rate.toFixed(2)}¢/m³</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Delivery Charge:</span>
                      <span className="font-semibold">{pricingData.pricing.natural_gas.delivery_charges.volumetric_charge.toFixed(2)}¢/m³</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600 dark:text-slate-400">Transportation Charge:</span>
                      <span className="font-semibold">{pricingData.pricing.natural_gas.transportation_charges.volumetric_charge.toFixed(2)}¢/m³</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-slate-200 dark:border-slate-700">
                      <span className="text-slate-600 dark:text-slate-400">Monthly Customer Charge:</span>
                      <span className="font-semibold">${pricingData.pricing.natural_gas.fixed_charges.monthly_customer_charge.toFixed(2)}/month</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">No pricing configuration found</div>
          )}
        </section>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-slate-300/50 dark:border-slate-700/50">
          <p className="text-sm text-center text-slate-600 dark:text-slate-400">
            To modify these settings, edit the configuration files directly in your code editor
          </p>
        </footer>
      </main>
    </div>
  );
}
