import axios from 'axios';
import type { MeterReading, ChartDataPoint, MeterConfig, PricingConfig, HouseholdConfig } from '../types/meter';

// Use Flask backend API instead of InfluxDB
const FLASK_API_URL = import.meta.env.VITE_FLASK_API_URL || 'http://127.0.0.1:2500';

const api = axios.create({
  baseURL: FLASK_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export interface InfluxDBQueryParams {
  meterType: 'water' | 'electric' | 'gas';
  range?: string; // e.g., '-1h', '-24h', '-7d'
  limit?: number;
}

export const fetchMeterReadings = async (params: InfluxDBQueryParams): Promise<MeterReading[]> => {
  const { meterType, range = '-24h' } = params;

  try {
    console.log(`Fetching ${meterType} readings from Flask backend...`);

    // Map range to Flask API format
    const period = range.replace('-', '').replace('h', 'h').replace('d', 'd');

    // Fetch from Flask /api/consumption endpoint
    const response = await api.get(`/api/consumption/${meterType}`, {
      params: {
        period,
        interval: 'hour'
      }
    });

    const data = response.data;

    if (data.status !== 'success' || !data.consumption) {
      throw new Error('Invalid response from Flask API');
    }

    // Convert Flask consumption data to MeterReading format
    const readings: MeterReading[] = [];
    const now = new Date();

    for (let i = 0; i < data.consumption.length; i++) {
      const hoursAgo = data.consumption.length - i;
      const timestamp = new Date(now.getTime() - hoursAgo * 3600000);

      readings.push({
        time: timestamp.toISOString(),
        value: data.consumption[i],
        confidence: 'high',
        meterType: meterType,
      });
    }

    console.log(`✓ Fetched ${readings.length} ${meterType} readings from Flask backend`);
    return readings;
  } catch (error: any) {
    console.warn(`Failed to fetch ${meterType} from Flask backend:`, error.message);
    console.log(`Using mock data for ${meterType} meter`);
    // Return mock data for development
    return generateMockData(meterType);
  }
};

export const fetchLatestReading = async (meterType: 'water' | 'electric' | 'gas'): Promise<MeterReading | null> => {
  const readings = await fetchMeterReadings({ meterType, range: '-1h', limit: 1 });
  return readings[0] || null;
};

export const fetchHistoricalData = async (
  meterType: 'water' | 'electric' | 'gas',
  range: string = '-7d'
): Promise<ChartDataPoint[]> => {
  const readings = await fetchMeterReadings({ meterType, range, limit: 1000 });

  return readings.map(reading => ({
    timestamp: reading.time,
    value: reading.value,
  }));
};

// Mock data generator for development/testing
function generateMockData(meterType: 'water' | 'electric' | 'gas'): MeterReading[] {
  const now = new Date();
  const readings: MeterReading[] = [];
  const baseValue = meterType === 'water' ? 1250000 : meterType === 'electric' ? 45000 : 12000;

  for (let i = 0; i < 24; i++) {
    const time = new Date(now.getTime() - i * 3600000);
    const randomVariation = Math.random() * 100 - 50;

    readings.push({
      time: time.toISOString(),
      value: baseValue + randomVariation * i,
      confidence: i % 3 === 0 ? 'high' : i % 3 === 1 ? 'medium' : 'low',
      meterType,
    });
  }

  return readings.reverse();
}

// Fetch meter configuration
export const fetchMeterConfig = async (): Promise<MeterConfig[]> => {
  try {
    console.log('Fetching meter configuration from Flask backend...');
    const response = await api.get('/api/config/meters');

    if (response.data.status === 'success') {
      console.log(`✓ Fetched configuration for ${response.data.meters.length} meters`);
      return response.data.meters;
    }

    throw new Error('Failed to fetch meter configuration');
  } catch (error: any) {
    console.warn('Failed to fetch meter configuration:', error.message);
    return [];
  }
};

// Fetch pricing configuration
export const fetchPricingConfig = async (): Promise<{
  pricing: PricingConfig;
  household: HouseholdConfig;
  metadata: any;
} | null> => {
  try {
    console.log('Fetching pricing configuration from Flask backend...');
    const response = await api.get('/api/config/pricing');

    if (response.data.status === 'success') {
      console.log('✓ Fetched pricing configuration');
      return {
        pricing: response.data.pricing,
        household: response.data.household,
        metadata: response.data.metadata
      };
    }

    throw new Error('Failed to fetch pricing configuration');
  } catch (error: any) {
    console.warn('Failed to fetch pricing configuration:', error.message);
    return null;
  }
};
