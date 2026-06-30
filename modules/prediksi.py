import streamlit as st
import json
import os
from datetime import date, datetime
from modules.db import load_sales, load_pengeluaran, load_stok, fmt_rupiah
from collections import Counter

UMKM_NAME = "TATA Kristal"
CREATOR_NAME = "Armanda Putra Rilda Lubis"
STOK_PER_PLASTIK_CAPACITY = 50  # kg kapasitas 1 plastik
STOK_PER_PLASTIK_ISI = 40  # kg isi normal 1 plastik

HARI_OPTIONS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
CUACA_OPTIONS = {
    "panas": "☀️ Panas / Terik",
    "sedang": "🌤️ Cerah Biasa",
    "mendung": "☁️ Mendung",
    "hujan": "🌧️ Hujan",
}
HARI_IDX = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def _hari_ini():
    idx = datetime.today().weekday()  # 0=Senin
    return HARI_IDX[idx]


def _predict_sales(hari, cuaca, sales):
    """Prediksi berbasis rule: analisis data historis"""
    if not sales:
        return {
            "prediksi_pemasukan": 50000,
            "prediksi_transaksi": 10,
            "prediksi_stok_plastik": 1.0,
            "prediksi_stok_es_kg": 40,
            "tingkat_permintaan": "sedang",
            "alasan": "Tidak ada data historis. Menggunakan asumsi dasar.",
            "tips_operasional": "Mulai catat setiap transaksi untuk analisis yang lebih akurat.",
            "peringatan": "Data belum cukup untuk prediksi yang akurat."
        }
    
    # Kelompokkan sales berdasarkan hari
    sales_by_hari = {}
    for s in sales:
        try:
            # Parse tanggal dalam format YYYY-MM-DD
            tanggal_str = s.get("tanggal", "")
            from datetime import datetime as dt
            d = dt.strptime(tanggal_str, "%Y-%m-%d")
            hari_nama = HARI_IDX[d.weekday()]
            
            if hari_nama not in sales_by_hari:
                sales_by_hari[hari_nama] = []
            sales_by_hari[hari_nama].append(s)
        except:
            pass
    
    # Hitung rata-rata untuk hari yang dipilih
    hari_sales = sales_by_hari.get(hari, [])
    if hari_sales:
        avg_penjualan = sum(s.get("nominal", 0) for s in hari_sales) // len(hari_sales)
        avg_transaksi = len(hari_sales) // len([d for d in set(s.get("tanggal", "") for s in hari_sales) if d])
    else:
        # Jika tidak ada data untuk hari ini, pakai rata-rata keseluruhan
        avg_penjualan = sum(s.get("nominal", 0) for s in sales) // len(sales)
        avg_transaksi = max(5, len(sales) // 30)  # asumsi ~30 hari data
    
    # Faktor cuaca
    cuaca_multiplier = {
        "panas": 1.3,      # ☀️ panas = es laku lebih
        "sedang": 1.0,     # 🌤️ normal
        "mendung": 0.85,   # ☁️ sedikit kurang
        "hujan": 0.6       # 🌧️ jauh berkurang
    }
    
    multiplier = cuaca_multiplier.get(cuaca, 1.0)
    
    # Hitung prediksi
    prediksi_penjualan = int(avg_penjualan * multiplier)
    prediksi_transaksi = int(avg_transaksi * multiplier)
    
    # Tentukan tingkat permintaan
    if multiplier >= 1.2:
        tingkat = "sangat_tinggi"
    elif multiplier >= 1.0:
        tingkat = "tinggi"
    elif multiplier >= 0.85:
        tingkat = "sedang"
    else:
        tingkat = "rendah"
    
    # Alasan & tips
    cuaca_text = {
        "panas": "cuaca panas = lebih banyak orang membeli es",
        "sedang": "cuaca normal",
        "mendung": "cuaca mendung sedikit mengurangi permintaan",
        "hujan": "cuaca hujan biasanya mengurangi kedatangan pembeli"
    }
    
    tips_text = {
        "panas": "Siapkan es extra karena cuaca panas. Jangan sampai kehabisan stok.",
        "sedang": "Persiapan normal. Pantau stok sepanjang hari.",
        "mendung": "Stok bisa lebih hemat. Fokus pada kualitas layanan.",
        "hujan": "Siapkan stok minimal. Manfaatkan waktu untuk maintenance/promosi."
    }
    
    # Hitung kebutuhan stok
    # Asumsi: rata-rata 5kg per transaksi (bisa disesuaikan)
    es_dibutuhkan = max(40, prediksi_transaksi * 5)
    
    # Plastik yang dibutuhkan (1 plastik bisa isi 40kg, capacity 50kg)
    # Tapi untuk prediksi, kita hitung berdasarkan isi 40kg
    plastik_dibutuhkan = es_dibutuhkan / STOK_PER_PLASTIK_ISI
    
    # Round ke 0.5 terdekat (bisa 1, 1.5, 2, 2.5, dll)
    plastik_dibutuhkan = round(plastik_dibutuhkan * 2) / 2
    
    return {
        "prediksi_pemasukan": prediksi_penjualan,
        "prediksi_transaksi": prediksi_transaksi,
        "prediksi_stok_plastik": plastik_dibutuhkan,
        "prediksi_stok_es_kg": int(es_dibutuhkan),
        "tingkat_permintaan": tingkat,
        "alasan": f"Berdasarkan rata-rata {hari} + {cuaca_text[cuaca]}.",
        "tips_operasional": tips_text[cuaca],
        "peringatan": ""
    }


def _get_api_key():
    # Tidak perlu API key, prediksi berbasis rule
    return "local"


def _run_ai(prompt, hari, cuaca, sales, stok):
    """Prediksi berbasis rule, tanpa AI"""
    result = _predict_sales(hari, cuaca, sales)
    
    return result, None


PERMINTAAN_COLOR = {
    "rendah": "#6b7280",
    "sedang": "#0284c7",
    "tinggi": "#16a34a",
    "sangat_tinggi": "#dc2626",
}
PERMINTAAN_LABEL = {
    "rendah": "🔵 Rendah",
    "sedang": "🟡 Sedang",
    "tinggi": "🟢 Tinggi",
    "sangat_tinggi": "🔴 Sangat Tinggi",
}


def show():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Prediksi AI</h1>
        <p>Analisis cerdas untuk perencanaan stok harian</p>
    </div>
    """, unsafe_allow_html=True)

    sales = load_sales()
    peng = load_pengeluaran()
    stok = load_stok()

    st.markdown("#### ⚙️ Parameter Prediksi")

    c1, c2 = st.columns(2)
    with c1:
        default_hari = _hari_ini()
        hari_idx = HARI_OPTIONS.index(default_hari) if default_hari in HARI_OPTIONS else 0
        hari = st.selectbox("Hari", HARI_OPTIONS, index=hari_idx)
    with c2:
        cuaca_key = st.selectbox("Cuaca", list(CUACA_OPTIONS.keys()),
                                  format_func=lambda k: CUACA_OPTIONS[k])

    catatan = st.text_area(
        "Catatan tambahan (opsional)",
        placeholder="contoh: ada hajatan besar di dekat lokasi, hari libur nasional, dll...",
        height=80
    )

    st.divider()

    if not sales:
        st.warning("⚠️ Belum ada data penjualan. Prediksi akan menggunakan asumsi dasar. Semakin banyak data, semakin akurat prediksinya.")

    run_btn = st.button("🚀 Jalankan Prediksi AI", use_container_width=True, type="primary")

    if run_btn:
        prompt = ""  # Tidak dipakai untuk rule-based prediction
        with st.spinner("🔍 Menganalisis data penjualan..."):
            result, error = _run_ai(prompt, hari, cuaca_key, sales, stok)

        if error:
            st.error(f"❌ {error}")
        elif result:
            st.divider()
            st.markdown("### 📊 Hasil Prediksi")

            perm = result.get("tingkat_permintaan", "sedang")
            perm_label = PERMINTAAN_LABEL.get(perm, perm)
            perm_color = PERMINTAAN_COLOR.get(perm, "#0284c7")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Prediksi Pemasukan", fmt_rupiah(result["prediksi_pemasukan"]))
            col2.metric("🧾 Prediksi Transaksi", f"~{result['prediksi_transaksi']}")
            col3.metric("📦 Plastik Disiapkan", f"{result['prediksi_stok_plastik']} plastik")
            col4.metric("🧊 Es Disiapkan", f"{result['prediksi_stok_es_kg']:,} kg")

            st.markdown(f"""
            <div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:1rem 1.2rem;margin:1rem 0'>
                <div style='font-size:0.8rem;color:#0369a1;font-weight:600;margin-bottom:4px'>TINGKAT PERMINTAAN PERKIRAAN</div>
                <div style='font-size:1.4rem;color:{perm_color};font-weight:700'>{perm_label}</div>
            </div>
            """, unsafe_allow_html=True)

            stok_penuh = sum(1 for x in stok["penuh"] if x)
            es_tersedia = stok_penuh * STOK_PER_PLASTIK_ISI
            es_dibutuhkan = result["prediksi_stok_es_kg"]
            selisih = es_tersedia - es_dibutuhkan

            st.markdown("#### 📦 Status Stok vs Kebutuhan")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Stok Es Saat Ini", f"{es_tersedia} kg", delta=None)
            col_b.metric("Es yang Dibutuhkan", f"{es_dibutuhkan} kg", delta=None)
            if selisih >= 0:
                col_c.metric("Kelebihan / Kekurangan", f"+{selisih} kg", delta="Cukup ✅")
            else:
                col_c.metric("Kelebihan / Kekurangan", f"{selisih} kg", delta=f"Kurang {abs(selisih)} kg ⚠️", delta_color="inverse")

            pct_siap = min(1.0, es_tersedia / max(es_dibutuhkan, 1))
            st.progress(pct_siap, text=f"Kesiapan stok: {es_tersedia}/{es_dibutuhkan} kg ({pct_siap*100:.0f}%)")

            st.divider()
            st.markdown("#### 💡 Analisis & Tips")

            alasan = result.get("alasan", "")
            tips = result.get("tips_operasional", "")
            peringatan = result.get("peringatan", "")

            if alasan:
                st.info(f"**Analisis:** {alasan}")
            if tips:
                st.success(f"**Tips Hari Ini:** {tips}")
            if peringatan:
                st.warning(f"**⚠️ Perhatian:** {peringatan}")

            st.caption(f"Prediksi dibuat pada {datetime.now().strftime('%d/%m/%Y %H:%M')} berdasarkan {len(sales)} data transaksi tersimpan.")
