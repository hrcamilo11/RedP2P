// RedP2P - Aplicación JavaScript principal

class RedP2PApp {
    constructor() {
        console.log('🚀 Inicializando RedP2P App...');
        this.apiBaseUrl = '/api';
        this.currentSection = 'dashboard';
        this.refreshInterval = null;
        this.init();
    }

    init() {
        console.log('🔧 Configurando aplicación...');
        this.setupEventListeners();
        console.log('📡 Cargando datos iniciales...');
        this.loadInitialData();
        this.startAutoRefresh();
        console.log('✅ Aplicación inicializada correctamente');
    }

    setupEventListeners() {
        // Navegación
        document.querySelectorAll('[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.getAttribute('data-section');
                this.showSection(section);
            });
        });

        // Filtros de peers
        document.querySelectorAll('input[name="peer-filter"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.filterPeers();
            });
        });

        // Filtros de transferencias
        document.querySelectorAll('input[name="transfer-filter"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.filterTransfers();
            });
        });

        // Formulario de búsqueda
        document.getElementById('search-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.searchFiles();
        });

        // Confirmar descarga
        document.getElementById('confirm-download').addEventListener('click', () => {
            this.confirmDownload();
        });
    }

    // === NAVEGACIÓN ===
    showSection(sectionName) {
        // Ocultar todas las secciones
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.add('d-none');
        });

        // Mostrar sección seleccionada
        document.getElementById(`${sectionName}-section`).classList.remove('d-none');

               // Actualizar navegación activa
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        this.currentSection = sectionName;

        // Cargar datos específicos de la sección
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'peers':
                this.loadPeers();
                break;
            case 'files':
                this.loadFiles();
                break;
            case 'transfers':
                this.loadTransfers();
                break;
        }
    }

    // === DASHBOARD ===
    async loadDashboard() {
        try {
            await this.loadSystemStats();
            await this.loadRecentActivity();
        } catch (error) {
            console.error('Error cargando dashboard:', error);
            this.showToast('Error cargando dashboard', 'error');
        }
    }

    async loadSystemStats() {
        try {
            console.log('🔍 Cargando estadísticas del sistema...');
            const response = await fetch(`${this.apiBaseUrl}/stats`);
            console.log('📡 Respuesta de API:', response.status);
            
            if (!response.ok) throw new Error('Error obteniendo estadísticas');
            
            const stats = await response.json();
            console.log('📊 Estadísticas recibidas:', stats);
            
            // Actualizar interfaz
            const totalPeersEl = document.getElementById('total-peers');
            const onlinePeersEl = document.getElementById('online-peers');
            const totalFilesEl = document.getElementById('total-files');
            const totalSizeEl = document.getElementById('total-size');
            
            if (totalPeersEl) totalPeersEl.textContent = stats.total_peers || 0;
            if (onlinePeersEl) onlinePeersEl.textContent = stats.online_peers || 0;
            if (totalFilesEl) totalFilesEl.textContent = stats.total_files || 0;
            if (totalSizeEl) totalSizeEl.textContent = this.formatFileSize(stats.total_size || 0);
            
            console.log('✅ Estadísticas actualizadas en la interfaz');
        } catch (error) {
            console.error('❌ Error cargando estadísticas:', error);
            this.showToast('Error cargando estadísticas del sistema', 'error');
        }
    }

    async loadRecentActivity() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/transfers/history?limit=5`);
            if (!response.ok) throw new Error('Error obteniendo actividad reciente');
            
            const transfers = await response.json();
            const container = document.getElementById('recent-activity');
            
            if (transfers.length === 0) {
                container.innerHTML = '<div class="empty-state"><i class="bi bi-clock-history"></i><p>No hay actividad reciente</p></div>';
                return;
            }

            container.innerHTML = transfers.map(transfer => `
                <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                    <div>
                        <strong>${transfer.file_hash.substring(0, 8)}...</strong>
                        <small class="text-muted d-block">${transfer.transfer_type} - ${transfer.status}</small>
                    </div>
                    <div class="text-end">
                        <small class="text-muted">${this.formatDate(transfer.started_at)}</small>
                        <span class="badge bg-${this.getStatusColor(transfer.status)} ms-2">${transfer.status}</span>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error cargando actividad reciente:', error);
            document.getElementById('recent-activity').innerHTML = '<div class="error-state"><i class="bi bi-exclamation-triangle"></i><p>Error cargando actividad</p></div>';
        }
    }

    // === PEERS ===
    async loadPeers() {
        const container = document.getElementById('peers-list');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Cargando peers...</span></div></div>';

        try {
            const response = await fetch(`${this.apiBaseUrl}/peers`);
            if (!response.ok) throw new Error('Error obteniendo peers');
            
            const peers = await response.json();
            this.renderPeers(peers);
        } catch (error) {
            console.error('Error cargando peers:', error);
            container.innerHTML = '<div class="error-state"><i class="bi bi-exclamation-triangle"></i><p>Error cargando peers</p></div>';
        }
    }

    renderPeers(peers) {
        const container = document.getElementById('peers-list');
        
        if (peers.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-laptop"></i><p>No hay peers registrados</p></div>';
            return;
        }

        container.innerHTML = peers.map(peer => `
            <div class="peer-item" data-peer-id="${peer.peer_id}" data-status="${peer.is_online ? 'online' : 'offline'}">
                <div class="peer-info">
                    <div class="peer-details">
                        <h6 class="mb-1">
                            <span class="peer-status ${peer.is_online ? 'online' : 'offline'}"></span>
                            ${peer.peer_id}
                        </h6>
                        <small class="text-muted">
                            <i class="bi bi-geo-alt"></i> ${peer.host}:${peer.port}
                            <span class="ms-3"><i class="bi bi-files"></i> ${peer.files_count} archivos</span>
                        </small>
                        <div class="mt-1">
                            <small class="text-muted">
                                Última conexión: ${this.formatDate(peer.last_seen)}
                            </small>
                        </div>
                    </div>
                    <div class="peer-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="app.indexPeerFiles('${peer.peer_id}')">
                            <i class="bi bi-search"></i> Indexar
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="app.viewPeerFiles('${peer.peer_id}')">
                            <i class="bi bi-files"></i> Ver Archivos
                        </button>
                        <button class="btn btn-sm btn-outline-${peer.is_online ? 'danger' : 'success'}" 
                                onclick="app.togglePeerStatus('${peer.peer_id}', ${!peer.is_online})">
                            <i class="bi bi-${peer.is_online ? 'x-circle' : 'check-circle'}"></i>
                            ${peer.is_online ? 'Desconectar' : 'Conectar'}
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    filterPeers() {
        const filter = document.querySelector('input[name="peer-filter"]:checked').id;
        const peerItems = document.querySelectorAll('.peer-item');
        
        peerItems.forEach(item => {
            const status = item.getAttribute('data-status');
            let show = true;
            
            switch (filter) {
                case 'online-peers':
                    show = status === 'online';
                    break;
                case 'offline-peers':
                    show = status === 'offline';
                    break;
                case 'all-peers':
                default:
                    show = true;
                    break;
            }
            
            item.style.display = show ? 'block' : 'none';
        });
    }

    // === ARCHIVOS ===
    async loadFiles() {
        // Cargar lista de peers para filtros
        await this.loadPeerOptions();
    }

    async loadPeerOptions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/peers`);
            if (!response.ok) return;
            
            const peers = await response.json();
            const peerSelect = document.getElementById('peer-filter-files');
            const targetPeerSelect = document.getElementById('target-peer');
            
            const options = peers.map(peer => 
                `<option value="${peer.peer_id}">${peer.peer_id} (${peer.host}:${peer.port})</option>`
            ).join('');
            
            peerSelect.innerHTML = '<option value="">Todos los peers</option>' + options;
            targetPeerSelect.innerHTML = '<option value="">Seleccionar peer...</option>' + options;
        } catch (error) {
            console.error('Error cargando opciones de peers:', error);
        }
    }

    async searchFiles() {
        const container = document.getElementById('files-list');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Buscando archivos...</span></div></div>';

        try {
            const formData = new FormData(document.getElementById('search-form'));
            const searchParams = {
                filename: formData.get('filename-search') || null,
                min_size: formData.get('min-size') ? parseInt(formData.get('min-size')) * 1024 * 1024 : null,
                max_size: formData.get('max-size') ? parseInt(formData.get('max-size')) * 1024 * 1024 : null,
                peer_id: formData.get('peer-filter-files') || null
            };

            // Limpiar valores nulos
            Object.keys(searchParams).forEach(key => {
                if (searchParams[key] === null || searchParams[key] === '') {
                    delete searchParams[key];
                }
            });

            const response = await fetch(`${this.apiBaseUrl}/files/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(searchParams)
            });

            if (!response.ok) throw new Error('Error buscando archivos');
            
            const result = await response.json();
            this.renderFiles(result.files);
            document.getElementById('files-count').textContent = `${result.total_found} archivos`;
        } catch (error) {
            console.error('Error buscando archivos:', error);
            container.innerHTML = '<div class="error-state"><i class="bi bi-exclamation-triangle"></i><p>Error buscando archivos</p></div>';
        }
    }

    renderFiles(files) {
        const container = document.getElementById('files-list');
        
        if (files.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-search"></i><p>No se encontraron archivos</p></div>';
            return;
        }

        container.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-details">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-file-earmark file-icon"></i>
                            <div>
                                <h6 class="mb-1">${file.filename}</h6>
                                <div class="file-size">${this.formatFileSize(file.size)}</div>
                                <div class="file-peer">Peer: ${file.peer_id}</div>
                            </div>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-primary" onclick="app.downloadFile('${file.file_hash}', '${file.filename}')">
                            <i class="bi bi-download"></i> Descargar
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="app.getFileInfo('${file.file_hash}')">
                            <i class="bi bi-info-circle"></i> Info
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // === TRANSFERENCIAS ===
    async loadTransfers() {
        const container = document.getElementById('transfers-list');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Cargando transferencias...</span></div></div>';

        try {
            const filter = document.querySelector('input[name="transfer-filter"]:checked').id;
            let url = `${this.apiBaseUrl}/transfers/active`;
            
            if (filter === 'all-transfers') {
                url = `${this.apiBaseUrl}/transfers/history?limit=50`;
            }

            const response = await fetch(url);
            if (!response.ok) throw new Error('Error obteniendo transferencias');
            
            const transfers = await response.json();
            this.renderTransfers(transfers);
        } catch (error) {
            console.error('Error cargando transferencias:', error);
            container.innerHTML = '<div class="error-state"><i class="bi bi-exclamation-triangle"></i><p>Error cargando transferencias</p></div>';
        }
    }

    renderTransfers(transfers) {
        const container = document.getElementById('transfers-list');
        
        if (transfers.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-arrow-left-right"></i><p>No hay transferencias</p></div>';
            return;
        }

        container.innerHTML = transfers.map(transfer => `
            <div class="transfer-item">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <h6 class="mb-1">${transfer.file_hash.substring(0, 12)}...</h6>
                        <small class="text-muted">
                            ${transfer.transfer_type} • ${transfer.source_peer_id} → ${transfer.target_peer_id}
                        </small>
                    </div>
                    <span class="transfer-status ${transfer.status}">${transfer.status}</span>
                </div>
                <div class="transfer-progress">
                    <div class="transfer-progress-bar" style="width: ${transfer.progress * 100}%"></div>
                </div>
                <div class="d-flex justify-content-between align-items-center mt-2">
                    <small class="text-muted">
                        ${this.formatFileSize(transfer.bytes_transferred)} / ${this.formatFileSize(transfer.total_bytes)}
                    </small>
                    <small class="text-muted">
                        ${this.formatDate(transfer.started_at)}
                    </small>
                </div>
            </div>
        `).join('');
    }

    filterTransfers() {
        this.loadTransfers();
    }

    // === ACCIONES ===
    async refreshStats() {
        await this.loadSystemStats();
        this.showToast('Estadísticas actualizadas', 'success');
    }

    async indexAllFiles() {
        try {
            this.showToast('Iniciando indexación de archivos...', 'info');
            const response = await fetch(`${this.apiBaseUrl}/files/index-all`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error('Error iniciando indexación');
            
            const result = await response.json();
            this.showToast('Indexación completada', 'success');
            await this.loadSystemStats();
        } catch (error) {
            console.error('Error indexando archivos:', error);
            this.showToast('Error indexando archivos', 'error');
        }
    }

    async indexPeerFiles(peerId) {
        try {
            this.showToast(`Indexando archivos del peer ${peerId}...`, 'info');
            const response = await fetch(`${this.apiBaseUrl}/files/index/${peerId}`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error('Error indexando archivos del peer');
            
            this.showToast('Archivos indexados correctamente', 'success');
            await this.loadPeers();
        } catch (error) {
            console.error('Error indexando archivos del peer:', error);
            this.showToast('Error indexando archivos del peer', 'error');
        }
    }

    async viewPeerFiles(peerId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/files/peer/${peerId}`);
            if (!response.ok) throw new Error('Error obteniendo archivos del peer');
            
            const files = await response.json();
            this.showSection('files');
            this.renderFiles(files);
            document.getElementById('files-count').textContent = `${files.length} archivos`;
        } catch (error) {
            console.error('Error obteniendo archivos del peer:', error);
            this.showToast('Error obteniendo archivos del peer', 'error');
        }
    }

    async togglePeerStatus(peerId, isOnline) {
        try {
            const action = isOnline ? 'conectar' : 'desconectar';
            this.showToast(`${action} peer ${peerId}...`, 'info');
            
            // En un sistema real, aquí se haría la llamada a la API correspondiente
            // Por ahora solo actualizamos la interfaz
            await this.loadPeers();
            this.showToast(`Peer ${peerId} ${action}do`, 'success');
        } catch (error) {
            console.error(`Error ${isOnline ? 'conectando' : 'desconectando'} peer:`, error);
            this.showToast(`Error ${isOnline ? 'conectando' : 'desconectando'} peer`, 'error');
        }
    }

    async downloadFile(fileHash, filename) {
        try {
            // Mostrar modal de confirmación
            const modal = new bootstrap.Modal(document.getElementById('downloadModal'));
            document.getElementById('download-info').innerHTML = `
                <p><strong>Archivo:</strong> ${filename}</p>
                <p><strong>Hash:</strong> ${fileHash}</p>
                <p>¿Desea descargar este archivo?</p>
            `;
            
            // Guardar información para la descarga
            this.pendingDownload = { fileHash, filename };
            modal.show();
        } catch (error) {
            console.error('Error preparando descarga:', error);
            this.showToast('Error preparando descarga', 'error');
        }
    }

    async confirmDownload() {
        if (!this.pendingDownload) return;
        
        try {
            const { fileHash, filename } = this.pendingDownload;
            
            // Usar el proxy centralizado para la descarga
            const downloadUrl = `${this.apiBaseUrl}/download/${fileHash}`;
            
            // Crear enlace de descarga
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            link.click();
            
            this.showToast('Descarga iniciada', 'success');
            
            // Cerrar modal
            bootstrap.Modal.getInstance(document.getElementById('downloadModal')).hide();
            this.pendingDownload = null;
            
        } catch (error) {
            console.error('Error confirmando descarga:', error);
            this.showToast('Error en la descarga', 'error');
        }
    }
    

    async getFileInfo(fileHash) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/files/${fileHash}`);
            if (!response.ok) throw new Error('Error obteniendo información del archivo');
            
            const fileInfo = await response.json();
            
            // Mostrar información en un modal o alerta
            alert(`Información del archivo:\n\nNombre: ${fileInfo.filename}\nTamaño: ${this.formatFileSize(fileInfo.size)}\nHash: ${fileInfo.file_hash}\nPeer: ${fileInfo.peer_id}\nÚltima modificación: ${this.formatDate(fileInfo.last_modified)}`);
        } catch (error) {
            console.error('Error obteniendo información del archivo:', error);
            this.showToast('Error obteniendo información del archivo', 'error');
        }
    }

    async uploadFiles() {
        const fileInput = document.getElementById('file-upload');
        const targetPeer = document.getElementById('target-peer').value;
        
        if (!fileInput.files.length) {
            this.showToast('Seleccione al menos un archivo', 'warning');
            return;
        }
        
        if (!targetPeer) {
            this.showToast('Seleccione un peer destino', 'warning');
            return;
        }
        
        try {
            this.showToast('Iniciando subida de archivos...', 'info');
            
            // Subir archivos reales
            for (let file of fileInput.files) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('target_peer', targetPeer);
                
                const response = await fetch(`${this.apiBaseUrl}/transfers/upload-file`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.text();
                    throw new Error(`Error subiendo ${file.name}: ${error}`);
                }
                
                const result = await response.json();
                console.log(`Archivo ${file.name} subido:`, result);
            }
            
            this.showToast('Archivos subidos correctamente', 'success');
            fileInput.value = '';
            
            // Recargar la lista de archivos para mostrar los nuevos
            await this.loadFiles();
            
        } catch (error) {
            console.error('Error subiendo archivos:', error);
            this.showToast(`Error subiendo archivos: ${error.message}`, 'error');
        }
    }

    // === UTILIDADES ===
    async loadInitialData() {
        await this.loadSystemStats();
        await this.loadPeerOptions();
    }

    startAutoRefresh() {
        // Actualizar cada 30 segundos
        this.refreshInterval = setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadSystemStats();
            }
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('es-ES');
    }

    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'initiated': 'info',
            'completed': 'success',
            'failed': 'danger'
        };
        return colors[status] || 'secondary';
    }

    async calculateFileHash(file) {
        // Simulación de cálculo de hash
        return 'hash_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');
        const toastHeader = toast.querySelector('.toast-header i');
        
        toastMessage.textContent = message;
        
        // Cambiar color según el tipo
        toastHeader.className = `bi bi-${this.getToastIcon(type)} text-${this.getStatusColor(type)} me-2`;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    getToastIcon(type) {
        const icons = {
            'success': 'check-circle-fill',
            'error': 'exclamation-triangle-fill',
            'warning': 'exclamation-triangle-fill',
            'info': 'info-circle-fill'
        };
        return icons[type] || 'info-circle-fill';
    }
}

// Funciones globales para uso en HTML
function refreshStats() {
    app.refreshStats();
}

function indexAllFiles() {
    app.indexAllFiles();
}

function showSection(section) {
    app.showSection(section);
}

function refreshPeers() {
    app.loadPeers();
}

function refreshTransfers() {
    app.loadTransfers();
}

function searchFiles() {
    app.searchFiles();
}

function uploadFiles() {
    app.uploadFiles();
}

// Inicializar aplicación
const app = new RedP2PApp();
