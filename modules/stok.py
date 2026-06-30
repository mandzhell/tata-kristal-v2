import streamlit as st
from modules.db import load_stok, save_stok, fmt_rupiah, KG_PER_PLASTIK_ISI


def show():
    st.markdown("""
    <div class="main-header">
        <h1>Stok Plastik 50 kg</h1>
        <p>Kapasitas mesin: 1.000 kg es per 24 jam</p>
    </div>
    """, unsafe_allow_html=True)

    stok = load_stok()
    stok_penuh = sum(1 for x in stok["penuh"] if x)
    stok_kosong = stok["jumlah"] - stok_penuh
    kg_tersedia = stok_penuh * KG_PER_PLASTIK_ISI

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Plastik Terisi", stok_penuh)
    col2.metric("Plastik Kosong", stok_kosong)
    col3.metric("Estimasi Stok (kg)", f"{kg_tersedia:,}")
    col4.metric("Kapasitas Mesin/hari", "1.000 kg")

    st.success(
        f"Mode otomatis aktif: setiap ada penjualan atau bon, stok berkurang otomatis "
        f"sebesar {stok.get('kg_per_transaksi', 2.0)} kg per transaksi. "
        f"Progress pemakaian saat ini: {stok.get('kg_terpakai_running', 0):.1f}/{KG_PER_PLASTIK_ISI} kg "
        f"menuju plastik berikutnya kosong."
    )

    st.divider()

    # Pengaturan jumlah plastik & kg per transaksi
    with st.expander("Pengaturan stok otomatis", expanded=False):
        new_jumlah = st.number_input(
            "Jumlah plastik 50kg yang dimiliki", min_value=1, max_value=100,
            value=stok["jumlah"], step=1
        )
        new_kg_per_transaksi = st.number_input(
            "Estimasi kg es terpakai per transaksi (untuk auto-decrement)",
            min_value=0.1, max_value=50.0, value=float(stok.get("kg_per_transaksi", 2.0)), step=0.1
        )
        if st.button("Simpan Pengaturan"):
            stok["jumlah"] = new_jumlah
            stok["kg_per_transaksi"] = new_kg_per_transaksi
            while len(stok["penuh"]) < new_jumlah:
                stok["penuh"].append(False)
            stok["penuh"] = stok["penuh"][:new_jumlah]
            save_stok(stok)
            st.success("Tersimpan!")
            st.rerun()

    st.markdown("#### Status Setiap Plastik")
    st.caption("Klik checkbox untuk menandai plastik terisi / kosong secara manual (misal saat restok)")

    col_all1, col_all2, _ = st.columns([1, 1, 3])
    with col_all1:
        if st.button("Tandai Semua Penuh (restok)", use_container_width=True):
            stok["penuh"] = [True] * stok["jumlah"]
            stok["kg_terpakai_running"] = 0
            save_stok(stok)
            st.rerun()
    with col_all2:
        if st.button("Reset Semua Kosong", use_container_width=True):
            stok["penuh"] = [False] * stok["jumlah"]
            save_stok(stok)
            st.rerun()

    st.markdown("")

    # Grid plastik — 5 per baris
    per_row = 5
    changed = False
    for row_start in range(0, stok["jumlah"], per_row):
        cols = st.columns(per_row)
        for col_idx in range(per_row):
            idx = row_start + col_idx
            if idx >= stok["jumlah"]:
                break
            with cols[col_idx]:
                label = f"Plastik {idx + 1}"
                icon = "🟢" if stok["penuh"][idx] else "⬜"
                new_val = st.checkbox(
                    f"{icon} {label}",
                    value=stok["penuh"][idx],
                    key=f"plastik_{idx}"
                )
                if new_val != stok["penuh"][idx]:
                    stok["penuh"][idx] = new_val
                    changed = True

    if changed:
        save_stok(stok)
        st.rerun()

    st.divider()
    pct = stok_penuh / stok["jumlah"] if stok["jumlah"] > 0 else 0
    st.progress(pct, text=f"Kapasitas terisi: {stok_penuh}/{stok['jumlah']} plastik ({kg_tersedia} kg dari {stok['jumlah'] * KG_PER_PLASTIK_ISI} kg total)")
