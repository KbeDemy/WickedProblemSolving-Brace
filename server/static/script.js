const MAX_VALUE = 180;
const GAUGE_CIRCUMFERENCE = 314;
const MAX_DATA_POINTS = 500;

const gaugeArc = document.getElementById('gauge-arc');
const gaugeValue = document.getElementById('gauge-value');
const waardeElement = document.getElementById('waarde');

const ctx = document.getElementById('historyChart').getContext('2d');
const historyChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Waarde',
            data: [],
            borderColor: '#66b2ff',
            backgroundColor: 'rgba(102, 178, 255, 0.1)',
            fill: true
        }]
    },
    options: {
        scales: {
            y: { beginAtZero: true, max: MAX_VALUE },
            x: { maxTicksLimit: 10 }
        }
    }
});

function updateGauge(value) {
    const normalizedValue = Math.min(Math.max(value, 0), MAX_VALUE);
    const fillPercentage = normalizedValue / MAX_VALUE;
    const dashArray = `${fillPercentage * GAUGE_CIRCUMFERENCE} ${GAUGE_CIRCUMFERENCE}`;

    gaugeArc.style.strokeDasharray = dashArray;
    gaugeValue.textContent = normalizedValue;
}

function updateChart(data) {
    const recentData = data.slice(-MAX_DATA_POINTS);
    const labels = recentData.map(item => new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    const values = recentData.map(item => item.value);

    historyChart.data.labels = labels;
    historyChart.data.datasets[0].data = values;
    historyChart.update('none');
}

function updateValues() {
    fetch('/get_values')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const lastValue = data[data.length - 1];
                waardeElement.innerText = lastValue.value;
                updateGauge(lastValue.value);
                updateChart(data);
            } else {
                waardeElement.innerText = "Geen data";
                updateGauge(0);
            }
        })
        .catch(error => {
            console.error('Fout bij ophalen van gegevens:', error);
            const testValue = Math.floor(Math.random() * 180);
            waardeElement.innerText = testValue;
            updateGauge(testValue);
        });
}

updateValues();
setInterval(updateValues, 1000);

