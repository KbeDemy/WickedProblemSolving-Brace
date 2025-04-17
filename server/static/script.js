const MAX_VALUE = 180;
const DAYS_OF_WEEK = ['Zondag', 'Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag'];

let config = {
    target_daily_movement: 600000
};

const waardeElement = document.getElementById('waarde');
const temperatureValueElement = document.getElementById('temperature-value');
const weekGrid = document.querySelector('.week-grid');

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
            fill: true,
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            y: {
                beginAtZero: true,
                max: MAX_VALUE,
                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                ticks: { color: '#90caf9' }
            },
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                ticks: { color: '#90caf9', maxTicksLimit: 12 }
            }
        }
    }
});

function updateKneeAngle(angle) {
    const lowerLeg = document.getElementById('knee-lower-leg');
    if (lowerLeg) {
        const rotated = 180 - angle;
        lowerLeg.style.transform = `rotate(${rotated}deg)`;
        document.getElementById('angle-value').textContent = angle;
    }
}

function formatMovementScore(score) {
    if (score >= 1_000_000) return `${(score / 1_000_000).toFixed(1)}M°`;
    else if (score >= 1000) return `${(score / 1000).toFixed(1)}K°`;
    return `${Math.round(score)}°`;
}

function getColorForValue(value) {
    const normalized = (value / config.target_daily_movement) * 100;
    if (normalized < 30) return '#ff4444';
    else if (normalized < 70) return '#ffbb33';
    else return '#00C851';
}

function createWeekOverview(weekData) {
    weekGrid.innerHTML = '';
    DAYS_OF_WEEK.forEach((day, index) => {
        const dayData = weekData[index] || { value: 0 };
        const score = dayData.value;
        const percentage = Math.min(100, Math.round((score / config.target_daily_movement) * 100));

        const card = document.createElement('div');
        card.className = 'day-card';
        card.style.borderColor = getColorForValue(score);
        card.innerHTML = `
            <div class="day-name">${day}</div>
            <div class="day-value" style="color: ${getColorForValue(score)}">
                ${formatMovementScore(score)}
            </div>
            <div class="day-percentage">${percentage}%</div>
        `;
        weekGrid.appendChild(card);
    });
}

function updateChart(labels, values) {
    historyChart.data.labels = labels;
    historyChart.data.datasets[0].data = values;
    historyChart.update('none');
}

function updateChartFromMomentValues() {
    fetch('/get_moment_values')
        .then(r => r.json())
        .then(data => {
            const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            const values = data.map(d => d.angle);
            updateChart(labels, values);
        })
        .catch(err => console.error('Fout bij ophalen van momentwaarden:', err));
}

function updateChartFromDeltas(mode) {
    fetch('/get_day_overview')
        .then(r => r.json())
        .then(data => {
            let filtered = [];
            let labels = [];

            if (mode === 'minute') {
                filtered = data.slice(0, 1440);
                labels = filtered.map((_, i) => `${i + 1}m`);
            } else if (mode === 'hour') {
                filtered = data.slice(0, 168);
                labels = filtered.map((_, i) => `${i + 1}u`);
            } else if (mode === 'day') {
                filtered = data;
                labels = filtered.map((_, i) => `Dag ${i + 1}`);
            }

            updateChart(labels, filtered);
        })
        .catch(err => console.error('Fout bij ophalen van deltas:', err));
}

function updateValues() {
    // 1. Huidige waarde
    fetch('/get_current_value')
        .then(r => r.json())
        .then(data => {
            if (data.angle !== undefined) updateKneeAngle(data.angle);
            if (data.temperature !== undefined) {
                temperatureValueElement.textContent = `${data.temperature.toFixed(1)} °C`;
            }
        })
        .catch(err => {
            console.error('Fout bij ophalen van huidige waarde:', err);
            waardeElement.textContent = "Verbinding verbroken";
            temperatureValueElement.textContent = "– °C";
        });

    // 2. Historiek op basis van actieve tab
    const selectedTab = document.querySelector('.tab.active')?.id;
    if (selectedTab === 'tab-dag') {
        updateChartFromDeltas('minute');
    } else if (selectedTab === 'tab-week') {
        updateChartFromDeltas('hour');
    } else if (selectedTab === 'tab-totaal') {
        updateChartFromDeltas('day');
    } else {
        updateChartFromMomentValues();
    }

    // 3. Weekoverzicht
    fetch('/get_week_overview')
        .then(r => r.json())
        .then(data => createWeekOverview(data))
        .catch(err => console.error('Fout bij ophalen van weekoverzicht:', err));
}

function loadConfig() {
    const saved = localStorage.getItem('dailyGoal');
    document.getElementById('dailyGoal').value = saved || 1000;
    config.target_daily_movement = parseInt(document.getElementById('dailyGoal').value);
}

function saveConfig() {
    const newGoal = parseInt(document.getElementById('dailyGoal').value);
    if (isNaN(newGoal) || newGoal < 0) {
        alert('Vul een geldig dagelijks doel in (moet een positief getal zijn)');
        return;
    }
    localStorage.setItem('dailyGoal', newGoal);
    config.target_daily_movement = newGoal;
    alert('Instellingen opgeslagen!');
}

document.addEventListener('DOMContentLoaded', function () {
    loadConfig();
    updateValues();
    setInterval(updateValues, 500);

    const settingsButton = document.getElementById('settings-button');
    const settingsPanel = document.getElementById('settings-panel');
    if (settingsButton && settingsPanel) {
        settingsButton.addEventListener('click', () => {
            settingsPanel.classList.toggle('hidden');
        });
    }

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            updateValues();  // Chart vernieuwen op tab-click
        });
    });
});
