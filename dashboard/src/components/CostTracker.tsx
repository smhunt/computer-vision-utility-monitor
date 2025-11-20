import { DollarSign } from 'lucide-react';
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
    <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <DollarSign className="w-6 h-6 text-green-600" />
        <h2 className="text-xl font-semibold text-neutral-800">Cost Tracking</h2>
      </div>

      {/* Total Costs */}
      <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-neutral-50 rounded-lg">
        <div>
          <p className="text-sm text-neutral-600 mb-1">Daily Total</p>
          <p className="text-2xl font-bold text-neutral-900">
            ${totalDaily.toFixed(2)}
            <span className="text-sm font-normal text-neutral-500 ml-1">{currency}</span>
          </p>
        </div>
        <div>
          <p className="text-sm text-neutral-600 mb-1">Monthly Estimate</p>
          <p className="text-2xl font-bold text-neutral-900">
            ${totalMonthly.toFixed(2)}
            <span className="text-sm font-normal text-neutral-500 ml-1">{currency}</span>
          </p>
        </div>
      </div>

      {/* Individual Meter Costs */}
      <div className="space-y-3">
        {costs.map((cost) => (
          <div key={cost.meterType} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className={`font-semibold ${meterColors[cost.meterType]}`}>
                {meterLabels[cost.meterType]}
              </div>
            </div>
            <div className="flex gap-6 text-sm">
              <div>
                <span className="text-neutral-600">Daily: </span>
                <span className="font-semibold text-neutral-900">${cost.dailyCost.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-neutral-600">Monthly: </span>
                <span className="font-semibold text-neutral-900">${cost.monthlyCost.toFixed(2)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Note */}
      <p className="text-xs text-neutral-500 mt-4 italic">
        * Monthly estimates are based on current daily usage patterns
      </p>
    </div>
  );
}
