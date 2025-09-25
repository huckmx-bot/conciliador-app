// static/app.js
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const statusMessage = document.getElementById('status-message');
    const searchBtn = document.getElementById('search-btn');
    const colectivaInput = document.getElementById('colectiva-search');
    const ctx = document.getElementById('trend-chart').getContext('2d');
    let trendChart;

    // 1. Manejar el envío del formulario de carga
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('file', document.getElementById('file-input').files[0]);
        formData.append('month_date', document.getElementById('month-date').value);

        statusMessage.textContent = 'Procesando...';
        statusMessage.className = 'message info';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                statusMessage.textContent = result.message;
                statusMessage.className = 'message success';
                uploadForm.reset();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            statusMessage.textContent = `Error: ${error.message}`;
            statusMessage.className = 'message error';
        }
    });

    // 2. Manejar la búsqueda para la gráfica
    searchBtn.addEventListener('click', async () => {
        const colectivaId = colectivaInput.value.trim();
        if (!colectivaId) {
            alert('Por favor, introduce un ID de Colectiva.');
            return;
        }

        try {
            const response = await fetch(`/get_data?colectiva=${colectivaId}`);
            const data = await response.json();

            if (response.ok) {
                if(data.labels.length === 0) {
                    alert('No se encontraron datos para esa Colectiva.');
                    return;
                }
                drawChart(data);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            alert(`Error al buscar datos: ${error.message}`);
        }
    });

    // 3. Función para dibujar la gráfica
    function drawChart(data) {
        if (trendChart) {
            trendChart.destroy(); // Destruye la gráfica anterior si existe
        }

        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Saldo Contabilidad',
                        data: data.saldoContabilidad,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1,
                    },
                    {
                        label: 'Saldo Conciliado',
                        data: data.saldoConciliado,
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1,
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' },
                    title: {
                        display: true,
                        text: `Evolución de Saldos para Colectiva: ${colectivaInput.value}`
                    }
                }
            }
        });
    }
});