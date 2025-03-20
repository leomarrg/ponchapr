document.addEventListener('DOMContentLoaded', function() {
    // Get data from Django template
    const dates = JSON.parse(document.getElementById('dates-data').textContent);
    const attendeeData = JSON.parse(document.getElementById('attendee-data').textContent);
    const reviewCategories = JSON.parse(document.getElementById('review-categories-data').textContent);
    const reviewCounts = JSON.parse(document.getElementById('review-counts-data').textContent);

    // Attendees Chart
    const attendeesCtx = document.getElementById('attendeesChart').getContext('2d');
    new Chart(attendeesCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Daily Registrations',
                data: attendeeData,
                borderColor: '#309bbf',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Daily Registrations'
                }
            }
        }
    });

    // Reviews Chart
    const reviewsCtx = document.getElementById('reviewsChart').getContext('2d');
    new Chart(reviewsCtx, {
        type: 'bar',
        data: {
            labels: reviewCategories,
            datasets: [{
                label: 'Reviews by Category',
                data: reviewCounts,
                backgroundColor: '#309bbf'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Reviews by Category'
                }
            }
        }
    });
});