// Fonctions pour la gestion des plantes
function loadPlants() {
    fetch('/api/plantes')
        .then(response => response.json())
        .then(plantes => {
            const plantsList = document.getElementById('plants-list');
            plantsList.innerHTML = plantes.map(plante => `
                <div class="card mb-2">
                    <div class="card-body">
                        <h6 class="card-title">${plante.nom}</h6>
                        <p class="card-text">
                            Humidité: ${plante.humidite_min}% - ${plante.humidite_max}%<br>
                            Zone: ${plante.zone || 'Non assignée'}
                        </p>
                        <button class="btn btn-sm btn-primary me-2" onclick="editPlant(${plante.id})">
                            <i class='bx bx-edit'></i> Modifier
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deletePlant(${plante.id})">
                            <i class='bx bx-trash'></i> Supprimer
                        </button>
                    </div>
                </div>
            `).join('');
        });
}

function addPlant() {
    const plantData = {
        nom: document.getElementById('plantName').value,
        humidite_min: parseFloat(document.getElementById('humidityMin').value),
        humidite_max: parseFloat(document.getElementById('humidityMax').value),
        description: document.getElementById('plantDescription').value,
        zone_id: document.getElementById('plantZone').value
    };

    fetch('/api/plantes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(plantData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            $('#addPlantModal').modal('hide');
            loadPlants();
        }
    });
}

function editPlant(id) {
    fetch(`/api/plantes/${id}`)
        .then(response => response.json())
        .then(plante => {
            document.getElementById('editPlantId').value = plante.id;
            document.getElementById('editPlantName').value = plante.nom;
            document.getElementById('editHumidityMin').value = plante.humidite_min;
            document.getElementById('editHumidityMax').value = plante.humidite_max;
            document.getElementById('editPlantDescription').value = plante.description || '';
            document.getElementById('editPlantZone').value = plante.zone_id || '';
            $('#editPlantModal').modal('show');
        });
}

function updatePlant() {
    const id = document.getElementById('editPlantId').value;
    const plantData = {
        nom: document.getElementById('editPlantName').value,
        humidite_min: parseFloat(document.getElementById('editHumidityMin').value),
        humidite_max: parseFloat(document.getElementById('editHumidityMax').value),
        description: document.getElementById('editPlantDescription').value,
        zone_id: document.getElementById('editPlantZone').value
    };

    fetch(`/api/plantes/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(plantData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            $('#editPlantModal').modal('hide');
            loadPlants();
        }
    });
}

function deletePlant(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette plante ?')) {
        fetch(`/api/plantes/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                loadPlants();
            }
        });
    }
}

// Fonctions pour la gestion des zones
function loadZones() {
    fetch('/api/zones')
        .then(response => response.json())
        .then(zones => {
            const zonesList = document.getElementById('zones-list');
            zonesList.innerHTML = zones.map(zone => `
                <div class="card mb-2">
                    <div class="card-body">
                        <h6 class="card-title">${zone.nom}</h6>
                        <p class="card-text">
                            Humidité actuelle: ${zone.humidite_actuelle || '--'}%<br>
                            Nombre de plantes: ${zone.nombre_plantes}
                        </p>
                        <button class="btn btn-sm btn-primary me-2" onclick="editZone(${zone.id})">
                            <i class='bx bx-edit'></i> Modifier
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteZone(${zone.id})">
                            <i class='bx bx-trash'></i> Supprimer
                        </button>
                    </div>
                </div>
            `).join('');
        });
}

function addZone() {
    const zoneData = {
        nom: document.getElementById('zoneName').value,
        description: document.getElementById('zoneDescription').value
    };

    fetch('/api/zones', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(zoneData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            $('#addZoneModal').modal('hide');
            loadZones();
        }
    });
}

// Fonctions pour la gestion du robot
function updateRobotStatus() {
    fetch('/api/robot/status')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }
            document.getElementById('battery-level').textContent = data.batterie;
            document.getElementById('water-level').textContent = data.eau;
            document.getElementById('robot-state').textContent = data.etat;
        });
}

// Fonctions pour la météo
function updateWeather() {
    fetch('/api/meteo')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }
            document.getElementById('temperature').textContent = data.temperature_C;
            document.getElementById('forecast').textContent = data.description;
            document.getElementById('humidity').textContent = data.humidity;
            document.getElementById('wind').textContent = data.wind_speed;
        });
}

// Fonction d'export des plantes
function exportPlantes() {
    window.location.href = '/api/plantes/export';
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    loadPlants();
    loadZones();
    updateRobotStatus();
    updateWeather();

    // Mise à jour périodique
    setInterval(updateRobotStatus, 30000); // Toutes les 30 secondes
    setInterval(updateWeather, 300000); // Toutes les 5 minutes
}); 