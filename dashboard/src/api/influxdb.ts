import axios from 'axios';
import { MeterReading, ChartDataPoint } from '../types/meter';

// Use proxy in development to avoid CORS issues
const INFLUXDB_URL = import.meta.env.DEV ? '/influxdb' : (import.meta.env.VITE_INFLUXDB_URL || 'http://localhost:8086');
const INFLUXDB_TOKEN = import.meta.env.VITE_INFLUXDB_TOKEN || '';
const INFLUXDB_ORG = import.meta.env.VITE_INFLUXDB_ORG || 'ecoworks';
const INFLUXDB_BUCKET = import.meta.env.VITE_INFLUXDB_BUCKET || 'utility_meters';

const api = axios.create({
  baseURL: INFLUXDB_URL,
  headers: {
    'Authorization': `Token ${INFLUXDB_TOKEN}`,
    'Content-Type': 'application/json',
    'Accept': 'application/csv',
  },
  timeout: 5000,
});

export interface InfluxDBQueryParams {
  meterType: 'water' | 'electric' | 'gas';
  range?: string; // e.g., '-1h', '-24h', '-7d'
  limit?: number;
}

export const fetchMeterReadings = async (params: InfluxDBQueryParams): Promise<MeterReading[]> => {
  const { meterType, range = '-24h', limit = 100 } = params;

  const fluxQuery = `
    from(bucket: "${INFLUXDB_BUCKET}")
      |> range(start: ${range})
      |> filter(fn: (r) => r["_measurement"] == "meter_reading")
      |> filter(fn: (r) => r["meter_type"] == "${meterType}")
      |> filter(fn: (r) => r["_field"] == "value" or r["_field"] == "confidence")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: ${limit})
  `;

  try {
    console.log(`Fetching ${meterType} readings from InfluxDB...`);
    const response = await api.post(
      `/api/v2/query?org=${INFLUXDB_ORG}`,
      fluxQuery,
      {
        headers: {
          'Content-Type': 'application/vnd.flux',
          'Accept': 'application/csv',
        },
      }
    );

    // Parse InfluxDB response
    const data = response.data;
    const readings: MeterReading[] = [];

    // InfluxDB returns CSV format by default
    if (typeof data === 'string') {
      const lines = data.split('\n').filter(line => line && !line.startsWith('#'));
      const headers = lines[0]?.split(',') || [];

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',');
        const reading: any = {};

        headers.forEach((header, index) => {
          reading[header.trim()] = values[index]?.trim();
        });

        if (reading._time && reading.value) {
          readings.push({
            time: reading._time,
            value: parseFloat(reading.value),
            confidence: reading.confidence || 'medium',
            meterType: meterType,
          });
        }
      }
    }

    console.log(`✓ Fetched ${readings.length} ${meterType} readings from InfluxDB`);
    return readings;
  } catch (error: any) {
    console.warn(`Failed to fetch ${meterType} from InfluxDB:`, error.message);
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
