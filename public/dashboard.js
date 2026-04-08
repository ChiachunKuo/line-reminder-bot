let chart;
async function refresh() {
  const list = await fetch('/data').then(r => r.json());
  if (!list.length) return;
  const labels = list.map(d => d.time);
  const temps = list.map(d => d.temperature);
  const hums = list.map(d => d.humidity);
  if (!chart) {
    chart = new Chart(document.getElementById('chart'), {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: '溫度 (°C)', data: temps, borderColor: 'red', fill: false },
          { label: '濕度 (%)', data: hums, borderColor: 'blue', fill: false }
        ]
      },
      options: { scales: { y: { beginAtZero: true } } }
    });
  } else {
    chart.data.labels = labels;
    chart.data.datasets[0].data = temps;
    chart.data.datasets[1].data = hums;
    chart.update();
  }
}
refresh();
setInterval(refresh, 15000);
