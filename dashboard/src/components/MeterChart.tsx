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
  const chartData = {
    labels: data.map(d => formatForChart(d.timestamp)),
    datasets: [
      {
        label: title,
        data: data.map(d => d.value),
        borderColor: color,
        backgroundColor: `${color}20`,
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
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
        display: true,
        text: title,
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
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
        ticks: {
          callback: (value: any) => `${value.toFixed(0)} ${unit}`,
        },
      },
      x: {
        ticks: {
          maxRotation: 45,
          minRotation: 45,
        },
      },
    },
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
      <div style={{ height: '300px' }}>
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
