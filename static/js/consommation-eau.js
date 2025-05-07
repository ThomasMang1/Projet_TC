// Fonction pour formater la date en format français
function formaterDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
}

// Fonction pour créer le graphique
function creerGraphiqueConsommation() {
    fetch('/api/consommation-eau')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('graphiqueConsommation').getContext('2d');
            
            // Préparer les données pour le graphique
            const labels = data.map(item => formaterDate(item.date));
            const valeurs = data.map(item => item.total_eau);
            
            // Créer le graphique
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Consommation d\'eau (L)',
                        data: valeurs,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Consommation d\'eau sur les 7 derniers jours'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Litres'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Erreur lors de la récupération des données:', error));
}

// Appeler la fonction au chargement de la page
document.addEventListener('DOMContentLoaded', creerGraphiqueConsommation); 