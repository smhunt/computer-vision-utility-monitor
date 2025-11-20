import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Camera, RotateCcw, Trash2, RefreshCw } from 'lucide-react';
import type { MeterConfig } from '../types/meter';
import { fetchMeterConfig } from '../api/influxdb';
import axios from 'axios';

const FLASK_API_URL = import.meta.env.VITE_FLASK_API_URL || 'http://127.0.0.1:2500';

interface ActivityLogEntry {
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'error';
}

const ROTATION_OPTIONS = [
  { value: 0, label: '0° Normal' },
  { value: 90, label: '90° CW' },
  { value: 180, label: '180° Flip' },
  { value: 270, label: '270° CW' },
];

export function CameraPreview() {
  const { meterType } = useParams<{ meterType: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [rotation, setRotation] = useState(0);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [statusMessage, setStatusMessage] = useState<{ message: string; type: string } | null>(null);

  const { data: meterConfigs, isLoading: metersLoading } = useQuery({
    queryKey: ['config', 'meters'],
    queryFn: fetchMeterConfig,
  });

  const currentMeter = meterConfigs?.find((m: MeterConfig) => m.type === meterType);

  const addLogEntry = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    setActivityLog(prev => [...prev.slice(-19), { timestamp, message, type }]);
  };

  const showStatus = (message: string, type: string) => {
    setStatusMessage({ message, type });
    if (type === 'success') {
      setTimeout(() => setStatusMessage(null), 5000);
    }
  };

  const rotationMutation = useMutation({
    mutationFn: async (degrees: number) => {
      const response = await axios.post(`${FLASK_API_URL}/api/rotation/${meterType}`, {
        rotation: degrees,
      });
      return response.data;
    },
    onSuccess: (_data, degrees) => {
      setRotation(degrees);
      addLogEntry(`✓ Rotation set to ${degrees}° (applied on next reading)`, 'success');
      showStatus(`✓ Rotation set to ${degrees}°. Will apply on next reading.`, 'success');
    },
    onError: (error: any) => {
      addLogEntry(`✗ Error: ${error.message}`, 'error');
      showStatus(`✗ Error: ${error.message}`, 'error');
    },
  });

  const reanalyzeMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${FLASK_API_URL}/api/snapshot/reanalyze/${meterType}`);
      return response.data;
    },
    onMutate: () => {
      addLogEntry('🔄 Reanalyzing snapshot...');
      showStatus('🔄 Reanalyzing snapshot...', 'info');
    },
    onSuccess: () => {
      addLogEntry('✓ Snapshot reanalyzed successfully!', 'success');
      showStatus('✓ Reanalysis complete! Refreshing...', 'success');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['meter', meterType] });
      }, 1500);
    },
    onError: (error: any) => {
      addLogEntry(`✗ Reanalysis error: ${error.message}`, 'error');
      showStatus(`✗ Error: ${error.message}`, 'error');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${FLASK_API_URL}/api/snapshot/delete/${meterType}`);
      return response.data;
    },
    onMutate: () => {
      addLogEntry('🗑️ Deleting snapshot...');
      showStatus('🗑️ Deleting snapshot...', 'info');
    },
    onSuccess: () => {
      addLogEntry('✓ Snapshot deleted successfully!', 'success');
      showStatus('✓ Deleted! Refreshing...', 'success');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['meter', meterType] });
      }, 1000);
    },
    onError: (error: any) => {
      addLogEntry(`✗ Delete error: ${error.message}`, 'error');
      showStatus(`✗ Error: ${error.message}`, 'error');
    },
  });

  const captureSnapshotMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${FLASK_API_URL}/api/snapshot/${meterType}`);
      return response.data;
    },
    onMutate: () => {
      addLogEntry('📸 Capturing snapshot with current camera settings...');
      showStatus('📸 Capturing image with current mode...', 'info');
    },
    onSuccess: () => {
      addLogEntry('✓ Snapshot captured successfully!', 'success');
      showStatus('✓ Snapshot captured! Refreshing...', 'success');
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['meter', meterType] });
      }, 1500);
    },
    onError: (error: any) => {
      addLogEntry(`✗ Capture error: ${error.message}`, 'error');
      showStatus(`✗ Error: ${error.message}`, 'error');
    },
  });

  const handleRotationChange = (degrees: number) => {
    rotationMutation.mutate(degrees);
  };

  const handleReanalyze = () => {
    if (confirm('Reanalyze this snapshot? This will use Claude API credits.')) {
      reanalyzeMutation.mutate();
    }
  };

  const handleDelete = () => {
    if (confirm('Delete this snapshot? This action cannot be undone.')) {
      deleteMutation.mutate();
    }
  };

  const handleCapture = () => {
    captureSnapshotMutation.mutate();
  };

  if (metersLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Loading camera...</p>
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
              <div className="p-2.5 bg-blue-500/20 rounded-xl border border-blue-500/30">
                <Camera className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  {currentMeter.display.label} Camera
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                  Live preview and camera controls
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Live Stream */}
          <div className="lg:col-span-2">
            <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Live Stream</h2>
              <div className="bg-slate-900 rounded-lg overflow-hidden">
                <img
                  src={`${FLASK_API_URL}/api/stream/${meterType}`}
                  alt={`${currentMeter.display.label} live stream`}
                  className="w-full max-h-[600px] object-contain"
                />
              </div>

              {/* Snapshot Actions */}
              <div className="flex gap-3 mt-4">
                <button
                  onClick={handleCapture}
                  disabled={captureSnapshotMutation.isPending}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors"
                >
                  <Camera className="w-5 h-5" />
                  {captureSnapshotMutation.isPending ? 'Capturing...' : 'Capture Snapshot'}
                </button>
                <button
                  onClick={handleReanalyze}
                  disabled={reanalyzeMutation.isPending}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-600 hover:bg-slate-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
                  title="Reanalyze this snapshot with Claude"
                >
                  <RefreshCw className="w-5 h-5" />
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg transition-colors"
                  title="Delete this snapshot"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Controls Sidebar */}
          <div className="space-y-6">
            {/* Rotation Controls */}
            <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
              <div className="flex items-center gap-2 mb-4">
                <RotateCcw className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                <h3 className="text-base font-semibold text-slate-900 dark:text-white">Image Rotation</h3>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {ROTATION_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleRotationChange(option.value)}
                    disabled={rotationMutation.isPending}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      rotation === option.value
                        ? 'bg-purple-600 text-white'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-center text-slate-500 dark:text-slate-400 mt-3">
                Current: {rotation}°
              </p>
            </div>

            {/* Status Message */}
            {statusMessage && (
              <div
                className={`rounded-xl p-4 border ${
                  statusMessage.type === 'success'
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200'
                    : statusMessage.type === 'error'
                    ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200'
                    : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200'
                }`}
              >
                <p className="text-sm">{statusMessage.message}</p>
              </div>
            )}

            {/* Activity Log */}
            <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 p-6">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Activity Log</h3>
              <div className="space-y-1 max-h-64 overflow-y-auto text-xs font-mono">
                {activityLog.length === 0 ? (
                  <p className="text-slate-500 dark:text-slate-400">Waiting for action...</p>
                ) : (
                  activityLog.map((entry, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-2 py-1 border-l-2 pl-2 ${
                        entry.type === 'success'
                          ? 'border-green-500'
                          : entry.type === 'error'
                          ? 'border-red-500'
                          : 'border-blue-500'
                      }`}
                    >
                      <span className="text-slate-500 dark:text-slate-400">[{entry.timestamp}]</span>
                      <span className="text-slate-700 dark:text-slate-300">{entry.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
