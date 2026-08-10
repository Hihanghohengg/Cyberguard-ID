/**
 * CyberGuard-ID — Stitch Refined Dataset Management & Labeling Page
 */
const DatasetPage = {
    currentFilename: null,
    currentPage: 1,
    labelSchema: null,

    async render(container) {
        container.innerHTML = `
            <div class="flex items-center justify-between mb-4" style="flex-wrap: wrap; gap: 16px;">
                <div class="page-header" style="margin-bottom: 0;">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="chip chip-sedang font-mono">CORPUS MANAGER</span>
                        <span class="text-xs text-muted">Anotasi Data Pelatihan</span>
                    </div>
                    <h1 style="font-size: 1.5rem; font-weight: 800; color: var(--text-primary);">Manajemen & Pelabelan Dataset</h1>
                    <p class="text-secondary text-sm">Kelola korpus data komentar untuk pelatihan dan fine-tuning model klasifikasi.</p>
                </div>
                <div class="flex gap-2">
                    <button class="btn btn-primary btn-sm flex items-center gap-1" id="btn-train-model" onclick="DatasetPage.trainModel()">
                        <span class="material-symbols-outlined text-xs">model_training</span>
                        <span>Latih Model</span>
                    </button>
                    <button class="btn btn-secondary btn-sm flex items-center gap-1" onclick="document.getElementById('dataset-upload-input').click()">
                        <span class="material-symbols-outlined text-xs">upload_file</span>
                        <span>Unggah Dataset CSV</span>
                    </button>
                    <input type="file" id="dataset-upload-input" accept=".csv" class="hidden" onchange="DatasetPage.handleUpload(event)" />
                    <button class="btn btn-secondary btn-sm flex items-center gap-1" id="btn-export-dataset" onclick="DatasetPage.exportDataset()" disabled>
                        <span class="material-symbols-outlined text-xs">download</span>
                        <span>Ekspor CSV</span>
                    </button>
                </div>
            </div>

            <!-- Dataset Selector & Distribution Charts (Stitch SOC Grid) -->
            <div class="grid-soc mb-4" style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
                <!-- Dataset File List -->
                <div class="card-soc">
                    <div class="card-header-sep">
                        <div class="card-title">
                            <span class="material-symbols-outlined text-primary">folder</span>
                            <span>Berkas Dataset di Server (data/raw)</span>
                        </div>
                    </div>
                    <div class="card-body" id="dataset-files-list" style="padding: var(--space-4);">
                        <div class="loading-screen" style="padding: 20px 0;"><div class="spinner"></div></div>
                    </div>
                </div>

                <!-- Label Distribution Chart -->
                <div class="card-soc">
                    <div class="card-header-sep">
                        <div class="card-title">
                            <span class="material-symbols-outlined text-primary">bar_chart</span>
                            <span>Distribusi Anotasi Label</span>
                        </div>
                    </div>
                    <div class="card-body" style="padding: var(--space-4);">
                        <div style="position: relative; height: 160px;">
                            <canvas id="chart-dataset-labels"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Label Taxonomy Reference -->
            <div class="card-soc mb-4">
                <div class="card-header-sep" onclick="DatasetPage.toggleTaxonomy()" style="cursor: pointer;">
                    <div class="card-title">
                        <span class="material-symbols-outlined text-primary">library_books</span>
                        <span>Taksonomi & Standar Pelabelan CyberGuard (C0–C4)</span>
                    </div>
                    <span class="material-symbols-outlined" id="taxonomy-toggle-icon">expand_more</span>
                </div>
                <div class="card-body hidden" id="taxonomy-content" style="padding: var(--space-4);">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px;" id="taxonomy-grid">
                        <!-- Populated by JS -->
                    </div>
                </div>
            </div>

            <!-- Dataset Preview & Inline Labeling Table -->
            <div class="card-soc">
                <div class="card-header-sep">
                    <div>
                        <div class="card-title">
                            <span class="material-symbols-outlined text-primary">edit_note</span>
                            <span id="dataset-table-title">Pratinjau & Pelabelan Data</span>
                        </div>
                        <span class="text-xs text-muted" id="dataset-table-subtitle">Pilih berkas dataset untuk mulai mengedit</span>
                    </div>
                </div>
                <div class="card-body" style="padding: var(--space-4);">
                    <div class="table-container mb-4">
                        <table class="cyber-table" id="dataset-table">
                            <thead>
                                <tr>
                                    <th style="width: 60px;">No</th>
                                    <th>Teks Komentar</th>
                                    <th style="width: 240px;">Anotasi Label (Inline Editor)</th>
                                </tr>
                            </thead>
                            <tbody id="dataset-tbody">
                                <tr><td colspan="3" style="text-align: center; padding: 30px; color: var(--text-muted);">Belum ada dataset yang dipilih.</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <div id="dataset-pagination"></div>
                </div>
            </div>

            <!-- Training Progress Modal -->
            <div id="train-modal" class="modal-overlay hidden" style="position: fixed; inset: 0; z-index: 9999; background: rgba(3, 7, 18, 0.78); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; padding: 20px;">
                <div class="modal-card" style="max-width: 460px; width: 100%; padding: 26px; border: 1px solid var(--border-strong); background: var(--bg-card); border-radius: var(--radius-lg); box-shadow: var(--shadow-xl);">
                    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px;">
                        <div class="modal-icon flex items-center justify-center" style="width: 48px; height: 48px; border-radius: 50%; background: rgba(59, 130, 246, 0.1); color: #3b82f6;">
                            <span class="material-symbols-outlined" style="font-size: 24px;">psychology</span>
                        </div>
                        <div>
                            <h3 style="font-size: 1.25rem; font-weight: 800; color: #ffffff; margin-bottom: 4px;">Melatih Model AI</h3>
                            <div id="train-modal-status" style="font-size: 0.9rem; color: var(--text-secondary);">Mempersiapkan...</div>
                        </div>
                    </div>
                    
                    <div class="progress-bar-container" style="background: var(--bg-body); border-radius: 99px; height: 10px; overflow: hidden; margin-bottom: 12px; border: 1px solid var(--border);">
                        <div id="train-modal-progress" class="progress-bar" style="height: 100%; background: linear-gradient(90deg, var(--primary), var(--accent)); width: 0%; transition: width 0.3s ease;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                        <span id="train-modal-step">Langkah 0 dari 5</span>
                        <span id="train-modal-pct">0%</span>
                    </div>

                    <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px;">
                        <button type="button" class="btn btn-primary hidden" id="train-modal-ok-btn" onclick="document.getElementById('train-modal').classList.add('hidden')">Tutup</button>
                    </div>
                </div>
            </div>
        `;

        await this.init();
    },

    async init() {
        try {
            this.labelSchema = await API.getLabelSchema();
            this.renderTaxonomy(this.labelSchema);
            await this.loadDatasetFiles();
        } catch (e) {
            Toast.error('Gagal Memuat Skema', e.message);
        }
    },

    renderTaxonomy(schema) {
        const grid = document.getElementById('taxonomy-grid');
        if (!grid || !schema || !schema.categories) return;

        let html = '';
        schema.categories.forEach(cat => {
            html += `
                <div style="background: var(--bg-card); padding: 12px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border);">
                    <div class="flex items-center justify-between mb-2">
                        ${DataTable.labelBadge(cat.internal_name)}
                        <span class="text-xs text-muted font-mono">Skor: ${cat.base_score}</span>
                    </div>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 6px; line-height: 1.4;">${DataTable.escapeHtml(cat.definition)}</p>
                    <div class="text-xs text-muted">Aksi: <span style="color: var(--accent); font-weight: 600;">${DataTable.escapeHtml(cat.recommended_action)}</span></div>
                </div>
            `;
        });
        grid.innerHTML = html;
    },

    toggleTaxonomy() {
        const content = document.getElementById('taxonomy-content');
        const icon = document.getElementById('taxonomy-toggle-icon');
        if (!content) return;

        const isHidden = content.classList.toggle('hidden');
        if (icon) {
            icon.textContent = isHidden ? 'expand_more' : 'expand_less';
        }
    },

    async loadDatasetFiles() {
        const container = document.getElementById('dataset-files-list');
        if (!container) return;

        try {
            const files = await API.getDatasetFiles();

            if (files.length === 0) {
                container.innerHTML = '<p class="text-muted text-xs">Tidak ada berkas CSV di folder <code>data/raw</code>. Silakan unggah dataset baru.</p>';
                return;
            }

            let html = '<div class="flex flex-col gap-2">';
            files.forEach((f, idx) => {
                const isSelected = f.filename === this.currentFilename || (!this.currentFilename && idx === 0);
                if (isSelected && !this.currentFilename) {
                    this.currentFilename = f.filename;
                }

                html += `
                    <div 
                        onclick="DatasetPage.selectDataset('${f.filename}')" 
                        class="flex items-center justify-between gap-3" 
                        style="padding: 10px 14px; border: 1px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}; border-radius: var(--radius-sm); cursor: pointer; background: ${isSelected ? 'rgba(56, 189, 248, 0.08)' : 'var(--bg-card)'};"
                    >
                        <div>
                            <div class="font-semibold text-xs text-primary font-mono">${DataTable.escapeHtml(f.filename)}</div>
                            <div class="text-xs text-muted">${f.rows.toLocaleString()} baris • ${f.size_kb} KB</div>
                        </div>
                        <span class="material-symbols-outlined text-muted" style="font-size: 18px;">chevron_right</span>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;

            if (this.currentFilename) {
                await this.previewDataset(this.currentFilename, 1);
            }
        } catch (e) {
            container.innerHTML = `<p style="color: var(--danger); font-size: 0.82rem;">Gagal: ${e.message}</p>`;
        }
    },

    async selectDataset(filename) {
        this.currentFilename = filename;
        await this.loadDatasetFiles();
        await this.previewDataset(filename, 1);
    },

    async previewDataset(filename, page = 1) {
        this.currentPage = page;
        const tbody = document.getElementById('dataset-tbody');
        const title = document.getElementById('dataset-table-title');
        const subtitle = document.getElementById('dataset-table-subtitle');
        const btnExport = document.getElementById('btn-export-dataset');

        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 20px;"><div class="spinner" style="margin: 0 auto;"></div></td></tr>';
        if (title) title.textContent = `Pratinjau: ${filename}`;
        if (btnExport) btnExport.disabled = false;

        try {
            const data = await API.previewDataset(filename, page, 25);
            if (subtitle) subtitle.textContent = `Total ${data.total.toLocaleString()} baris komentar • Halaman ${data.page} dari ${data.total_pages}`;

            if (data.label_distribution) {
                Charts.datasetBar('chart-dataset-labels', data.label_distribution);
            }

            if (!data.rows || data.rows.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 30px; color: var(--text-muted);">Dataset kosong.</td></tr>';
                return;
            }

            const trainingLabels = this.labelSchema?.training_labels || [
                'normal_konstruktif', 'kritik_wajar', 'bahasa_kasar',
                'personal_harassment', 'hate_speech', 'sexual_harassment',
                'threat_intimidation'
            ];

            let html = '';
            data.rows.forEach((row, i) => {
                const rowIndex = row._index !== undefined ? row._index : ((page - 1) * 25 + i);
                const currentLabel = row.label || '';
                
                // Find text: try standard aliases, fallback to the first data column
                let text = row.text || row.comment || row.komentar || row.tweet || row.content;
                if (!text && text !== 0) {
                    const firstDataCol = Object.keys(row).find(k => k !== '_index' && k !== 'label');
                    text = firstDataCol ? row[firstDataCol] : '';
                }
                text = text || '';

                let optionsHtml = '<option value="">-- Belum Dilabeli --</option>';
                trainingLabels.forEach(lbl => {
                    const sel = lbl === currentLabel ? 'selected' : '';
                    optionsHtml += `<option value="${lbl}" ${sel}>${lbl}</option>`;
                });

                html += `
                    <tr>
                        <td class="text-muted font-mono text-xs">${rowIndex + 1}</td>
                        <td style="max-width: 480px;">
                            <span style="display: block; line-height: 1.45; font-size: 0.85rem; color: var(--text-primary);">${DataTable.escapeHtml(text)}</span>
                        </td>
                        <td>
                            <select class="form-select font-mono text-xs" style="padding: 4px 8px;" onchange="DatasetPage.handleLabelChange('${filename}', ${rowIndex}, this.value)">
                                ${optionsHtml}
                            </select>
                        </td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;

            const paginationContainer = document.getElementById('dataset-pagination');
            paginationContainer.innerHTML = DataTable.renderPagination(data.page, data.total_pages);
            DataTable.attachPagination('dataset-pagination', (p) => this.previewDataset(filename, p));

        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="3" style="color: var(--danger); text-align: center; padding: 20px;">Gagal memuat dataset: ${err.message}</td></tr>`;
        }
    },

    async handleLabelChange(filename, rowIndex, newLabel) {
        try {
            await API.updateLabel(filename, rowIndex, newLabel);
            Toast.success('Label Disimpan', `Baris #${rowIndex + 1} diupdate ke '${newLabel || 'kosong'}'`);
        } catch (err) {
            Toast.error('Gagal Update Label', err.message);
        }
    },

    async handleUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        try {
            Toast.info('Mengunggah', `Menyimpan ${file.name}...`);
            const res = await API.uploadDataset(file);
            Toast.success('Berhasil Diunggah', `${res.filename} (${res.rows} baris) siap digunakan.`);
            this.currentFilename = res.filename;
            await this.loadDatasetFiles();
        } catch (err) {
            Toast.error('Gagal Unggah', err.message);
        }
    },

    exportDataset() {
        if (!this.currentFilename) return;
        window.open(`/api/dataset/files/${this.currentFilename}/export`, '_blank');
    },

    async trainModel() {
        if (!confirm("Apakah Anda yakin ingin memulai proses pelatihan model sekarang? Proses ini akan berjalan di latar belakang dan mungkin memakan waktu beberapa saat.")) {
            return;
        }
        
        Toast.info('Memulai Pelatihan', 'Mempersiapkan pipeline...');
        
        try {
            // Trigger training via API
            const res = await fetch('/api/dataset/train', { method: 'POST' });
            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || 'Gagal memulai pelatihan');
            }
            
            const data = await res.json();
            Toast.success('Pelatihan Dimulai', data.message);
            
            // Listen to SSE progress
            if (window.EventSource) {
                const source = new EventSource('/api/dataset/train/progress');
                
                // create a simple modal dynamically
                const modalHtml = `
                    <div id="train-progress-modal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 9999; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px);">
                        <div style="background: var(--surface-2); padding: 30px; border-radius: 12px; border: 1px solid var(--border-color); width: 400px; text-align: center;">
                            <h3 style="margin-top: 0; color: var(--text-primary);">Melatih Model AI</h3>
                            <p id="train-status-text" style="color: var(--text-muted); margin-bottom: 20px;">Menunggu log...</p>
                            
                            <div style="width: 100%; background: var(--surface-3); border-radius: 8px; height: 12px; overflow: hidden; margin-bottom: 20px;">
                                <div id="train-progress-bar" style="width: 0%; height: 100%; background: var(--primary); transition: width 0.3s ease;"></div>
                            </div>
                            
                            <button id="btn-close-train-modal" class="btn btn-secondary" style="display: none; width: 100%;" onclick="document.getElementById('train-progress-modal').remove()">Tutup</button>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                source.onmessage = function(event) {
                    const progress = JSON.parse(event.data);
                    
                    const statusText = document.getElementById('train-status-text');
                    const progressBar = document.getElementById('train-progress-bar');
                    const btnClose = document.getElementById('btn-close-train-modal');
                    
                    if (progress.error) {
                        statusText.textContent = 'Error: ' + progress.error;
                        statusText.style.color = 'var(--danger)';
                        progressBar.style.background = 'var(--danger)';
                        btnClose.style.display = 'block';
                        source.close();
                        Toast.error('Pelatihan Gagal', progress.error);
                        return;
                    }
                    
                    if (progress.message) {
                        statusText.textContent = progress.message;
                    }
                    
                    if (progress.step !== undefined && progress.total_steps) {
                        const pct = Math.min(100, Math.round((progress.step / progress.total_steps) * 100));
                        progressBar.style.width = pct + '%';
                    }
                    
                    if (progress.done) {
                        statusText.textContent = 'Pelatihan Selesai 100%';
                        statusText.style.color = 'var(--success)';
                        progressBar.style.width = '100%';
                        progressBar.style.background = 'var(--success)';
                        btnClose.style.display = 'block';
                        source.close();
                        Toast.success('Berhasil', 'Model berhasil dilatih dan disimpan!');
                    }
                };
                
                source.onerror = function() {
                    console.error('SSE Error during training');
                    source.close();
                    document.getElementById('btn-close-train-modal').style.display = 'block';
                };
            }
            
        } catch (err) {
            Toast.error('Kesalahan', err.message);
        }
    }
};

window.DatasetPage = DatasetPage;
