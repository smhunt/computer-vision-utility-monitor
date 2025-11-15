import { Droplets, Zap, Flame, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { MeterData } from '../types/meter';

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
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`${config.color} p-3 rounded-lg`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">{config.label}</h3>
            <p className="text-xs text-gray-500">Last updated: {new Date(data.lastUpdated).toLocaleTimeString()}</p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${confidenceBadgeColors[data.confidence]}`}>
          {data.confidence}
        </span>
      </div>

      {/* Current Reading */}
      <div className="mb-4">
        <div className="text-3xl font-bold text-gray-900">
          {data.current.toLocaleString()}
          <span className="text-lg font-normal text-gray-500 ml-2">{data.unit}</span>
        </div>
      </div>

      {/* 24h Change */}
      <div className="flex items-center gap-2">
        <TrendIcon className={`w-4 h-4 ${data.trend === 'up' ? 'text-red-500' : data.trend === 'down' ? 'text-green-500' : 'text-gray-400'}`} />
        <span className="text-sm text-gray-600">
          <span className={`font-semibold ${data.trend === 'up' ? 'text-red-600' : data.trend === 'down' ? 'text-green-600' : 'text-gray-600'}`}>
            {Math.abs(data.change24h).toFixed(2)} {data.unit}
          </span>
          <span className="ml-1">in last 24h</span>
        </span>
      </div>
    </div>
  );
}
