import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import type { ChartDataPoint } from '../types/meter';
import { formatForChart } from '../utils/timezone';
import { useTheme } from '../contexts/ThemeContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MeterChartProps {
  data: ChartDataPoint[];
  title: string;
  color: string;
  unit: string;
}

export function MeterChart({ data, title, color, unit }: MeterChartProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  // Theme-aware colors
  const textColor = isDark ? '#e2e8f0' : '#1e293b';
  const gridColor = isDark ? '#334155' : '#cbd5e1';
  const tooltipBg = isDark ? '#1e293b' : '#ffffff';
  const tooltipBorder = isDark ? '#475569' : '#cbd5e1';

  const chartData = {
    labels: data.map(d => formatForChart(d.timestamp)),
    datasets: [
      {
        label: title,
        data: data.map(d => d.value),
        borderColor: color,
        backgroundColor: `${color}30`,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: color,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        borderWidth: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        backgroundColor: tooltipBg,
        titleColor: textColor,
        bodyColor: textColor,
        borderColor: tooltipBorder,
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: (context: any) => {
            return `${context.parsed.y.toFixed(2)} ${unit}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        border: {
          display: false,
        },
        grid: {
          color: gridColor,
          lineWidth: 1,
        },
        ticks: {
          color: textColor,
          font: {
            size: 12,
          },
          callback: (value: any) => `${value.toFixed(0)} ${unit}`,
        },
      },
      x: {
        border: {
          display: false,
        },
        grid: {
          color: gridColor,
          lineWidth: 1,
        },
        ticks: {
          color: textColor,
          font: {
            size: 11,
          },
          maxRotation: 45,
          minRotation: 45,
        },
      },
    },
  };

  return (
    <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-2xl border border-slate-300/50 dark:border-slate-700/50 p-7 hover:bg-white/80 dark:hover:bg-slate-800/80 hover:border-slate-400/50 dark:hover:border-slate-600/50 transition-all duration-200 shadow-xl">
      <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-5">{title}</h3>
      <div style={{ height: '320px' }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
