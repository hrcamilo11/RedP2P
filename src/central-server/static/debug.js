// RedP2P - JavaScript de diagnóstico
console.log("🔍 RedP2P Debug Script cargado");

// Función para probar la API
async function testAPI() {
    console.log("🧪 Probando API...");
    try {
        const response = await fetch('/api/health');
        console.log("✅ Health check:", response.status);
        
        const statsResponse = await fetch('/api/stats');
        const stats = await statsResponse.json();
        console.log("📊 Estadísticas:", stats);
        
        // Actualizar la interfaz
        document.getElementById('total-peers').textContent = stats.total_peers || 0;
        document.getElementById('online-peers').textContent = stats.online_peers || 0;
        document.getElementById('total-files').textContent = stats.total_files || 0;
        document.getElementById('total-size').textContent = formatFileSize(stats.total_size || 0);
        
        console.log("✅ Interfaz actualizada");
        
    } catch (error) {
        console.error("❌ Error en API:", error);
    }
}

// Función para formatear tamaño de archivo
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Función para mostrar notificación
function showNotification(message, type = 'info') {
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
    // Crear notificación visual simple
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#198754' : '#0d6efd'};
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        z-index: 9999;
        font-family: Arial, sans-serif;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        document.body.removeChild(notification);
    }, 3000);
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 DOM cargado, iniciando diagnóstico...");
    
    // Mostrar notificación de inicio
    showNotification("RedP2P Debug iniciado", "info");
    
    // Probar API después de un breve delay
    setTimeout(testAPI, 1000);
    
    // Probar API cada 5 segundos
    setInterval(testAPI, 5000);
});

// Función global para probar manualmente
window.testRedP2P = testAPI;
window.showNotification = showNotification;

console.log("✅ RedP2P Debug Script configurado");
