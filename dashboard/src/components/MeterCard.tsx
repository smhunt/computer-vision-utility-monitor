import { Droplets, Zap, Flame, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { MeterData } from '../types/meter';
import { formatInLocalTimezone } from '../utils/timezone';

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

const confidenceBadgeColors = {
  high: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-red-100 text-red-800',
};

export function MeterCard({ type, data }: MeterCardProps) {
  const config = meterConfig[type];
  const Icon = config.icon;

  const TrendIcon = data.trend === 'up' ? TrendingUp : data.trend === 'down' ? TrendingDown : Minus;

  return (
    <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-2xl border border-slate-300/50 dark:border-slate-700/50 p-6 hover:bg-white/80 dark:hover:bg-slate-800/80 hover:border-slate-400/50 dark:hover:border-slate-600/50 transition-all duration-200 shadow-xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className={`${config.color} p-2.5 rounded-xl shadow-lg`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">{config.label}</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              {formatInLocalTimezone(data.lastUpdated, { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </p>
          </div>
        </div>
        <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${confidenceBadgeColors[data.confidence]}`}>
          {data.confidence}
        </span>
      </div>

      {/* Current Reading */}
      <div className="mb-5">
        <div className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
          {data.current.toLocaleString()}
          <span className="text-base font-normal text-slate-600 dark:text-slate-400 ml-2">{data.unit}</span>
        </div>
      </div>

      {/* 24h Change */}
      <div className="flex items-center gap-2 pt-4 border-t border-slate-300/50 dark:border-slate-700/50">
        <TrendIcon className={`w-4 h-4 ${data.trend === 'up' ? 'text-red-400' : data.trend === 'down' ? 'text-green-400' : 'text-slate-500'}`} />
        <span className="text-sm text-slate-700 dark:text-slate-300">
          <span className={`font-semibold ${data.trend === 'up' ? 'text-red-400' : data.trend === 'down' ? 'text-green-400' : 'text-slate-700 dark:text-slate-300'}`}>
            {Math.abs(data.change24h).toFixed(2)} {data.unit}
          </span>
          <span className="ml-1 text-slate-600 dark:text-slate-400">in last 24h</span>
        </span>
      </div>
    </div>
  );
}
