import streamlit as st
from datetime import date
from pages.db import (
    load_pengeluaran, add_pengeluaran, delete_pengeluaran,
    pengeluaran_today, fmt_rupiah, KATEGORI_LABEL
)


def show():
    st.markdown("""
    <div class="main-header">
        <h1>💸 Pengeluaran Harian</h1>
        <p>Catat semua biaya operasional usaha</p>
    </div>
    """, unsafe_allow_html=True)

    today_peng = pengeluaran_today()
    total_today = sum(p["nominal"] for p in today_peng)

    # Ringkasan per kategori hari ini
    if today_peng:
        col1, col2, col3, col4 = st.columns(4)
        kat_totals = {}
        for p in today_peng:
            kat_totals[p["kategori"]] = kat_totals.get(p["kategori"], 0) + p["nominal"]
        col1.metric("⚡ Listrik", fmt_rupiah(kat_totals.get("listrik", 0)))
        col2.metric("🛍️ Plastik", fmt_rupiah(kat_totals.get("plastik", 0)))
        col3.metric("👤 Gaji", fmt_rupiah(kat_totals.get("gaji", 0)))
        col4.metric("📋 Lainnya", fmt_rupiah(kat_totals.get("lainnya", 0)))
        st.divider()

    # Form tambah pengeluaran
    st.markdown("#### ➕ Tambah Pengeluaran")
    with st.form("form_pengeluaran", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tgl = st.date_input("Tanggal", value=date.today())
            kategori = st.selectbox("Kategori", options=list(KATEGORI_LABEL.keys()),
                                     format_func=lambda k: KATEGORI_LABEL[k])
        with c2:
            nominal = st.number_input("Nominal (Rp)", min_value=0, step=1000, value=None,
                                       placeholder="contoh: 50000")
            ket = st.text_input("Keterangan", placeholder="contoh: tagihan PLN Juli")

        submitted = st.form_submit_button("💾 Simpan Pengeluaran", use_container_width=True)
        if submitted:
            if nominal and nominal > 0:
                add_pengeluaran(str(tgl), kategori, int(nominal), ket)
                st.success(f"✅ Tersimpan: {KATEGORI_LABEL[kategori]} — {fmt_rupiah(int(nominal))}")
                st.rerun()
            else:
                st.warning("Masukkan nominal yang valid")

    st.divider()

    # Riwayat lengkap
    all_peng = load_pengeluaran()
    total_all = sum(p["nominal"] for p in all_peng)

    st.markdown(f"#### 📋 Riwayat Pengeluaran &nbsp; — &nbsp; Total hari ini: **{fmt_rupiah(total_today)}**")

    if not all_peng:
        st.info("Belum ada pengeluaran yang dicatat.")
        return

    # Filter tanggal
    all_dates = sorted(set(p["tanggal"] for p in all_peng), reverse=True)
    filter_tgl = st.selectbox("Filter tanggal", ["Semua"] + all_dates, key="peng_filter")

    filtered = all_peng if filter_tgl == "Semua" else [p for p in all_peng if p["tanggal"] == filter_tgl]
    filtered = list(reversed(filtered))

    for p in filtered:
        kat = KATEGORI_LABEL.get(p["kategori"], p["kategori"])
        ket = p.get("keterangan") or "—"
        c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 1])
        c1.markdown(f"<span style='font-size:0.85rem;color:#6b7280'>{p['tanggal']}</span>", unsafe_allow_html=True)
        c2.markdown(f"**{kat}**")
        c3.markdown(f"<span style='color:#ea580c;font-weight:600'>{fmt_rupiah(p['nominal'])}</span>", unsafe_allow_html=True)
        c4.markdown(f"<span style='color:#6b7280;font-size:0.9rem'>{ket}</span>", unsafe_allow_html=True)
        with c5:
            if st.button("🗑️", key=f"del_peng_{p['id']}", help="Hapus"):
                delete_pengeluaran(p["id"])
                st.rerun()

    st.divider()
    st.markdown(f"**Total semua pengeluaran tercatat: {fmt_rupiah(total_all)}**")
