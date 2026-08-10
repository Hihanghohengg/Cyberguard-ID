/**
 * CyberGuard-ID — Pure URL-Only Minimalist Home Dashboard
 * Focus: Direct YouTube URL input + Execute Button + Clean History Table (Icon-only actions)
 */
const HomePage = {
    currentPollInterval: null,

    async render(container) {
        container.innerHTML = `
            <div class="hero-clean-container">
                <div class="hero-clean-header">
                    <h1>Pemeriksaan Komentar YouTube</h1>
                    <p>Masukkan link video YouTube di bawah ini untuk mendeteksi ujaran kebencian, kata kasar, dan komentar berbahaya secara otomatis.</p>
                </div>

                <!-- Single Ultra-Clean Input Card -->
                <div class="input-main-card">
                    <form id="yt-scan-form" onsubmit="HomePage.handleSubmitYouTube(event)">
                        <div class="clean-input-box">
                            <label for="yt-url-input" class="form-label" style="font-size: 1.05rem; font-weight: 700; color: #ffffff; margin-bottom: 10px; display: block;">
                                Link / URL Video YouTube:
                            </label>
                            <div class="clean-input-row">
                                <input 
                                    type="text" 
                                    id="yt-url-input" 
                                    class="input-large" 
                                    placeholder="Tempel link video YouTube di sini (contoh: https://www.youtube.com/watch?v=...)" 
                                    autocomplete="off"
                                    required
                                    autofocus
                                />
                                <button type="submit" class="btn-large" id="btn-submit-yt">
                                    <span class="material-symbols-outlined">search</span>
                                    <span>Periksa Sekarang</span>
                                </button>
                            </div>
                        </div>
                    </form>

                    <!-- Progress Indicator Box (Active during scan) -->
                    <div id="scan-progress-box" class="hidden" style="margin-top: 20px; padding: 20px; background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--accent);">
                        <div class="flex items-center justify-between mb-2">
                            <span id="progress-status-text" style="font-weight: 700; color: #ffffff; font-size: 1.05rem;">Sedang memproses...</span>
                            <span id="progress-percentage-text" style="font-weight: 800; color: var(--accent); font-size: 1.1rem;">0%</span>
                        </div>
                        <div style="height: 12px; background: var(--bg-input); border-radius: var(--radius-full); overflow: hidden;">
                            <div id="progress-fill-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #0284c7, #38bdf8); transition: width 0.3s ease;"></div>
                        </div>
                        <p id="progress-detail-text" style="font-size: 0.92rem; color: var(--text-secondary); margin-top: 10px;">Mohon tunggu sebentar, sistem sedang memindai komentar...</p>
                    </div>
                </div>
            </div>

            <!-- Recent Analyses History Card -->
            <div class="card-soc" id="recent-analyses-card">
                <div class="card-header-sep">
                    <div class="card-title">
                        <span class="material-symbols-outlined text-primary">history</span>
                        <span>Riwayat Pemeriksaan Terakhir</span>
                    </div>
                    <a href="#/results" class="btn btn-secondary btn-sm">
                        <span>Lihat Semua Hasil</span>
                        <span class="material-symbols-outlined" style="font-size: 16px;">arrow_forward</span>
                    </a>
                </div>
                <div class="card-body" style="padding: 0;">
                    <div id="recent-list-container">
                        <div class="loading-screen" style="padding: 30px;">
                            <div class="spinner"></div>
                            <p>Memuat riwayat...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Check if there was a passed quick URL
        const quickUrl = sessionStorage.getItem('cyberguard_quick_url');
        if (quickUrl) {
            sessionStorage.removeItem('cyberguard_quick_url');
            const input = document.getElementById('yt-url-input');
            if (input) input.value = quickUrl;
        }

        await this.loadRecentHistory();
    },

    async handleSubmitYouTube(event) {
        event.preventDefault();
        const urlInput = document.getElementById('yt-url-input');
        const btnSubmit = document.getElementById('btn-submit-yt');

        const url = urlInput?.value.trim();
        if (!url) {
            Toast.warning('Input Kosong', 'Silakan masukkan link video YouTube.');
            return;
        }

        btnSubmit.disabled = true;
        this.showProgress(true, 'Menghubungi YouTube & Memulai Analisis...', 10);

        try {
            const resp = await API.startYouTubeAnalysis({
                video_url: url,
                max_comments: 5000,
                include_replies: true,
            });

            const analysisId = resp.analysis_id || resp.id;
            this.pollAnalysisProgress(analysisId);
        } catch (err) {
            btnSubmit.disabled = false;
            this.showProgress(false);
            Toast.error('Gagal Memulai Pemeriksaan', err.message || 'Terjadi kesalahan pada server.');
        }
    },

    showProgress(show, text = '', pct = 0) {
        const box = document.getElementById('scan-progress-box');
        const statusText = document.getElementById('progress-status-text');
        const pctText = document.getElementById('progress-percentage-text');
        const fillBar = document.getElementById('progress-fill-bar');

        if (!box) return;

        if (show) {
            box.classList.remove('hidden');
            if (statusText) statusText.textContent = text;
            if (pctText) pctText.textContent = `${pct}%`;
            if (fillBar) fillBar.style.width = `${pct}%`;
        } else {
            box.classList.add('hidden');
        }
    },

    pollAnalysisProgress(analysisId) {
        if (this.currentPollInterval) clearInterval(this.currentPollInterval);
        if (this.currentSseStream) this.currentSseStream.close();

        let progress = 25;
        this.currentSseStream = API.streamSSE(`/api/analyze/${analysisId}/progress`, {
            onMessage: (data) => {
                if (!data.done) {
                    progress = Math.min(progress + 15, 90);
                    this.showProgress(true, data.message || 'Sedang memproses data...', progress);
                }
            },
            onDone: () => {
                this.showProgress(true, 'Pemeriksaan Selesai! Membuka hasil...', 100);
                Toast.success('Analisis Selesai', 'Mengarahkan ke halaman Hasil Analisis.');
                setTimeout(() => {
                    window.location.hash = `#/results?id=${analysisId}`;
                }, 800);
            },
            onError: (err) => {
                this.showProgress(false);
                const btnYt = document.getElementById('btn-submit-yt');
                if (btnYt) btnYt.disabled = false;
                Toast.error('Analisis Gagal', err || 'Proses analisis mengalami kendala.');
            }
        });
    },

    async loadRecentHistory() {
        const container = document.getElementById('recent-list-container');
        if (!container) return;

        try {
            const analyses = await API.getAnalyses(6);
            if (!analyses || analyses.length === 0) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 36px 20px; color: var(--text-muted);">
                        <span class="material-symbols-outlined" style="font-size: 42px; margin-bottom: 8px; opacity: 0.6;">inbox</span>
                        <p style="font-size: 1rem; font-weight: 600; color: var(--text-secondary);">Belum ada riwayat pemeriksaan</p>
                        <p style="font-size: 0.92rem;">Masukkan link video YouTube di atas untuk memulai pemeriksaan pertama.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="table-container" style="border: none;">
                    <table class="cyber-table">
                        <thead>
                            <tr>
                                <th>Judul Video YouTube</th>
                                <th>Waktu Pemeriksaan</th>
                                <th>Jumlah Komentar</th>
                                <th>Status Risiko</th>
                                <th style="text-align: right; width: 100px;"></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${analyses.map(item => {
                                const title = item.video_title || `Video (${item.video_id || item.id})`;
                                const dateStr = item.created_at ? new Date(item.created_at).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '-';
                                const total = item.total_comments || 0;
                                const harmful = item.harmful_count || 0;
                                const isCritical = (item.critical_risk_count || 0) > 0;
                                
                                let riskBadge = `<span class="chip chip-aman">Aman</span>`;
                                if (isCritical) {
                                    riskBadge = `<span class="chip chip-kritis">Kritis (${harmful} Berbahaya)</span>`;
                                } else if (harmful > 0) {
                                    riskBadge = `<span class="chip chip-sedang">${harmful} Perlu Perhatian</span>`;
                                }

                                return `
                                    <tr>
                                        <td>
                                            <div style="font-weight: 700; color: #ffffff; max-width: 380px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 1rem;">
                                                ${escapeHtml(title)}
                                            </div>
                                            <div style="font-size: 0.82rem; color: var(--text-muted);">ID: ${item.id}</div>
                                        </td>
                                        <td style="color: var(--text-secondary); font-size: 0.92rem;">${dateStr}</td>
                                        <td style="font-weight: 700; color: #ffffff; font-size: 0.95rem;">${total} Komentar</td>
                                        <td>${riskBadge}</td>
                                        <td style="text-align: right; white-space: nowrap;">
                                            <div style="display: inline-flex; align-items: center; gap: 8px; justify-content: flex-end;">
                                                <a href="#/results?id=${item.id}" class="btn btn-primary btn-sm" title="Buka Hasil Analisis" style="padding: 6px 10px; min-width: unset; display: inline-flex; align-items: center; justify-content: center;">
                                                    <span class="material-symbols-outlined" style="font-size: 18px;">visibility</span>
                                                </a>
                                                <button type="button" class="btn btn-danger btn-sm" onclick="App.confirmDeleteAnalysis('${item.id}', '${escapeHtml(title).replace(/'/g, "\\'")}', () => HomePage.loadRecentHistory())" title="Hapus Riwayat" style="padding: 6px 10px; min-width: unset; display: inline-flex; align-items: center; justify-content: center; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171;" onmouseover="this.style.background='rgba(239, 68, 68, 0.3)'" onmouseout="this.style.background='rgba(239, 68, 68, 0.15)'">
                                                    <span class="material-symbols-outlined" style="font-size: 18px;">delete</span>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (err) {
            container.innerHTML = `<div style="padding: 20px; color: var(--danger-text);">Gagal memuat riwayat: ${err.message}</div>`;
        }
    }
};

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
