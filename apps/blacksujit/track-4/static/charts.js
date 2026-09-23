/**
 * Charts for Meeting QA Copilot dashboard.
 * Uses Chart.js to render trend visualizations.
 */

function renderTrendChart(ctxId, labels, data, label, color) {
  const ctx = document.getElementById(ctxId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: label,
        data: data,
        borderColor: color,
        backgroundColor: color + '20',
        tension: 0.3,
        fill: true,
        pointRadius: 5,
        pointHoverRadius: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 0, max: 100, grid: { color: '#e5e7eb' } },
        x: { grid: { display: false } }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          padding: 8,
          borderRadius: 6,
          titleFont: { size: 12 },
          bodyFont: { size: 13 },
        }
      },
      interaction: { intersect: false, mode: 'index' }
    }
  });
}

function initTrendsChart() {
  fetch('/api/trends-data')
    .then(r => r.json())
    .then(d => {
      if (!d.labels || d.labels.length === 0) return;

      renderTrendChart('chart-overall', d.labels, d.overall, 'Overall Score', '#2563eb');
      renderTrendChart('chart-clarity', d.labels, d.clarity, 'Clarity', '#3b82f6');
      renderTrendChart('chart-tension', d.labels, d.tension, 'Tension', '#f59e0b');
      renderTrendChart('chart-compliance', d.labels, d.compliance, 'Compliance', '#ef4444');
      renderTrendChart('chart-action', d.labels, d.action_items, 'Action Items', '#10b981');
    })
    .catch(err => console.error('Trend data fetch failed:', err));
}

function jumpToTimestamp(jobId, seconds) {
  window.open(`https://whipscribe.com/transcript/${jobId}?t=${Math.floor(seconds)}`, '_blank');
}

document.addEventListener('DOMContentLoaded', function() {
  if (document.getElementById('chart-overall')) {
    initTrendsChart();
  }
});
