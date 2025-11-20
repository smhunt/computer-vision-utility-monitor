import type { CostData } from '../types/meter';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Separator } from './ui/separator';

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
    <Card>
      <CardContent className="pt-6">
        {/* Total Costs */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-green-700 dark:text-green-300">
                Daily Total
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold tracking-tight">
                ${totalDaily.toFixed(2)}
                <span className="text-base font-normal text-muted-foreground ml-2">{currency}</span>
              </p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-blue-700 dark:text-blue-300">
                Monthly Estimate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold tracking-tight">
                ${totalMonthly.toFixed(2)}
                <span className="text-base font-normal text-muted-foreground ml-2">{currency}</span>
              </p>
            </CardContent>
          </Card>
        </div>

        <Separator className="my-6" />

        {/* Individual Meter Costs */}
        <div className="space-y-3">
          {costs.map((cost) => (
            <div key={cost.meterType} className="flex items-center justify-between py-3 px-4 bg-secondary/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className={`text-sm font-semibold ${meterColors[cost.meterType]}`}>
                  {meterLabels[cost.meterType]}
                </div>
              </div>
              <div className="flex gap-8 text-sm">
                <div>
                  <span className="text-muted-foreground">Daily: </span>
                  <span className="font-semibold">${cost.dailyCost.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Monthly: </span>
                  <span className="font-semibold">${cost.monthlyCost.toFixed(2)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <Separator className="my-4" />

        {/* Note */}
        <p className="text-xs text-muted-foreground">
          * Monthly estimates based on current daily usage patterns
        </p>
      </CardContent>
    </Card>
  );
}
