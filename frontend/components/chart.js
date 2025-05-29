
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-black text-white">
    <canvas id="equityChart" width="400" height="200"></canvas>
    <script>
        const ctx = document.getElementById('equityChart').getContext('2d');
        const equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ["T1", "T2", "T3", "T4", "T5"],
                datasets: [{
                    label: 'Equity Curve',
                    data: [100, 105, 110, 108, 115],
                    borderColor: 'lime',
                    tension: 0.4
                }]
            },
            options: {
                scales: {
                    x: { display: true },
                    y: { display: true }
                }
            }
        });
    </script>
</body>
</html>
