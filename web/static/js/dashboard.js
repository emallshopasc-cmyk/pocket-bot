class DashboardApp {
    constructor() {
        this.socket = null;
        this.timeframe = 'M5';
        this.signals = [];
        this.audioCtx = null;
        
        // DOM Elements
        this.elements = {
            clock: document.getElementById('live-clock'),
            connDot: document.getElementById('connection-dot'),
            connText: document.getElementById('connection-text'),
            statTotal: document.getElementById('stat-total'),
            statWinrate: document.getElementById('stat-winrate'),
            statPairs: document.getElementById('stat-pairs'),
            statUpdate: document.getElementById('stat-last-update'),
            tfBtns: document.querySelectorAll('.tf-btn'),
            refreshBtn: document.getElementById('refresh-btn'),
            signalGrid: document.getElementById('signal-grid'),
            emptyState: document.getElementById('empty-state'),
            tfDisplay: document.getElementById('current-tf-display'),
            historyBody: document.getElementById('history-body'),
            modal: document.getElementById('signal-modal'),
            closeModal: document.getElementById('close-modal'),
            modalInfo: document.getElementById('modal-info'),
            modalChart: document.getElementById('modal-chart-img'),
            toastContainer: document.getElementById('toast-container')
        };
    }

    init() {
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);
        
        this.setupEventListeners();
        this.connectSocket();
        
        this.fetchData();
        // Auto refresh every 60s
        setInterval(() => this.fetchData(), 60000);
    }

    setupEventListeners() {
        this.elements.tfBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.elements.tfBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.timeframe = e.target.dataset.tf;
                this.elements.tfDisplay.textContent = this.timeframe;
                this.fetchSignals();
            });
        });

        this.elements.refreshBtn.addEventListener('click', () => this.fetchData());
        
        this.elements.closeModal.addEventListener('click', () => {
            this.elements.modal.classList.remove('active');
        });
        
        // Close modal on outside click
        this.elements.modal.addEventListener('click', (e) => {
            if (e.target === this.elements.modal) {
                this.elements.modal.classList.remove('active');
            }
        });
    }

    connectSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                this.elements.connDot.className = 'status-dot connected';
                this.elements.connText.textContent = 'Qoşuldu';
            });
            
            this.socket.on('disconnect', () => {
                this.elements.connDot.className = 'status-dot disconnected';
                this.elements.connText.textContent = 'Əlaqə kəsildi';
            });
            
            this.socket.on('new_signal', (signal) => {
                if (signal.timeframe === this.timeframe || signal.timeframe === 'ALL') {
                    this.fetchSignals();
                }
                this.fetchStats();
                this.fetchHistory();
                
                this.showToast(`YENİ SİQNAL: ${signal.display_name} - ${signal.direction}`);
                this.playNotificationSound();
            });
        } catch (e) {
            console.error("Socket.io initialization error:", e);
            this.elements.connText.textContent = 'Socket xətası';
        }
    }

    async fetchData() {
        await Promise.all([
            this.fetchSignals(),
            this.fetchStats(),
            this.fetchHistory()
        ]);
        
        const now = new Date();
        this.elements.statUpdate.textContent = now.toLocaleTimeString('az-AZ');
    }

    async fetchSignals() {
        try {
            const res = await fetch(`/api/signals?timeframe=${this.timeframe}`);
            if (res.ok) {
                this.signals = await res.json();
                this.renderSignalCards();
            }
        } catch (e) {
            console.error('Siqnalları yükləyərkən xəta:', e);
        }
    }

    async fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (res.ok) {
                const stats = await res.json();
                this.animateValue(this.elements.statTotal, parseInt(this.elements.statTotal.textContent), stats.total_signals, 500);
                this.animateValue(this.elements.statPairs, parseInt(this.elements.statPairs.textContent), stats.active_pairs, 500);
                this.elements.statWinrate.textContent = `${stats.win_rate.toFixed(1)}%`;
            }
        } catch (e) {
            console.error('Statistika yüklənərkən xəta:', e);
        }
    }

    async fetchHistory() {
        try {
            const res = await fetch('/api/history');
            if (res.ok) {
                const history = await res.json();
                this.renderHistory(history);
            }
        } catch (e) {
            console.error('Tarixçə yüklənərkən xəta:', e);
        }
    }

    renderSignalCards() {
        this.elements.signalGrid.innerHTML = '';
        
        if (!this.signals || this.signals.length === 0) {
            this.elements.emptyState.classList.remove('hidden');
            return;
        }
        
        this.elements.emptyState.classList.add('hidden');
        
        this.signals.forEach((signal, index) => {
            const card = document.createElement('div');
            card.className = `signal-card glass-panel ${signal.direction.toLowerCase()}`;
            card.style.animationDelay = `${index * 0.1}s`;
            
            const dirClass = signal.direction === 'BUY' ? 'buy-text' : 'sell-text';
            const dirArrow = signal.direction === 'BUY' ? '↑' : '↓';
            
            card.innerHTML = `
                <div class="card-header">
                    <div class="pair-name">${signal.display_name}</div>
                    <div class="tf-badge">${signal.timeframe}</div>
                </div>
                <div class="card-body">
                    <div class="direction">
                        <span class="dir-text ${dirClass}">${dirArrow} ${signal.direction}</span>
                        <span class="price-text">${signal.price.toFixed(5)}</span>
                    </div>
                    <div class="confidence-wrapper" style="--progress: ${signal.confidence}%">
                        <div class="confidence-value">${signal.confidence}%</div>
                    </div>
                </div>
            `;
            
            card.addEventListener('click', () => this.showSignalDetail(signal));
            this.elements.signalGrid.appendChild(card);
        });
    }

    showSignalDetail(signal) {
        document.getElementById('modal-title').textContent = `${signal.display_name} - ${signal.timeframe}`;
        
        const dirColor = signal.direction === 'BUY' ? 'var(--buy)' : 'var(--sell)';
        
        let html = `
            <div style="display:flex; justify-content: space-between; margin-bottom: 20px;">
                <div>
                    <h3 style="color:${dirColor}; font-size:1.5rem">${signal.direction}</h3>
                    <p style="font-family: var(--font-mono); color: var(--text-muted)">Qiymət: ${signal.price}</p>
                </div>
                <div>
                    <h3 style="font-size:1.5rem">${signal.confidence}%</h3>
                    <p style="color: var(--text-muted)">Etibar dərəcəsi</p>
                </div>
            </div>
        `;
        
        this.elements.modalInfo.innerHTML = html;
        
        if (signal.chart_path) {
            this.elements.modalChart.src = `/charts/${signal.chart_path}`;
            this.elements.modalChart.style.display = 'block';
        } else {
            this.elements.modalChart.style.display = 'none';
        }
        
        this.elements.modal.classList.add('active');
    }

    renderHistory(history) {
        this.elements.historyBody.innerHTML = '';
        
        history.slice(0, 15).forEach(item => {
            const tr = document.createElement('tr');
            const date = new Date(item.timestamp);
            const timeStr = date.toLocaleTimeString('az-AZ');
            const dirColor = item.direction === 'BUY' ? 'var(--buy)' : 'var(--sell)';
            
            tr.innerHTML = `
                <td>${timeStr}</td>
                <td>${item.display_name}</td>
                <td style="color: ${dirColor}; font-weight: bold;">${item.direction}</td>
                <td>${item.confidence}%</td>
                <td>${item.price}</td>
                <td>${item.timeframe}</td>
            `;
            this.elements.historyBody.appendChild(tr);
        });
    }

    updateClock() {
        const now = new Date();
        this.elements.clock.textContent = now.toLocaleTimeString('az-AZ', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        
        // Simple icon
        const icon = document.createElement('div');
        icon.style.width = '10px';
        icon.style.height = '10px';
        icon.style.borderRadius = '50%';
        icon.style.background = 'var(--primary)';
        icon.style.boxShadow = '0 0 10px var(--primary-glow)';
        
        const text = document.createElement('span');
        text.textContent = message;
        
        toast.appendChild(icon);
        toast.appendChild(text);
        
        this.elements.toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    playNotificationSound() {
        try {
            if (!this.audioCtx) {
                this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            if (this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }
            
            const oscillator = this.audioCtx.createOscillator();
            const gainNode = this.audioCtx.createGain();
            
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, this.audioCtx.currentTime); // A5
            oscillator.frequency.exponentialRampToValueAtTime(1760, this.audioCtx.currentTime + 0.1);
            
            gainNode.gain.setValueAtTime(0, this.audioCtx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, this.audioCtx.currentTime + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.5);
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioCtx.destination);
            
            oscillator.start();
            oscillator.stop(this.audioCtx.currentTime + 0.5);
        } catch (e) {
            console.error("Səs səsləndirilərkən xəta:", e);
        }
    }
    
    animateValue(obj, start, end, duration) {
        if (start === end) return;
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.innerHTML = end;
            }
        };
        window.requestAnimationFrame(step);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new DashboardApp();
    app.init();
});
