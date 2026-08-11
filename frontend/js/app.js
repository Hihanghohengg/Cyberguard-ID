/**
 * CyberGuard-ID — Main Single Page Application Router & Orchestrator
 * Ergonomic Navigation & Human-Computer Interaction Controller
 */
const App = {
    pages: {
        'home': HomePage,
        'analyze': HomePage,      // Seamlessly directs to the clean home input
        'results': ResultsPage,
        'report': ResultsPage,    // Seamlessly directs to results with top download bar
    },

    currentPage: null,

    init() {
        Toast.init();
        this.setupNavigation();
        this.setupMobileMenu();
        this.setupKeyboardAccessibility();
        this.checkSystemHealth();

        // Listen for hash changes
        window.addEventListener('hashchange', () => this.handleRoute());

        // Handle initial route
        this.handleRoute();

        // Auto-close drawer on desktop resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                this.closeMobileSidebar();
            }
        });

        // Periodic health check every 30s
        setInterval(() => this.checkSystemHealth(), 30000);
    },

    setupNavigation() {
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const href = item.getAttribute('href');
                if (href) {
                    location.hash = href;
                }
                this.closeMobileSidebar();
            });
        });
    },

    setupMobileMenu() {
        const toggle = document.getElementById('menu-toggle');
        const overlay = document.getElementById('sidebar-overlay');
        const sidebar = document.getElementById('sidebar');

        if (toggle && sidebar && overlay) {
            toggle.addEventListener('click', () => {
                const isOpen = sidebar.classList.toggle('open');
                overlay.classList.toggle('active', isOpen);
                toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            });

            overlay.addEventListener('click', () => {
                this.closeMobileSidebar();
            });
        }
    },

    setupKeyboardAccessibility() {
        // Close modals and drawer on Escape key
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMobileSidebar();

                // Close any open modals
                document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                    modal.classList.remove('active');
                });
            }
        });
    },

    closeMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const toggle = document.getElementById('menu-toggle');
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
    },

    async checkSystemHealth() {
        const statusEl = document.getElementById('system-status');
        if (!statusEl) return;

        try {
            const status = await API.getSystemStatus();
            const dot = statusEl.querySelector('.status-dot');
            const span = statusEl.querySelector('span');

            const hasModel = status.api_status?.model_available;
            const hasDb = status.api_status?.database_ready;

            if (hasModel && hasDb) {
                dot.className = 'status-dot online';
                span.textContent = `Online • v${status.version || '2.0.0'}`;
            } else if (hasDb) {
                dot.className = 'status-dot warning';
                span.textContent = 'Model Belum Terlatih';
            } else {
                dot.className = 'status-dot offline';
                span.textContent = 'Sistem Offline';
            }
        } catch (e) {
            const dot = statusEl.querySelector('.status-dot');
            const span = statusEl.querySelector('span');
            if (dot) dot.className = 'status-dot offline';
            if (span) span.textContent = 'Koneksi Terputus';
        }
    },

    async handleRoute() {
        const hash = window.location.hash || '#/';
        const routePath = hash.split('?')[0].replace('#/', '') || 'home';
        const pageKey = routePath.split('/')[0] || 'home';

        const page = this.pages[pageKey] || HomePage;
        this.currentPage = pageKey;

        // Update active nav state
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
            const pageAttr = item.getAttribute('data-page');
            if (pageAttr === pageKey) {
                item.classList.add('active');
                item.setAttribute('aria-current', 'page');
            } else {
                item.classList.remove('active');
                item.removeAttribute('aria-current');
            }
        });

        // Scroll to top of main content
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Mount page
        const container = document.getElementById('page-container');
        if (container) {
            container.innerHTML = `
                <div class="loading-screen" aria-live="polite">
                    <div class="spinner"></div>
                    <p>Memuat halaman...</p>
                </div>
            `;

            try {
                await page.render(container);
                if (window.lucide) {
                    lucide.createIcons();
                }
            } catch (err) {
                container.innerHTML = `
                    <div class="card" style="margin-top: 40px; text-align: center; padding: 40px;">
                        <h2 class="text-danger mb-2">Terjadi Kesalahan</h2>
                        <p class="text-muted mb-4">${err.message}</p>
                        <a href="#/" class="btn btn-primary btn-sm">Kembali ke Dashboard</a>
                    </div>
                `;
                Toast.error('Gagal Memuat Halaman', err.message);
            }
        }
    },

    showConfirmDialog({ title, message, confirmText = 'Hapus', onConfirm }) {
        const modal = document.getElementById('app-confirm-modal');
        const titleEl = document.getElementById('confirm-modal-title');
        const descEl = document.getElementById('confirm-modal-desc');
        const cancelBtn = document.getElementById('confirm-modal-cancel-btn');
        const okBtn = document.getElementById('confirm-modal-ok-btn');

        if (!modal) return;

        if (titleEl) titleEl.textContent = title || 'Konfirmasi Tindakan';
        if (descEl) descEl.innerHTML = message || 'Apakah Anda yakin?';
        if (okBtn) okBtn.textContent = confirmText;

        const closeModal = () => {
            modal.classList.remove('active');
            modal.classList.add('hidden');
            cancelBtn?.removeEventListener('click', onCancel);
            okBtn?.removeEventListener('click', onOk);
            modal.removeEventListener('click', onBackdrop);
            document.removeEventListener('keydown', onKeyDown);
        };

        const onCancel = () => closeModal();
        const onOk = async () => {
            closeModal();
            if (typeof onConfirm === 'function') {
                await onConfirm();
            }
        };
        const onBackdrop = (e) => {
            if (e.target === modal) closeModal();
        };
        const onKeyDown = (e) => {
            if (e.key === 'Escape') closeModal();
        };

        cancelBtn?.addEventListener('click', onCancel);
        okBtn?.addEventListener('click', onOk);
        modal.addEventListener('click', onBackdrop);
        document.addEventListener('keydown', onKeyDown);

        modal.classList.remove('hidden');
        modal.classList.add('active');
    },

    confirmDeleteAnalysis(id, name, onDeleted = null) {
        const safeName = name ? this.escapeHtml(name) : id;
        this.showConfirmDialog({
            title: 'Hapus Riwayat Pemeriksaan?',
            message: `Apakah Anda yakin ingin menghapus riwayat pemeriksaan untuk <strong>"${safeName}"</strong>?<br><br><span style="color: var(--text-muted); font-size: 0.88rem;">Seluruh data analisis dan komentar video ini akan dihapus secara permanen dari sistem.</span>`,
            confirmText: 'Ya, Hapus',
            onConfirm: async () => {
                try {
                    await API.deleteAnalysis(id);
                    Toast.success('Riwayat Dihapus', `Analisis "${name || id}" berhasil dihapus.`);
                    if (onDeleted) {
                        onDeleted();
                    } else {
                        this.handleRoute();
                    }
                } catch (err) {
                    Toast.error('Gagal Menghapus', err.message);
                }
            }
        });
    },

    confirmClearAllAnalyses(onCleared = null) {
        this.showConfirmDialog({
            title: 'Hapus Semua Riwayat?',
            message: `Peringatan: Apakah Anda yakin ingin <strong>MENGHAPUS SEMUA</strong> riwayat analisis?<br><br><span style="color: var(--danger-text); font-size: 0.88rem;">Semua data riwayat pemeriksaan yang tersimpan akan dibersihkan total.</span>`,
            confirmText: 'Hapus Semua',
            onConfirm: async () => {
                try {
                    const res = await API.clearAllAnalyses();
                    Toast.success('Riwayat Dibersihkan', `Semua riwayat analisis (${res.deleted_count || 0} data) telah dihapus.`);
                    if (onCleared) {
                        onCleared();
                    } else {
                        this.handleRoute();
                    }
                } catch (err) {
                    Toast.error('Gagal Membersihkan Riwayat', err.message);
                }
            }
        });
    },

    escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
