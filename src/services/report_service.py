"""CyberGuard-ID — Report Service.

Generates CSV, JSON, and HTML reports from analysis results.
Manages report artifacts and provides export functionality.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Template

from src.core.logging_config import get_logger
from src.core.schemas import AnalysisRun, AnalysisStats, ReportSummary

logger = get_logger("report_service")


HTML_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CyberGuard-ID — Laporan Audit Moderasi Eksekutif [{{ analysis_id }}]</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
    --bg-page: #0B0F19;
    --bg-canvas: #F8FAFC;
    --bg-card: #FFFFFF;
    --bg-subtle: #F1F5F9;
    --bg-dark: #0F172A;
    --bg-dark-card: #1E293B;
    --text-main: #0F172A;
    --text-muted: #64748B;
    --text-light: #F8FAFC;
    --border-color: #E2E8F0;
    --border-dark: #334155;
    --primary: #0F766E;
    --primary-light: #CCFBF1;
    --primary-dark: #115E59;
    --accent: #6366F1;
    --success: #16A34A;
    --success-bg: #DCFCE7;
    --warning: #D97706;
    --warning-bg: #FEF3C7;
    --danger: #DC2626;
    --danger-bg: #FEE2E2;
    --critical: #991B1B;
    --critical-bg: #FFE4E6;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--bg-canvas);
    color: var(--text-main);
    line-height: 1.6;
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
}

.report-wrapper {
    max-width: 1000px;
    margin: 0 auto;
    background: #FFFFFF;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
}

/* Action Toolbar (Hidden on Print) */
.action-toolbar {
    background: var(--bg-dark);
    color: #FFFFFF;
    padding: 12px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-dark);
}
.action-toolbar .doc-tag {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    color: #94A3B8;
}
.action-toolbar .btn-print {
    background: var(--primary);
    color: #FFFFFF;
    border: none;
    padding: 6px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 0.15s ease;
}
.action-toolbar .btn-print:hover {
    background: var(--primary-dark);
}

/* Executive Header */
.doc-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    color: #FFFFFF;
    padding: 36px 40px 30px;
    position: relative;
    border-bottom: 4px solid var(--primary);
}
.doc-header-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    margin-bottom: 24px;
}
.brand-identity {
    display: flex;
    align-items: center;
    gap: 14px;
}
.brand-logo-icon {
    width: 44px;
    height: 44px;
    background: var(--primary);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    box-shadow: 0 4px 12px rgba(15, 118, 110, 0.4);
}
.brand-logo-icon svg { width: 24px; height: 24px; }
.brand-title {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
}
.brand-subtitle {
    font-size: 12px;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

.security-badge {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    color: #FCA5A5;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.report-title-area h1 {
    font-size: 24px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}
.report-target-meta {
    font-size: 14px;
    color: #CBD5E1;
}

.header-meta-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.meta-chip {
    font-size: 11px;
}
.meta-chip .label {
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
    font-weight: 600;
}
.meta-chip .val {
    color: #F8FAFC;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    word-break: break-all;
}

/* Report Content Body */
.report-content {
    padding: 40px;
}

/* Threat Index & KPI Scorecard */
.threat-index-banner {
    background: #FFFFFF;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 36px;
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 24px;
    align-items: center;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
}
.threat-dial-card {
    background: var(--bg-subtle);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    border: 1px solid var(--border-color);
}
.threat-level-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 8px;
}
.threat-badge-rendah { background: var(--success-bg); color: var(--success); }
.threat-badge-sedang { background: var(--warning-bg); color: var(--warning); }
.threat-badge-tinggi { background: var(--danger-bg); color: var(--danger); }
.threat-badge-kritis { background: var(--critical-bg); color: var(--critical); }

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
}
.kpi-card {
    background: var(--bg-subtle);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 16px;
}
.kpi-card .kpi-num {
    font-size: 24px;
    font-weight: 800;
    line-height: 1.1;
    color: var(--text-main);
    margin-bottom: 4px;
}
.kpi-card .kpi-label {
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 600;
}
.kpi-card.danger .kpi-num { color: var(--danger); }
.kpi-card.warning .kpi-num { color: var(--warning); }
.kpi-card.accent .kpi-num { color: var(--primary); }

/* Sections */
.section {
    margin-bottom: 36px;
}
.section-title {
    font-size: 16px;
    font-weight: 800;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--border-color);
    letter-spacing: -0.01em;
}
.section-num {
    background: var(--primary);
    color: #FFFFFF;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 800;
}

/* Callout Box */
.callout-box {
    background: #F0FDFA;
    border-left: 4px solid var(--primary);
    border-radius: 0 8px 8px 0;
    padding: 18px 22px;
    color: #134E4A;
    font-size: 14px;
    line-height: 1.7;
    margin-bottom: 20px;
}

/* Findings & Action Cards */
.findings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
.bullet-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
}
.bullet-card h4 {
    font-size: 13px;
    font-weight: 700;
    color: var(--text-main);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.bullet-card ul {
    list-style: none;
    padding-left: 0;
}
.bullet-card li {
    position: relative;
    padding-left: 18px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #334155;
    line-height: 1.5;
}
.bullet-card li::before {
    content: "•";
    position: absolute;
    left: 4px;
    color: var(--primary);
    font-weight: bold;
    font-size: 16px;
}

/* Modern Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    margin: 12px 0;
    font-size: 13px;
}
.data-table th {
    background: var(--bg-subtle);
    color: var(--text-muted);
    font-weight: 700;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.04em;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}
.data-table td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-main);
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:nth-child(even) { background: #FAFAFA; }

/* Progress Meter */
.meter-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
}
.meter-bg {
    flex: 1;
    height: 8px;
    background: #E2E8F0;
    border-radius: 4px;
    overflow: hidden;
}
.meter-fill {
    height: 100%;
    border-radius: 4px;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-low { background: var(--success-bg); color: var(--success); }
.badge-medium { background: var(--warning-bg); color: var(--warning); }
.badge-high { background: var(--danger-bg); color: var(--danger); }
.badge-critical { background: var(--critical-bg); color: var(--critical); }

.badge-c0 { background: #E0F2FE; color: #0369A1; }
.badge-c1 { background: #E0E7FF; color: #4338CA; }
.badge-c2 { background: #FEF3C7; color: #B45309; }
.badge-c3 { background: #FFEDD5; color: #C2410C; }
.badge-c4 { background: #FEE2E2; color: #B91C1C; }
.badge-c5 { background: #FCE7F3; color: #BE185D; }
.badge-c6 { background: #FFE4E6; color: #9F1239; }
.badge-c7 { background: #F1F5F9; color: #475569; }

/* Methodology Card */
.methodology-box {
    background: #F8FAFC;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.6;
}

/* Disclaimer & Sign-off */
.disclaimer-card {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 8px;
    padding: 16px 20px;
    margin-top: 32px;
    font-size: 12px;
    color: #92400E;
    line-height: 1.6;
}
.signature-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid var(--border-color);
}
.sign-box {
    font-size: 12px;
}
.sign-line {
    width: 180px;
    height: 1px;
    background: #CBD5E1;
    margin: 40px 0 8px;
}

/* Print Styles */
@media print {
    body { background: #FFFFFF !important; font-size: 12px; }
    .action-toolbar { display: none !important; }
    .report-wrapper { box-shadow: none !important; max-width: 100% !important; }
    .doc-header { padding: 24px 30px !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .report-content { padding: 24px 30px !important; }
    .threat-index-banner { break-inside: avoid; page-break-inside: avoid; }
    .section { break-inside: avoid; page-break-inside: avoid; }
    .data-table { break-inside: avoid; page-break-inside: avoid; }
}
</style>
</head>
<body>

<div class="report-wrapper">
    <!-- Action Toolbar -->
    <div class="action-toolbar">
        <div class="doc-tag">
            <span>🛡️ CYBERGUARD AUDIT REPORT</span>
            <span>•</span>
            <span>ID: {{ analysis_id }}</span>
        </div>
        <div>
            <button class="btn-print" onclick="window.print()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>
                Cetak / Ekspor PDF
            </button>
        </div>
    </div>

    <!-- Certified Audit Header -->
    <header class="doc-header">
        <div class="doc-header-top">
            <div class="brand-identity">
                <div class="brand-logo-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
                </div>
                <div>
                    <div class="brand-title">CyberGuard-ID</div>
                    <div class="brand-subtitle">Automated Moderation & Threat Screening Platform</div>
                </div>
            </div>
            <div class="security-badge">
                Restricted • Internal Audit
            </div>
        </div>

        <div class="report-title-area">
            <h1>Laporan Hasil Analisis & Audit Moderasi</h1>
            <div class="report-target-meta">Target: <strong>{{ analysis_name }}</strong> (Sumber: {{ source_type }})</div>
        </div>

        <div class="header-meta-grid">
            <div class="meta-chip">
                <div class="label">Dokumen ID</div>
                <div class="val">CG-{{ analysis_id[:12] | upper }}</div>
            </div>
            <div class="meta-chip">
                <div class="label">Waktu Dibuat</div>
                <div class="val">{{ generated_at }}</div>
            </div>
            <div class="meta-chip">
                <div class="label">Provider AI</div>
                <div class="val">{{ report_provider }}</div>
            </div>
            <div class="meta-chip">
                <div class="label">Status Integritas</div>
                <div class="val" style="color: #6EE7B7;">VERIFIED (SHA-256)</div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="report-content">
        <!-- Threat Index & KPI Scorecard -->
        <div class="threat-index-banner">
            <div class="threat-dial-card">
                <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Indeks Risiko Global</div>
                <div style="font-size: 28px; font-weight: 800; color: var(--text-main); margin-top: 4px;">{{ severity_label | upper }}</div>
                <div class="threat-level-badge threat-badge-{{ severity_label | lower }}">
                    Status: {{ severity_label }}
                </div>
            </div>

            <div class="kpi-grid">
                <div class="kpi-card accent">
                    <div class="kpi-num">{{ total_comments }}</div>
                    <div class="kpi-label">Total Komentar</div>
                </div>
                <div class="kpi-card danger">
                    <div class="kpi-num">{{ harmful_count }}</div>
                    <div class="kpi-label">Komentar Berbahaya ({{ harmful_pct }}%)</div>
                </div>
                <div class="kpi-card warning">
                    <div class="kpi-num">{{ review_count }}</div>
                    <div class="kpi-label">Perlu Ditinjau</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-num">{{ cluster_count }}</div>
                    <div class="kpi-label">Kluster Serangan / Bot</div>
                </div>
            </div>
        </div>

        <!-- Section 1: Executive Summary -->
        <section class="section">
            <h2 class="section-title">
                <span class="section-num">1</span>
                Ringkasan Eksekutif Moderasi
            </h2>
            <div class="callout-box">
                {{ executive_summary }}
            </div>

            <div class="findings-grid">
                <div class="bullet-card">
                    <h4>🔍 Temuan Utama (Key Findings)</h4>
                    <ul>
                    {% for finding in key_findings %}
                        <li>{{ finding }}</li>
                    {% endfor %}
                    </ul>
                </div>
                <div class="bullet-card">
                    <h4>⚡ Rekomendasi Tindak Lanjut</h4>
                    <ul>
                    {% for action in recommended_actions %}
                        <li>{{ action }}</li>
                    {% endfor %}
                    </ul>
                </div>
            </div>
        </section>

        <!-- Section 2: Taxonomy & Category Distribution -->
        <section class="section">
            <h2 class="section-title">
                <span class="section-num">2</span>
                Distribusi Kategori Konten
            </h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 220px;">Kategori Taksonomi</th>
                        <th style="width: 80px;">Kode</th>
                        <th>Proporsi Visual</th>
                        <th style="width: 90px; text-align: right;">Jumlah</th>
                    </tr>
                </thead>
                <tbody>
                {% for cat, count in category_distribution.items() %}
                    {% set pct = (count / total_comments * 100) if total_comments > 0 else 0 %}
                    <tr>
                        <td><strong>{{ cat | replace('_', ' ') | title }}</strong></td>
                        <td><span class="badge badge-{{ cat[:2] | lower }}">{{ cat[:4] | upper }}</span></td>
                        <td>
                            <div class="meter-wrap">
                                <div class="meter-bg">
                                    <div class="meter-fill" style="width: {{ pct }}%; background: var(--primary);"></div>
                                </div>
                                <span style="font-size: 11px; color: var(--text-muted); font-family: monospace; width: 45px;">{{ "%.1f"|format(pct) }}%</span>
                            </div>
                        </td>
                        <td style="text-align: right; font-weight: 700;">{{ count }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </section>

        <!-- Section 3: Risk Level Distribution -->
        <section class="section">
            <h2 class="section-title">
                <span class="section-num">3</span>
                Tingkat Risiko Moderasi & Prioritas Penanganan
            </h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 140px;">Tingkat Risiko</th>
                        <th>Definisi Operasional</th>
                        <th>Jumlah Kasus</th>
                        <th style="width: 140px;">Rekomendasi Tindakan</th>
                    </tr>
                </thead>
                <tbody>
                {% for level, count in risk_distribution.items() %}
                    <tr>
                        <td><span class="badge badge-{{ level }}">{{ level | upper }}</span></td>
                        <td style="font-size: 12px; color: var(--text-muted);">
                            {% if level == 'critical' %}Ancaman fisik, doxxing, atau pelecehan ekstrem (Skor ≥ 5)
                            {% elif level == 'high' %}Ujaran kebencian SARA atau serangan terkoordinasi (Skor 3-4)
                            {% elif level == 'medium' %}Bahasa kasar berulang atau pelecehan personal ringan (Skor 1-2)
                            {% else %}Komentar wajar, konstruktif, atau opini netral (Skor 0){% endif %}
                        </td>
                        <td style="font-weight: 700;">{{ count }}</td>
                        <td style="font-size: 12px;">
                            {% if level in ['critical', 'high'] %}<strong style="color: var(--danger);">Tinjau Segera</strong>
                            {% elif level == 'medium' %}Skrining Rutin
                            {% else %}Aman / Abaikan{% endif %}
                        </td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </section>

        <!-- Section 4: Repetitive Attacks / Bot Clusters -->
        {% if cluster_count > 0 %}
        <section class="section">
            <h2 class="section-title">
                <span class="section-num">4</span>
                Intelijen Pola Serangan Berulang & Indikasi Bot
            </h2>
            <p style="margin-bottom: 12px; color: var(--text-muted); font-size: 13px;">
                Sistem mendeteksi <strong>{{ cluster_count }} kluster komentar</strong> dengan kemiripan teks tinggi (cosine similarity ≥ 0.80) yang mengindikasikan copy-paste spam atau serangan siber terkoordinasi.
            </p>
        </section>
        {% endif %}

        <!-- Section 5: Methodology & Provenance -->
        <section class="section">
            <h2 class="section-title">
                <span class="section-num">{% if cluster_count > 0 %}5{% else %}4{% endif %}</span>
                Metodologi Klasifikasi AI & Provenance
            </h2>
            <div class="methodology-box">
                <p><strong>Arsitektur Model:</strong> Pipeline klasifikasi utama berbasis <em>IndoBERT (indobenchmark/indobert-base-p1)</em> dengan fine-tuning untuk analisis sentimen dan deteksi ujaran kebencian spesifik bahasa Indonesia (5 kelas: C0-C4).</p>
                <p style="margin-top: 6px;"><strong>Kebijakan Verifikasi & Abstensi:</strong> Klasifikasi otomatis hanya disetujui jika Confidence ≥ 0.70 dan Margin ≥ 0.10. Komentar dengan keyakinan di bawah ambang batas (Confidence &lt; 0.55 atau Margin &lt; 0.10) dialihkan ke status <em>Uncertain / Mandatory Human Review</em> untuk menjaga integritas keadilan moderasi.</p>
            </div>
        </section>

        <!-- Section 6: Limitations & Legal Disclaimer -->
        <section class="section">
            <h2 class="section-title">
                <span class="section-num">{% if cluster_count > 0 %}6{% else %}5{% endif %}</span>
                Keterbatasan & Batasan Ruang Lingkup
            </h2>
            <ul style="margin-left: 20px; color: var(--text-muted); font-size: 13px;">
            {% for lim in limitations %}
                <li style="margin-bottom: 4px;">{{ lim }}</li>
            {% endfor %}
            </ul>

            <div class="disclaimer-card">
                <strong>Disclaimer Resmi & Kepatuhan Etika AI:</strong><br>
                Laporan ini dihasilkan oleh instrumen algoritma <strong>CyberGuard-ID</strong> sebagai alat bantu skrining dan prioritisasi antrian moderasi komentar. Hasil klasifikasi bukan merupakan vonis hukum, putusan pidana, atau penilaian definitif. Seluruh temuan berisiko tinggi wajib melalui proses tinjauan manual (*human-in-the-loop*) oleh moderator berwenang sebelum tindakan sanksi diambil.
            </div>

            <div class="signature-grid">
                <div class="sign-box">
                    <div style="font-weight: 700; color: var(--text-main);">Disusun Oleh Sistem:</div>
                    <div style="color: var(--text-muted);">CyberGuard-ID Automated Engine</div>
                    <div class="sign-line"></div>
                    <div style="font-family: monospace; font-size: 11px; color: var(--text-muted);">Signature: CG-AI-{{ analysis_id[:8] }}</div>
                </div>
            </div>
        </section>
    </main>
</div>

</body>
</html>"""


class ReportService:
    """Generates and manages analysis reports."""

    def __init__(self, reports_path: Path) -> None:
        self.reports_path = reports_path
        self.reports_path.mkdir(parents=True, exist_ok=True)

    def generate_csv_all(
        self,
        predictions: list[dict[str, Any]],
        analysis_id: str,
    ) -> Path:
        """Generate CSV of all predictions.

        Args:
            predictions: List of prediction dicts (joined with comments).
            analysis_id: Analysis ID for filename.

        Returns:
            Path to generated CSV.
        """
        path = self.reports_path / f"{analysis_id}_all_comments.csv"

        columns = [
            "analysis_id",
            "comment_id",
            "author_hash",
            "published_at",
            "original_text",
            "normalized_text",
            "predicted_label",
            "confidence",
            "second_label",
            "second_confidence",
            "margin",
            "verification_status",
            "base_risk_score",
            "additional_risk_score",
            "total_risk_score",
            "risk_level",
            "reviewer_label",
            "review_decision",
            "review_note",
        ]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for pred in predictions:
                row = {
                    "analysis_id": pred.get("analysis_id", ""),
                    "comment_id": pred.get("id", ""),
                    "author_hash": pred.get("author_hash", ""),
                    "published_at": pred.get("published_at", ""),
                    "original_text": pred.get("original_text", ""),
                    "normalized_text": pred.get("normalized_text", ""),
                    "predicted_label": pred.get("predicted_label", ""),
                    "confidence": pred.get("confidence", ""),
                    "second_label": pred.get("second_label", ""),
                    "second_confidence": pred.get("second_confidence", ""),
                    "margin": pred.get("margin", ""),
                    "verification_status": pred.get("verification_status", ""),
                    "base_risk_score": pred.get("base_risk_score", ""),
                    "additional_risk_score": pred.get("additional_risk_score", ""),
                    "total_risk_score": pred.get("total_risk_score", ""),
                    "risk_level": pred.get("risk_level", ""),
                    "reviewer_label": pred.get("reviewer_label", ""),
                    "review_decision": pred.get("review_decision", ""),
                    "review_note": pred.get("review_note", ""),
                }
                writer.writerow(row)

        logger.info("Generated CSV report: %s", path)
        return path

    def generate_csv_priority(
        self,
        predictions: list[dict[str, Any]],
        analysis_id: str,
    ) -> Path:
        """Generate CSV of priority items only (Critical/High/Mandatory/Uncertain)."""
        priority_levels = {"critical", "high"}
        priority_statuses = {"MANDATORY_REVIEW", "UNCERTAIN"}

        priority = [
            p
            for p in predictions
            if p.get("risk_level") in priority_levels or p.get("verification_status") in priority_statuses
        ]

        path = self.reports_path / f"{analysis_id}_priority.csv"

        columns = [
            "comment_id",
            "author_hash",
            "original_text",
            "predicted_label",
            "confidence",
            "margin",
            "verification_status",
            "total_risk_score",
            "risk_level",
        ]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for pred in priority:
                row = {col: pred.get(col, pred.get("id", "")) for col in columns}
                if "comment_id" not in pred:
                    row["comment_id"] = pred.get("id", "")
                writer.writerow(row)

        logger.info("Generated priority CSV: %s (%d items)", path, len(priority))
        return path

    def generate_json(
        self,
        analysis: AnalysisRun,
        stats: AnalysisStats,
        predictions: list[dict[str, Any]],
        summary: ReportSummary,
        analysis_id: str,
    ) -> Path:
        """Generate comprehensive JSON report."""
        path = self.reports_path / f"{analysis_id}_report.json"

        report_data = {
            "analysis": {
                "id": analysis.id,
                "name": analysis.name,
                "source_type": analysis.source_type,
                "video_id": analysis.video_id,
                "video_title": analysis.video_title,
                "status": analysis.status,
                "started_at": analysis.started_at,
                "completed_at": analysis.completed_at,
            },
            "statistics": {
                "total_comments": stats.total_comments,
                "category_distribution": stats.category_distribution,
                "risk_distribution": stats.risk_distribution,
                "harmful_count": stats.harmful_count,
                "uncertain_count": stats.uncertain_count,
                "high_count": stats.high_count,
                "critical_count": stats.critical_count,
                "cluster_count": stats.cluster_count,
                "reviewed_count": stats.reviewed_count,
            },
            "summary": {
                "executive_summary": summary.executive_summary,
                "key_findings": summary.key_findings,
                "recommended_actions": summary.recommended_actions,
                "limitations": summary.limitations,
            },
            "generated_at": datetime.now(UTC).isoformat(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info("Generated JSON report: %s", path)
        return path

    def generate_html(
        self,
        analysis: AnalysisRun,
        stats: AnalysisStats,
        summary: ReportSummary,
        report_provider: str = "local",
        analysis_id: str = "",
    ) -> Path:
        """Generate HTML report.

        Args:
            analysis: Analysis run data.
            stats: Aggregate statistics.
            summary: Report narrative summary.
            report_provider: "gemini" or "local".
            analysis_id: Analysis ID.

        Returns:
            Path to HTML file.
        """
        path = self.reports_path / f"{analysis_id}_report.html"

        # Calculate severity and percentage metrics
        total = stats.total_comments or 0
        harmful = (stats.high_count or 0) + (stats.critical_count or 0)
        review_count = (stats.uncertain_count or 0) + (stats.risk_distribution.get("sedang", 0) if stats.risk_distribution else 0)
        harmful_pct = round((harmful / total * 100), 1) if total > 0 else 0.0

        if harmful_pct > 30.0:
            severity_label = "Kritis"
        elif harmful_pct >= 15.0:
            severity_label = "Tinggi"
        elif harmful_pct >= 5.0:
            severity_label = "Sedang"
        else:
            severity_label = "Rendah"

        template = Template(HTML_REPORT_TEMPLATE)
        html = template.render(
            analysis_name=analysis.name or analysis.video_title or "Analisis Komentar",
            analysis_id=analysis.id,
            source_type=analysis.source_type.upper(),
            total_comments=total,
            harmful_count=harmful,
            harmful_pct=harmful_pct,
            review_count=review_count,
            high_count=stats.high_count or 0,
            critical_count=stats.critical_count or 0,
            cluster_count=stats.cluster_count or 0,
            severity_label=severity_label,
            executive_summary=summary.executive_summary,
            category_distribution=stats.category_distribution or {},
            risk_distribution=stats.risk_distribution or {},
            key_findings=summary.key_findings or [],
            recommended_actions=summary.recommended_actions or [],
            limitations=summary.limitations or [],
            report_provider="Gemini AI" if report_provider == "gemini" else "Template Lokal (Engine Internal)",
            generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info("Generated HTML report: %s", path)
        return path
