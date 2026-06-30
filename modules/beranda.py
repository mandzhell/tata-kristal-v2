import streamlit as st
from datetime import date
from modules.db import (
    sales_today, pengeluaran_today, load_stok,
    bon_today, total_piutang, bon_belum_lunas,
    fmt_rupiah, KATEGORI_LABEL
)


def show():
    st.markdown("""
    <div class="main-header">
        <h1>TATA Kristal — Beranda</h1>
        <p>Ringkasan aktivitas hari ini</p>
    </div>
    """, unsafe_allow_html=True)

    today_sales = sales_today()
    today_peng = pengeluaran_today()
    today_bon = bon_today()
    stok = load_stok()

    pemasukan_kas = sum(s["nominal"] for s in today_sales)
    pengeluaran = sum(p["nominal"] for p in today_peng)
    bon_belum_lunas_today = sum(b["nominal"] for b in today_bon if b["status"] == "belum_lunas")
    laba = pemasukan_kas - pengeluaran
    stok_penuh = sum(1 for x in stok["penuh"] if x)
    piutang_total = total_piutang()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pemasukan Kas Hari Ini", fmt_rupiah(pemasukan_kas))
    col2.metric("Pengeluaran Hari Ini", fmt_rupiah(pengeluaran))
    col3.metric("Laba Bersih (Kas)", fmt_rupiah(laba), delta=fmt_rupiah(laba) if laba != 0 else None)
    col4.metric("Stok Plastik Terisi", f"{stok_penuh} / {stok['jumlah']}")

    if piutang_total > 0:
        st.warning(
            f"Total piutang (bon belum lunas): **{fmt_rupiah(piutang_total)}** "
            f"dari {len(bon_belum_lunas())} bon. Bon baru hari ini: {fmt_rupiah(bon_belum_lunas_today)} "
            f"(belum masuk pemasukan kas sampai dilunasi)."
        )

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Penjualan Terkini")
        if not today_sales:
            st.info("Belum ada penjualan hari ini.")
        else:
            for s in reversed(today_sales[-8:]):
                ket = s.get("keterangan") or "Penjualan es"
                st.markdown(f"""
                <div class="sale-card">
                    <span>{s['waktu']} — {ket}</span>
                    <strong style="color:#16a34a">{fmt_rupiah(s['nominal'])}</strong>
                </div>
                """, unsafe_allow_html=True)
            if len(today_sales) > 8:
                st.caption(f"+{len(today_sales)-8} transaksi lainnya hari ini")

    with col_b:
        st.markdown("#### Pengeluaran Hari Ini")
        if not today_peng:
            st.info("Tidak ada pengeluaran hari ini.")
        else:
            for p in today_peng:
                kat = KATEGORI_LABEL.get(p["kategori"], p["kategori"])
                ket = p.get("keterangan") or ""
                st.markdown(f"""
                <div class="peng-card">
                    <div style="display:flex;justify-content:space-between">
                        <span>{kat} {f'— {ket}' if ket else ''}</span>
                        <strong style="color:#ea580c">{fmt_rupiah(p['nominal'])}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Status Stok Plastik")
    pct = stok_penuh / stok["jumlah"] if stok["jumlah"] > 0 else 0
    st.progress(pct, text=f"{stok_penuh} plastik terisi dari {stok['jumlah']}")
