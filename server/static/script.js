const MAX_VALUE = 180;
const DAYS_OF_WEEK = ['Zondag', 'Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag'];
const MOVEMENT_THRESHOLD = 5;

let config = {
    target_daily_movement: 600000
};


const waardeElement = document.getElementById('waarde');
const temperatureValueElement = document.getElementById('temperature-value'); // ✅ Nieuw

const weekGrid = document.querySelector('.week-grid');
const dailyDetail = document.getElementById('daily-detail');
const backButton = document.getElementById('back-to-week');

// Chart.js setup
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

function getColorForValue(value) {
    const normalizedValue = (value / config.target_daily_movement) * 100;
    if (normalizedValue < 30) return '#ff4444';
    else if (normalizedValue < 70) return '#ffbb33';
    else return '#00C851';
}

function formatMovementScore(score) {
    if (score >= 1_000_000) return `${(score / 1_000_000).toFixed(1)}M°`;
    else if (score >= 1000) return `${(score / 1000).toFixed(1)}K°`;
    return `${Math.round(score)}°`;
}

function createWeekOverview(weekData) {
    weekGrid.innerHTML = '';
    DAYS_OF_WEEK.forEach((day, index) => {
        const dayData = weekData[index] || { value: 0, count: 0 };
        const movementScore = dayData.value;
        const normalizedValue = (movementScore / config.target_daily_movement) * 100;

        const dayCard = document.createElement('div');
        dayCard.className = 'day-card';
        dayCard.style.borderColor = getColorForValue(movementScore);
        dayCard.innerHTML = `
            <div class="day-name">${day}</div>
            <div class="day-value" style="color: ${getColorForValue(movementScore)}">
                ${formatMovementScore(movementScore)}
            </div>
            <div class="day-percentage">
                ${Math.min(100, Math.round(normalizedValue))}%
            </div>
        `;
        dayCard.addEventListener('click', () => showDailyDetail(index));
        weekGrid.appendChild(dayCard);
    });
}


function updateKneeAngle(angle) {
  const lowerLeg = document.getElementById('knee-lower-leg');
  if (lowerLeg) {
    const rotated = 180 - angle;
    lowerLeg.style.transform = `rotate(${rotated}deg)`;
    document.getElementById('angle-value').textContent = angle;
  }
}


function updateChart(data) {
    const labels = data.map(item => {
        const date = new Date(item.timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    const values = data.map(item => item.angle);
    historyChart.data.labels = labels;
    historyChart.data.datasets[0].data = values;
    historyChart.update('none');
}

function loadConfig() {
    const savedDailyGoal = localStorage.getItem('dailyGoal');
    document.getElementById('dailyGoal').value = savedDailyGoal || 1000;
    config.target_daily_movement = parseInt(document.getElementById('dailyGoal').value);
}

function saveConfig() {
    const newDailyGoal = parseInt(document.getElementById('dailyGoal').value);
    if (isNaN(newDailyGoal) || newDailyGoal < 0) {
        alert('Vul een geldig dagelijks doel in (moet een positief getal zijn)');
        return;
    }
    localStorage.setItem('dailyGoal', newDailyGoal);
    config.target_daily_movement = newDailyGoal;
    alert('Instellingen opgeslagen!');
}

function updateValues() {
    fetch('/get_current_value')
        .then(response => response.json())
        .then(data => {
            if (data.angle !== undefined) {
                updateKneeAngle(data.angle);
            }
            if (data.temperature !== undefined && temperatureValueElement) {
                temperatureValueElement.textContent = `${data.temperature.toFixed(1)} °C`;
            }
        })
        .catch(error => {
            console.error('Fout bij ophalen van huidige waarde:', error);
            waardeElement.textContent = "Verbinding verbroken";
            updateGauge(0);
            if (temperatureValueElement) {
                temperatureValueElement.textContent = "– °C";
            }
        });
    
    fetch('/get_values')
        .then(response => response.json())
        .then(data => updateChart(data))
        .catch(error => console.error('Fout bij ophalen van historische waardes:', error));

    fetch('/get_week_overview')
        .then(response => response.json())
        .then(data => createWeekOverview(data))
        .catch(error => console.error('Fout bij ophalen van weekoverzicht:', error));
}

// Event Listeners
backButton.addEventListener('click', () => {
    dailyDetail.style.display = 'none';
    document.querySelector('.week-overview').style.display = 'block';
});

document.addEventListener('DOMContentLoaded', function () {
    loadConfig();
    updateValues();
    setInterval(updateValues, 500);

    // Settings gear logic
    const settingsButton = document.getElementById('settings-button');
    const settingsPanel = document.getElementById('settings-panel');

    if (settingsButton && settingsPanel) {
        settingsButton.addEventListener('click', () => {
            settingsPanel.classList.toggle('hidden');
        });
    }
});
