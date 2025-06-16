document.addEventListener('DOMContentLoaded', function () {
  const ctx = document.getElementById('userStatusChart').getContext('2d');
  const userStatusChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Active', 'Inactive', 'Verified', 'Unverified'],
      datasets: [{
        label: 'User Status',
        data: [
          chartData.active_users,
          chartData.inactive_users,
          chartData.verified_users,
          chartData.unverified_users
        ],
        backgroundColor: ['#0d6efd', '#dc3545', '#198754', '#ffc107'], // Updated for navy+bootstrap colors
        borderColor: 'rgba(255, 255, 255, 0.8)',
        borderWidth: 2,
        hoverOffset: 40
      }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: 'white',
            font: {
              size: 14,
              weight: '600'
            }
          }
        },
        tooltip: {
          enabled: true,
          backgroundColor: '#001F4D',
          titleColor: '#fff',
          bodyColor: '#eee'
        }
      }
    }
  });
});
