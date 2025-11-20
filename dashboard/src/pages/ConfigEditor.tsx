import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, FileCode, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const FLASK_API_URL = import.meta.env.VITE_FLASK_API_URL || 'http://127.0.0.1:2500';

export function ConfigEditor() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [metersConfig, setMetersConfig] = useState('');
  const [pricingConfig, setPricingConfig] = useState('');
  const [activeTab, setActiveTab] = useState<'meters' | 'pricing'>('meters');
  const [hasChanges, setHasChanges] = useState(false);

  // Load current configurations
  useQuery({
    queryKey: ['config', 'raw'],
    queryFn: async () => {
      const [metersResponse, pricingResponse] = await Promise.all([
        axios.get(`${FLASK_API_URL}/config/edit`),
        axios.get(`${FLASK_API_URL}/api/config/pricing`),
      ]);

      // Extract meters config from HTML response (this is a workaround)
      // In production, you'd want a dedicated API endpoint
      const metersText = metersResponse.data; // Would need parsing in real implementation
      const pricingText = JSON.stringify(pricingResponse.data.pricing, null, 2);

      setMetersConfig(metersText);
      setPricingConfig(pricingText);

      return { metersConfig: metersText, pricingConfig: pricingText };
    },
  });

  const saveMetersMutation = useMutation({
    mutationFn: async (config: string) => {
      const formData = new FormData();
      formData.append('meters_config', config);

      const response = await axios.post(`${FLASK_API_URL}/config/save/meters`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setHasChanges(false);
      alert('✅ Meter configuration saved successfully!');
    },
    onError: (error: any) => {
      alert(`❌ Error saving meter configuration: ${error.message}`);
    },
  });

  const savePricingMutation = useMutation({
    mutationFn: async (config: string) => {
      const formData = new FormData();
      formData.append('pricing_config', config);

      const response = await axios.post(`${FLASK_API_URL}/config/save/pricing`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      setHasChanges(false);
      alert('✅ Pricing configuration saved successfully!');
    },
    onError: (error: any) => {
      alert(`❌ Error saving pricing configuration: ${error.message}`);
    },
  });

  const handleSave = () => {
    if (activeTab === 'meters') {
      saveMetersMutation.mutate(metersConfig);
    } else {
      savePricingMutation.mutate(pricingConfig);
    }
  };

  const handleMetersChange = (value: string) => {
    setMetersConfig(value);
    setHasChanges(true);
  };

  const handlePricingChange = (value: string) => {
    setPricingConfig(value);
    setHasChanges(true);
  };

  const handleReset = () => {
    if (confirm('Discard all unsaved changes?')) {
      queryClient.invalidateQueries({ queryKey: ['config', 'raw'] });
      setHasChanges(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Header */}
      <header className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-b border-slate-300/50 dark:border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => {
                  if (hasChanges && !confirm('You have unsaved changes. Are you sure you want to leave?')) {
                    return;
                  }
                  navigate('/settings');
                }}
                className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="p-2.5 bg-purple-500/20 rounded-xl border border-purple-500/30">
                <FileCode className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Configuration Editor</h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                  Edit meter hardware settings and utility pricing rates
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {hasChanges && (
                <span className="text-sm text-orange-600 dark:text-orange-400 font-medium">
                  Unsaved changes
                </span>
              )}
              <button
                onClick={handleReset}
                disabled={!hasChanges}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-700 disabled:bg-slate-400 text-white rounded-lg transition-colors"
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || saveMetersMutation.isPending || savePricingMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors"
              >
                <Save className="w-5 h-5" />
                {saveMetersMutation.isPending || savePricingMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-8">
        {/* Warning */}
        <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400 mt-0.5" />
            <div>
              <h3 className="text-base font-semibold text-orange-900 dark:text-orange-100 mb-1">
                Warning: Direct Configuration Editing
              </h3>
              <p className="text-sm text-orange-800 dark:text-orange-300">
                Changes to configuration files will reload the system. Make sure your YAML and JSON syntax is
                correct before saving. Invalid syntax may cause the system to malfunction.
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('meters')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'meters'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white/60 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800'
            }`}
          >
            📹 Meter Configuration
          </button>
          <button
            onClick={() => setActiveTab('pricing')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'pricing'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white/60 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800'
            }`}
          >
            💰 Pricing Configuration
          </button>
        </div>

        {/* Editor */}
        <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-300/50 dark:border-slate-700/50 overflow-hidden">
          <div className="bg-slate-100 dark:bg-slate-900/50 border-b border-slate-300/50 dark:border-slate-700/50 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                  {activeTab === 'meters' ? 'config/meters.yaml' : 'config/pricing.json'}
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {activeTab === 'meters'
                    ? 'Meter hardware configuration (cameras, intervals, etc.)'
                    : 'Utility pricing rates and household information'}
                </p>
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Format: {activeTab === 'meters' ? 'YAML' : 'JSON'}
              </div>
            </div>
          </div>

          <div className="p-6">
            <textarea
              value={activeTab === 'meters' ? metersConfig : pricingConfig}
              onChange={(e) =>
                activeTab === 'meters' ? handleMetersChange(e.target.value) : handlePricingChange(e.target.value)
              }
              className="w-full h-[600px] bg-slate-900 dark:bg-slate-950 text-green-400 font-mono text-sm p-4 rounded-lg border border-slate-700 focus:border-blue-500 focus:outline-none resize-none"
              spellCheck={false}
              style={{ fontFamily: '"Monaco", "Menlo", "Courier New", monospace', lineHeight: '1.6' }}
            />
          </div>

          {/* Help Text */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border-t border-blue-200 dark:border-blue-800 px-6 py-4">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
              {activeTab === 'meters' ? 'YAML Format Example:' : 'JSON Format Notes:'}
            </h3>
            {activeTab === 'meters' ? (
              <pre className="text-xs text-blue-800 dark:text-blue-300 font-mono overflow-x-auto">
                {`meters:
  - name: "water_main"
    type: "water"
    camera_ip: "10.10.10.207"
    reading_interval: 600
  - name: "electric_main"
    type: "electric"
    camera_ip: "10.10.10.208"
    reading_interval: 300`}
              </pre>
            ) : (
              <div className="text-xs text-blue-800 dark:text-blue-300 space-y-1">
                <p>• Household address and timezone information</p>
                <p>• Utility account numbers and provider details</p>
                <p>• Water, electricity, and natural gas pricing rates</p>
                <p>• Bill upload history and metadata</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
