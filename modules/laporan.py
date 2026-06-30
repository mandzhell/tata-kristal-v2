import streamlit as st
import pandas as pd
from modules.db import load_sales, load_pengeluaran, fmt_rupiah, all_dates, KATEGORI_LABEL


def show():
    st.markdown("""
    <div class="main-header">
        <h1>📊 Laporan</h1>
        <p>Ringkasan keuangan usaha TATA Kristal</p>
    </div>
    """, unsafe_allow_html=True)

    sales = load_sales()
    peng = load_pengeluaran()

    if not sales and not peng:
        st.info("Belum ada data untuk ditampilkan. Mulai catat penjualan dan pengeluaran terlebih dahulu.")
        return

    total_pemasukan = sum(s["nominal"] for s in sales)
    total_pengeluaran = sum(p["nominal"] for p in peng)
    total_laba = total_pemasukan - total_pengeluaran
    total_transaksi = len(sales)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Pemasukan", fmt_rupiah(total_pemasukan))
    col2.metric("💸 Total Pengeluaran", fmt_rupiah(total_pengeluaran))
    col3.metric("📈 Total Laba Bersih", fmt_rupiah(total_laba))
    col4.metric("🧾 Total Transaksi", total_transaksi)

    st.divider()

    # ── RINGKASAN STATISTIK ──────────────────────────────────────────────
    st.markdown("#### 📈 Statistik Penjualan")
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    if total_transaksi > 0:
        avg_transaksi = total_pemasukan / total_transaksi
        profit_margin = (total_laba / total_pemasukan * 100) if total_pemasukan > 0 else 0
        col_stat1.metric("💵 Rata-rata per Transaksi", fmt_rupiah(int(avg_transaksi)))
        col_stat2.metric("📊 Profit Margin", f"{profit_margin:.1f}%")
    
    if total_pengeluaran > 0:
        expense_ratio = (total_pengeluaran / total_pemasukan * 100) if total_pemasukan > 0 else 0
        col_stat3.metric("💰 Rasio Pengeluaran", f"{expense_ratio:.1f}%")

    st.divider()

    # ── Bangun dataframe per hari ────────────────────────────────────────
    dates = all_dates()
    if not dates:
        st.info("Belum ada data.")
        return

    rows = []
    for d in dates:
        pemasukan_d  = sum(s["nominal"] for s in sales if s["tanggal"] == d)
        pengeluaran_d = sum(p["nominal"] for p in peng  if p["tanggal"] == d)
        laba_d       = pemasukan_d - pengeluaran_d
        transaksi_d  = sum(1 for s in sales if s["tanggal"] == d)
        rows.append({
            "Tanggal": d,
            "pemasukan_raw": pemasukan_d,
            "pengeluaran_raw": pengeluaran_d,
            "laba_raw": laba_d,
            "Transaksi": transaksi_d,
        })

    df = pd.DataFrame(rows).sort_values("Tanggal")

    # ── CHART PEMASUKAN vs PENGELUARAN vs LABA ───────────────────────────
    if len(df) >= 1:
        st.markdown("#### 📈 Grafik Keuangan Harian")

        tab1, tab2, tab3 = st.tabs(["💰 Pemasukan & Pengeluaran", "📈 Laba Bersih", "🧾 Jumlah Transaksi"])

        with tab1:
            chart_df = df[["Tanggal", "pemasukan_raw", "pengeluaran_raw"]].rename(columns={
                "pemasukan_raw": "Pemasukan",
                "pengeluaran_raw": "Pengeluaran"
            }).set_index("Tanggal")
            st.bar_chart(chart_df, color=["#0ea5e9", "#f97316"], use_container_width=True)

        with tab2:
            laba_df = df[["Tanggal", "laba_raw"]].rename(columns={"laba_raw": "Laba Bersih"}).set_index("Tanggal")
            st.bar_chart(laba_df, color=["#16a34a"], use_container_width=True)

        with tab3:
            trx_df = df[["Tanggal", "Transaksi"]].set_index("Tanggal")
            st.bar_chart(trx_df, color=["#8b5cf6"], use_container_width=True)

    # ── VISUALISASI TAMBAHAN ─────────────────────────────────────────────
    if len(df) >= 3:
        st.markdown("#### 📉 Trend Keuangan (Line Chart)")
        trend_df = df[["Tanggal", "pemasukan_raw", "pengeluaran_raw"]].rename(columns={
            "pemasukan_raw": "Pemasukan",
            "pengeluaran_raw": "Pengeluaran"
        }).set_index("Tanggal")
        st.line_chart(trend_df, color=["#0ea5e9", "#f97316"], use_container_width=True)

    # ── TOP & BOTTOM DAYS ────────────────────────────────────────────────
    st.markdown("#### 🏆 Performa Harian")
    col_top, col_bottom = st.columns(2)
    
    with col_top:
        st.markdown("**Top 5 Hari Terbaik**")
        top_days = df.nlargest(5, "pemasukan_raw")[["Tanggal", "pemasukan_raw"]].copy()
        top_days["Pemasukan"] = top_days["pemasukan_raw"].apply(fmt_rupiah)
        st.dataframe(top_days[["Tanggal", "Pemasukan"]], use_container_width=True, hide_index=True)
    
    with col_bottom:
        st.markdown("**Top 5 Hari Terberat (Pengeluaran)**")
        top_expense = df.nlargest(5, "pengeluaran_raw")[["Tanggal", "pengeluaran_raw"]].copy()
        top_expense["Pengeluaran"] = top_expense["pengeluaran_raw"].apply(fmt_rupiah)
        st.dataframe(top_expense[["Tanggal", "Pengeluaran"]], use_container_width=True, hide_index=True)

    st.divider()

    # ── TABEL RINGKASAN ──────────────────────────────────────────────────
    st.markdown("#### 📅 Ringkasan Per Hari")
    df_display = df.copy().sort_values("Tanggal", ascending=False)
    df_display["Pemasukan"]   = df_display["pemasukan_raw"].apply(fmt_rupiah)
    df_display["Pengeluaran"] = df_display["pengeluaran_raw"].apply(fmt_rupiah)
    df_display["Laba Bersih"] = df_display["laba_raw"].apply(fmt_rupiah)
    st.dataframe(
        df_display[["Tanggal", "Pemasukan", "Pengeluaran", "Laba Bersih", "Transaksi"]],
        use_container_width=True, hide_index=True
    )

    st.divider()

    # ── CHART PENGELUARAN PER KATEGORI ──────────────────────────────────
    st.markdown("#### 🗂️ Pengeluaran Per Kategori")
    if peng:
        kat_totals = {}
        for p in peng:
            k = p["kategori"]
            kat_totals[k] = kat_totals.get(k, 0) + p["nominal"]

        kat_df = pd.DataFrame([
            {"Kategori": KATEGORI_LABEL.get(k, k), "Total (Rp)": v}
            for k, v in kat_totals.items()
        ]).sort_values("Total (Rp)", ascending=False)

        col_chart, col_tbl = st.columns([2, 1])
        with col_chart:
            st.bar_chart(kat_df.set_index("Kategori"), color=["#f97316"], use_container_width=True)
        with col_tbl:
            kat_df_disp = kat_df.copy()
            kat_df_disp["Total (Rp)"] = kat_df_disp["Total (Rp)"].apply(fmt_rupiah)
            st.dataframe(kat_df_disp, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data pengeluaran.")

    st.divider()

    # ── DETAIL TRANSAKSI ─────────────────────────────────────────────────
    with st.expander("🔍 Lihat semua transaksi penjualan"):
        if sales:
            sales_df = pd.DataFrame(sales)[["tanggal", "waktu", "nominal", "keterangan"]]
            sales_df.columns = ["Tanggal", "Waktu", "Nominal", "Keterangan"]
            sales_df["Nominal"] = sales_df["Nominal"].apply(fmt_rupiah)
            st.dataframe(sales_df.sort_values("Tanggal", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada transaksi.")
