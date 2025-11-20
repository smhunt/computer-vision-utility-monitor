export interface MeterReading {
  time: string;
  value: number;
  confidence: 'high' | 'medium' | 'low';
  meterType: 'water' | 'electric' | 'gas';
}

// Meter data interface for display
export interface MeterData {
  current: number;
  unit: string;
  lastUpdated: string;
  confidence: 'high' | 'medium' | 'low';
  change24h: number;
  trend: 'up' | 'down' | 'stable';
}

export interface MeterStats {
  water: MeterData;
  electric: MeterData;
  gas: MeterData;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
}

export interface CostData {
  meterType: 'water' | 'electric' | 'gas';
  dailyCost: number;
  monthlyCost: number;
  currency: string;
}
