import { Droplets, Zap, Flame, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { MeterData } from '../types/meter';
import { formatInLocalTimezone } from '../utils/timezone';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

interface MeterCardProps {
  type: 'water' | 'electric' | 'gas';
  data: MeterData;
}

const meterConfig = {
  water: {
    icon: Droplets,
    label: 'Water Meter',
    color: 'bg-blue-500',
    lightColor: 'bg-blue-50',
    textColor: 'text-blue-600',
  },
  electric: {
    icon: Zap,
    label: 'Electric Meter',
    color: 'bg-yellow-500',
    lightColor: 'bg-yellow-50',
    textColor: 'text-yellow-600',
  },
  gas: {
    icon: Flame,
    label: 'Gas Meter',
    color: 'bg-orange-500',
    lightColor: 'bg-orange-50',
    textColor: 'text-orange-600',
  },
};

const confidenceBadgeVariant = {
  high: 'default' as const,
  medium: 'secondary' as const,
  low: 'destructive' as const,
};

export function MeterCard({ type, data }: MeterCardProps) {
  const config = meterConfig[type];
  const Icon = config.icon;

  const TrendIcon = data.trend === 'up' ? TrendingUp : data.trend === 'down' ? TrendingDown : Minus;

  return (
    <Card className="hover:shadow-lg transition-all duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`${config.color} p-2.5 rounded-xl shadow-lg`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-base">{config.label}</CardTitle>
              <CardDescription className="text-xs mt-1">
                {formatInLocalTimezone(data.lastUpdated, { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </CardDescription>
            </div>
          </div>
          <Badge variant={confidenceBadgeVariant[data.confidence]}>
            {data.confidence}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {/* Current Reading */}
        <div className="mb-5">
          <div className="text-3xl font-bold tracking-tight">
            {data.current.toLocaleString()}
            <span className="text-base font-normal text-muted-foreground ml-2">{data.unit}</span>
          </div>
        </div>

        {/* 24h Change */}
        <div className="flex items-center gap-2 pt-4 border-t">
          <TrendIcon className={`w-4 h-4 ${data.trend === 'up' ? 'text-red-500' : data.trend === 'down' ? 'text-green-500' : 'text-muted-foreground'}`} />
          <span className="text-sm">
            <span className={`font-semibold ${data.trend === 'up' ? 'text-red-500' : data.trend === 'down' ? 'text-green-500' : ''}`}>
              {Math.abs(data.change24h).toFixed(2)} {data.unit}
            </span>
            <span className="ml-1 text-muted-foreground">in last 24h</span>
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
