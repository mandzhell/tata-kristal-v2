# ── CARA DEPLOY KE STREAMLIT CLOUD ────────────────────────────────────────
#
# PRASYARAT: Sudah punya Google Sheets + Service Account
# (lihat panduan lengkap di bawah)
#
# 1. Upload semua file ke GitHub (repository baru atau yang sudah ada)
#    Struktur folder:
#    tata_kristal/
#    ├── app.py
#    ├── requirements.txt
#    ├── .streamlit/
#    │   └── config.toml        ← BOLEH di-commit (tidak ada rahasia di sini)
#    ├── pages/
#    │   ├── __init__.py
#    │   ├── db.py
#    │   ├── beranda.py
#    │   ├── kasir.py
#    │   ├── stok.py
#    │   ├── pengeluaran.py
#    │   ├── laporan.py
#    │   └── prediksi.py
#    └── (JANGAN upload folder data/ — sudah tidak dipakai)
#
# 2. Buka https://share.streamlit.io → "New app"
#    - Repository: pilih repo GitHub kamu
#    - Branch: main
#    - Main file path: tata_kristal/app.py  (sesuaikan)
#
# 3. Di Streamlit Cloud → Settings → Secrets, tambahkan:
#
#    SPREADSHEET_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz"   ← ID Google Sheet kamu
#
#    [gcp_service_account]
#    type = "service_account"
#    project_id = "nama-project-kamu"
#    private_key_id = "xxxx"
#    private_key = "-----BEGIN RSA PRIVATE KEY-----\nxxxx\n-----END RSA PRIVATE KEY-----\n"
#    client_email = "tata-kristal@nama-project.iam.gserviceaccount.com"
#    client_id = "xxxx"
#    auth_uri = "https://accounts.google.com/o/oauth2/auth"
#    token_uri = "https://oauth2.googleapis.com/token"
#    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
#    client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
#
# 4. Klik Deploy!
#
# ── CARA SETUP GOOGLE SHEETS + SERVICE ACCOUNT ────────────────────────────
#
# LANGKAH A — Buat Google Spreadsheet:
#   1. Buka https://sheets.google.com → buat spreadsheet baru
#   2. Beri nama: "TATA Kristal - Data"
#   3. Salin ID dari URL-nya:
#      https://docs.google.com/spreadsheets/d/[INI_ID_NYA]/edit
#
# LANGKAH B — Buat Service Account di Google Cloud:
#   1. Buka https://console.cloud.google.com
#   2. Buat project baru (atau pakai yang sudah ada)
#   3. Aktifkan 2 API ini:
#      - Google Sheets API
#      - Google Drive API
#   4. IAM & Admin → Service Accounts → Create Service Account
#      Nama: tata-kristal
#   5. Setelah dibuat, klik service account → Keys → Add Key → JSON
#      File JSON akan ter-download otomatis — SIMPAN BAIK-BAIK
#
# LANGKAH C — Share spreadsheet ke service account:
#   1. Buka file JSON yang tadi di-download
#   2. Salin nilai "client_email" (contoh: tata-kristal@project.iam.gserviceaccount.com)
#   3. Buka Google Spreadsheet → Share → paste email tadi → Editor → Send
#
# LANGKAH D — Isi Streamlit Secrets:
#   Salin semua isi dari file JSON ke bagian [gcp_service_account] di Secrets
#   (pastikan format TOML, bukan JSON)
#
# ── UNTUK JALANKAN LOKAL ──────────────────────────────────────────────────
#
# pip install -r requirements.txt
# streamlit run app.py
#
# Buat file .streamlit/secrets.toml:
#
# SPREADSHEET_ID = "1AbCdEfGhIjKlMnOpQrStUvWxYz"
#
# [gcp_service_account]
# type = "service_account"
# project_id = "..."
# private_key = "..."
# client_email = "..."
# ... (isi dari file JSON yang di-download)
#
# ── CATATAN DATA ──────────────────────────────────────────────────────────
#
# Data sekarang disimpan di Google Sheets — TIDAK akan hilang saat redeploy.
# Kamu bisa pantau semua transaksi real-time dari Google Sheets kapan saja.
# Link spreadsheet bisa dibookmark di HP untuk monitoring cepat.
