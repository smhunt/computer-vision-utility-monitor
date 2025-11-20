import type { CostData } from '../types/meter';

interface CostTrackerProps {
  costs: CostData[];
}

const meterColors = {
  water: 'text-blue-600',
  electric: 'text-yellow-600',
  gas: 'text-orange-600',
};

const meterLabels = {
  water: 'Water',
  electric: 'Electric',
  gas: 'Gas',
};

export function CostTracker({ costs }: CostTrackerProps) {
  const totalDaily = costs.reduce((sum, cost) => sum + cost.dailyCost, 0);
  const totalMonthly = costs.reduce((sum, cost) => sum + cost.monthlyCost, 0);
  const currency = costs[0]?.currency || 'USD';

  return (
    <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-2xl border border-slate-300/50 dark:border-slate-700/50 p-7 shadow-xl">
      {/* Total Costs */}
      <div className="grid grid-cols-2 gap-6 mb-8 pb-8 border-b border-slate-300/50 dark:border-slate-700/50">
        <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-xl p-5 border border-green-500/20">
          <p className="text-sm font-medium text-green-700 dark:text-green-300 mb-2">Daily Total</p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            ${totalDaily.toFixed(2)}
            <span className="text-base font-normal text-slate-600 dark:text-slate-400 ml-2">{currency}</span>
          </p>
        </div>
        <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-xl p-5 border border-blue-500/20">
          <p className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">Monthly Estimate</p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
            ${totalMonthly.toFixed(2)}
            <span className="text-base font-normal text-slate-600 dark:text-slate-400 ml-2">{currency}</span>
          </p>
        </div>
      </div>

      {/* Individual Meter Costs */}
      <div className="space-y-3">
        {costs.map((cost) => (
          <div key={cost.meterType} className="flex items-center justify-between py-3 px-4 bg-slate-200/30 dark:bg-slate-700/30 rounded-lg">
            <div className="flex items-center gap-3">
              <div className={`text-sm font-semibold ${meterColors[cost.meterType]}`}>
                {meterLabels[cost.meterType]}
              </div>
            </div>
            <div className="flex gap-8 text-sm">
              <div>
                <span className="text-slate-600 dark:text-slate-400">Daily: </span>
                <span className="font-semibold text-slate-900 dark:text-white">${cost.dailyCost.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-slate-600 dark:text-slate-400">Monthly: </span>
                <span className="font-semibold text-slate-900 dark:text-white">${cost.monthlyCost.toFixed(2)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Note */}
      <p className="text-xs text-slate-500 dark:text-slate-500 mt-6 pt-4 border-t border-slate-300/50 dark:border-slate-700/50">
        * Monthly estimates based on current daily usage patterns
      </p>
    </div>
  );
}
