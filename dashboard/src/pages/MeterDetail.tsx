import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Activity, Image as ImageIcon, Camera } from 'lucide-react';
import type { MeterConfig } from '../types/meter';
import { fetchMeterConfig } from '../api/influxdb';
import axios from 'axios';

const FLASK_API_URL = import.meta.env.VITE_FLASK_API_URL || 'http://127.0.0.1:2500';

interface Snapshot {
  snapshot: {
    filename: string;
    timestamp: string;
    path: string;
  };
  meter_reading: {
    digital_reading?: number;
    black_digit?: number;
    dial_reading?: number;
    total_reading?: number;
    confidence?: string;
    notes?: string;
  };
  camera?: {
    source_file: string;
    model: string;
    ip: string;
  };
  image_url: string;
  reanalyzed?: boolean;
  reanalyzed_at?: string;
}

export function MeterDetail() {
  const { meterName } = useParams<{ meterName: string }>();
  const navigate = useNavigate();

  const { data: meterConfigs, isLoading: metersLoading } = useQuery({
    queryKey: ['config', 'meters'],
    queryFn: fetchMeterConfig,
  });

  const { data: snapshotsData, isLoading: snapshotsLoading } = useQuery({
    queryKey: ['snapshots', meterName],
    queryFn: async () => {
      const response = await axios.get(`${FLASK_API_URL}/api/snapshots/${meterName}`);
      return response.data;
    },
    enabled: !!meterName,
  });

  const currentMeter = meterConfigs?.find((m: MeterConfig) => m.name === meterName);
  const snapshots: Snapshot[] = snapshotsData?.snapshots || [];

  const formatTimestamp = (isoTimestamp: string) => {
    try {
      const dt = new Date(isoTimestamp);
      return dt.toLocaleString();
    } catch {
      return isoTimestamp;
    }
  };

  if (metersLoading || snapshotsLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading meter data...</p>
        </div>
      </div>
    );
  }

  if (!currentMeter) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-600 dark:text-slate-400 text-lg mb-4">Meter not found</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Header */}
      <header className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-b border-slate-300/50 dark:border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div
                className="p-2.5 rounded-xl border"
                style={{
                  backgroundColor: currentMeter.display.color + '20',
                  borderColor: currentMeter.display.color + '40',
                }}
              >
                <Activity className="w-6 h-6" style={{ color: currentMeter.display.color }} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  {currentMeter.display.label}
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                  Historical readings and snapshots
                </p>
              </div>
            </div>
            <button
              onClick={() => navigate(`/camera/${currentMeter.type}`)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Camera className="w-5 h-5" />
              Camera Preview
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8">
        {/* Meter Info */}
        <section className="mb-8">
          <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Meter Information</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Camera IP</p>
                <p className="text-base font-semibold text-slate-900 dark:text-white font-mono">
                  {currentMeter.camera_ip}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Reading Interval</p>
                <p className="text-base font-semibold text-slate-900 dark:text-white">
                  {currentMeter.reading_interval}s
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Unit</p>
                <p className="text-base font-semibold text-slate-900 dark:text-white">
                  {currentMeter.display.unit}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Type</p>
                <p className="text-base font-semibold text-slate-900 dark:text-white capitalize">
                  {currentMeter.type}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Snapshots */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
            <div className="w-1 h-5 bg-purple-500 rounded-full"></div>
            Snapshot History
            <span className="text-sm font-normal text-slate-500 dark:text-slate-400">
              ({snapshots.length} snapshots)
            </span>
          </h2>

          {snapshots.length === 0 ? (
            <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-12 text-center">
              <ImageIcon className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400 text-lg">No snapshots available</p>
              <p className="text-sm text-slate-500 dark:text-slate-500 mt-2">
                Snapshots will appear here after readings are captured
              </p>
            </div>
          ) : (
            <div className="grid gap-6">
              {snapshots.map((snapshot, idx) => (
                <div
                  key={idx}
                  className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 overflow-hidden"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
                    {/* Snapshot Image */}
                    <div>
                      <img
                        src={`${FLASK_API_URL}${snapshot.image_url}`}
                        alt={`Snapshot from ${formatTimestamp(snapshot.snapshot.timestamp)}`}
                        className="w-full rounded-lg border border-slate-300 dark:border-slate-700"
                      />
                      <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                        <p>📷 {snapshot.snapshot.filename}</p>
                        <p>🕐 {formatTimestamp(snapshot.snapshot.timestamp)}</p>
                        {snapshot.reanalyzed && (
                          <p className="text-purple-600 dark:text-purple-400">
                            🔄 Reanalyzed: {formatTimestamp(snapshot.reanalyzed_at || '')}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Reading Data */}
                    <div>
                      <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">
                        Meter Reading
                      </h3>
                      <div className="space-y-3">
                        {snapshot.meter_reading.total_reading !== undefined && (
                          <div className="flex justify-between items-center py-3 border-b border-slate-200 dark:border-slate-700">
                            <span className="text-sm text-slate-600 dark:text-slate-400">Total Reading</span>
                            <span className="text-xl font-bold text-blue-600 dark:text-blue-400">
                              {snapshot.meter_reading.total_reading.toFixed(3)} {currentMeter.display.unit}
                            </span>
                          </div>
                        )}

                        {snapshot.meter_reading.digital_reading !== undefined && (
                          <div className="flex justify-between items-center py-2 border-b border-slate-200 dark:border-slate-700">
                            <span className="text-sm text-slate-600 dark:text-slate-400">Digital Display</span>
                            <span className="text-base font-semibold text-slate-900 dark:text-white">
                              {snapshot.meter_reading.digital_reading}
                            </span>
                          </div>
                        )}

                        {snapshot.meter_reading.dial_reading !== undefined && (
                          <div className="flex justify-between items-center py-2 border-b border-slate-200 dark:border-slate-700">
                            <span className="text-sm text-slate-600 dark:text-slate-400">Dial Reading</span>
                            <span className="text-base font-semibold text-slate-900 dark:text-white">
                              {snapshot.meter_reading.dial_reading.toFixed(3)}
                            </span>
                          </div>
                        )}

                        {snapshot.meter_reading.confidence && (
                          <div className="flex justify-between items-center py-2 border-b border-slate-200 dark:border-slate-700">
                            <span className="text-sm text-slate-600 dark:text-slate-400">Confidence</span>
                            <span
                              className={`text-base font-semibold uppercase ${
                                snapshot.meter_reading.confidence === 'high'
                                  ? 'text-green-600 dark:text-green-400'
                                  : snapshot.meter_reading.confidence === 'medium'
                                  ? 'text-yellow-600 dark:text-yellow-400'
                                  : 'text-red-600 dark:text-red-400'
                              }`}
                            >
                              {snapshot.meter_reading.confidence}
                            </span>
                          </div>
                        )}

                        {snapshot.meter_reading.notes && (
                          <div className="py-2">
                            <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Notes</p>
                            <p className="text-sm text-slate-700 dark:text-slate-300 italic">
                              {snapshot.meter_reading.notes}
                            </p>
                          </div>
                        )}
                      </div>

                      {snapshot.camera && (
                        <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            📹 {snapshot.camera.model}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            🌐 {snapshot.camera.ip}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
