/**
 * CyberGuard-ID — API Client Module
 * Handles all HTTP requests, data normalization, and SSE streaming.
 */
const API = {
    baseUrl: '',

    // Label mapping dictionary
    labelMap: {
        'normal_konstruktif': 'C0',
        'bahasa_kasar': 'C1',
        'kritik_wajar': 'C2',
        'hate_speech': 'C3',
        'personal_harassment': 'C4',
        'sexual_harassment': 'C5',
        'threat_intimidation': 'C6',
        'uncertain': 'C7',
    },

    inverseLabelMap: {
        'C0': 'normal_konstruktif',
        'C1': 'bahasa_kasar',
        'C2': 'kritik_wajar',
        'C3': 'hate_speech',
        'C4': 'personal_harassment',
        'C5': 'sexual_harassment',
        'C6': 'threat_intimidation',
        'C7': 'uncertain',
    },

    riskMap: {
        'low': 'rendah',
        'medium': 'sedang',
        'high': 'tinggi',
        'critical': 'kritis',
    },

    getApiKey() {
        const match = document.cookie.match(new RegExp('(^| )stride_api_key=([^;]+)'));
        return match ? match[2] : null;
    },

    async request(method, path, body = null, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const config = {
            method,
            headers: {},
            ...options,
        };

        const apiKey = this.getApiKey();
        if (apiKey) {
            config.headers['X-API-Key'] = apiKey;
        }

        if (body && !(body instanceof FormData)) {
            config.headers['Content-Type'] = 'application/json';
            config.body = JSON.stringify(body);
        } else if (body instanceof FormData) {
            config.body = body;
        }

        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(err.detail || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Tidak dapat terhubung ke server');
            }
            throw error;
        }
    },

    get(path) { return this.request('GET', path); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    delete(path) { return this.request('DELETE', path); },

    async upload(path, file, extraFields = {}) {
        const form = new FormData();
        form.append('file', file);
        for (const [k, v] of Object.entries(extraFields)) {
            form.append(k, v);
        }
        return this.request('POST', path, form);
    },

    streamSSE(path, { onMessage, onError, onDone }) {
        let url = `${this.baseUrl}${path}`;
        const apiKey = this.getApiKey();
        if (apiKey) {
            url += (url.includes('?') ? '&' : '?') + `api_key=${apiKey}`;
        }
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.error) {
                    onError?.(data.error);
                    eventSource.close();
                    return;
                }
                onMessage?.(data);
                if (data.done) {
                    onDone?.(data);
                    eventSource.close();
                }
            } catch (e) {
                // Heartbeats
            }
        };

        eventSource.onerror = () => {
            onError?.('Koneksi ke server terputus');
            eventSource.close();
        };

        return {
            close: () => eventSource.close(),
        };
    },

    // --- High-Level Analysis Endpoints ---

    startAnalysis(url, name, maxComments = 100, includeReplies = true) {
        return this.post('/api/analyze', { url, name, max_comments: maxComments, include_replies: includeReplies });
    },

    startYouTubeAnalysis(payload) {
        return this.post('/api/analyze', {
            url: payload.video_url || payload.url,
            name: payload.name || '',
            max_comments: payload.max_comments || 500,
            include_replies: payload.include_replies !== false,
        });
    },

    uploadCSV(file, name = '') {
        return this.upload('/api/analyze/csv', file, { name });
    },

    getAnalyses(limit = 50) {
        return this.get(`/api/analyses?limit=${limit}`);
    },

    async getAnalysis(id) {
        const raw = await this.get(`/api/analysis/${id}`);
        if (!raw) return null;

        // If wrapped in { analysis: {...}, stats: {...}, clusters: [...] }
        if (raw.analysis) {
            return {
                ...raw.analysis,
                id: raw.analysis.id || id,
                video_title: raw.analysis.video_title || raw.analysis.name || `Video (${raw.analysis.video_id || id})`,
                created_at: raw.analysis.completed_at || raw.analysis.started_at,
                total_comments: raw.analysis.total_comments || (raw.stats ? raw.stats.total_comments : 0),
                harmful_count: raw.analysis.toxic_count || raw.analysis.harmful_count || 0,
                high_risk_count: raw.analysis.high_count || 0,
                critical_risk_count: raw.analysis.critical_count || 0,
                abstention_count: raw.analysis.uncertain_count || 0,
                category_distribution: raw.stats ? (raw.stats.category_distribution || {}) : {},
                risk_distribution: raw.stats ? (raw.stats.risk_distribution || {}) : {},
                clusters: raw.clusters || [],
                raw: raw,
            };
        }
        return raw;
    },

    async getComments(id, options = {}) {
        const page = options.page || 1;
        const perPage = options.per_page || 25;
        const filters = {};

        if (options.priority) {
            if (options.priority === 'harmful') {
                filters.risk_level = 'high';
            } else if (options.priority === 'review') {
                filters.risk_level = 'medium';
            } else if (options.priority === 'safe') {
                filters.risk_level = 'low';
            }
        }
        if (options.search) {
            filters.search = options.search;
        }

        const raw = await this.getAnalysisComments(id, page, perPage, filters);
        const mappedItems = (raw.comments || []).map(item => ({
            ...item,
            text_original: item.original_text || item.text_original || item.text || '',
            predicted_label: this.labelMap[item.predicted_label] || item.predicted_label || 'C0',
            final_label: item.reviewer_label ? (this.labelMap[item.reviewer_label] || item.reviewer_label) : (this.labelMap[item.predicted_label] || item.predicted_label || 'C0'),
            risk_level: this.riskMap[item.risk_level] || item.risk_level || 'rendah',
            is_reviewed: !!item.reviewer_label,
        }));

        return {
            items: mappedItems,
            total: raw.total || 0,
            pages: raw.total_pages || 0,
        };
    },

    getAnalysisComments(id, page = 1, perPage = 50, filters = {}) {
        const params = new URLSearchParams({ page, per_page: perPage });
        if (filters.risk_level) params.set('risk_level', filters.risk_level);
        if (filters.label) params.set('label', filters.label);
        if (filters.search) params.set('search', filters.search);
        return this.get(`/api/analysis/${id}/comments?${params}`);
    },

    async submitReview(analysisId, payload) {
        const commentId = payload.comment_id || payload.id;
        const targetLabel = payload.corrected_label || payload.reviewer_label;
        const reviewer_label = this.inverseLabelMap[targetLabel] || targetLabel;
        const notes = payload.notes || 'Koreksi pengawas manusia';

        return this.post(`/api/analysis/${analysisId}/comments/${commentId}/review`, {
            reviewer_label,
            notes,
        });
    },

    saveCommentReview(analysisId, commentId, data) {
        return this.post(`/api/analysis/${analysisId}/comments/${commentId}/review`, data);
    },

    deleteAnalysis(id) {
        return this.delete(`/api/analysis/${id}`);
    },

    clearAllAnalyses() {
        return this.delete('/api/analyses');
    },

    // Adaptive Intelligence
    getAdaptiveStats() {
        return this.get('/api/adaptive/stats');
    },

    // Reports
    getReportSummary(analysisId) {
        return this.get(`/api/reports/${analysisId}`);
    },

    regenerateReport(analysisId) {
        return this.post(`/api/reports/${analysisId}/regenerate`);
    },

    getReportDownloadUrl(analysisId, format) {
        const apiKey = this.getApiKey();
        const suffix = apiKey ? `?api_key=${apiKey}` : '';
        return `${this.baseUrl}/api/reports/${analysisId}/${format}${suffix}`;
    },

    // System
    getSystemStatus() {
        return this.get('/api/system/status');
    },

    getLabelSchema() {
        return this.get('/api/system/labels');
    },

    // Dataset
    getDatasetFiles() {
        return this.get('/api/dataset/files');
    },

    previewDataset(filename, page = 1, perPage = 50) {
        return this.get(`/api/dataset/files/${filename}/preview?page=${page}&per_page=${perPage}`);
    },

    updateLabel(filename, rowIndex, label) {
        return this.put(`/api/dataset/files/${filename}/label`, { row_index: rowIndex, label });
    },

    uploadDataset(file, name = '') {
        return this.upload('/api/dataset/upload', file, { name });
    },
};

// Make globally available
window.API = API;
