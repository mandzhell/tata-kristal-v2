import streamlit as st
from pages.db import add_sale, delete_sale, sales_today, fmt_rupiah

QUICK_NOMINALS = [3000, 4000, 5000, 6000, 10000, 15000, 20000]


def show():
    st.markdown("""
    <div class="main-header">
        <h1>🧾 Kasir / POS</h1>
        <p>Catat penjualan dengan cepat</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Nominal Cepat")
    st.caption("Klik tombol untuk langsung mencatat penjualan")

    # Keterangan global (dipakai oleh tombol cepat)
    keterangan = st.text_input("Keterangan (opsional)", placeholder="contoh: pelanggan warung pak budi", key="kasir_ket")

    # Tombol cepat — 7 kolom
    cols = st.columns(len(QUICK_NOMINALS))
    for i, nominal in enumerate(QUICK_NOMINALS):
        with cols[i]:
            label = f"Rp {nominal:,.0f}".replace(",", ".")
            if st.button(label, key=f"quick_{nominal}", use_container_width=True):
                add_sale(nominal, keterangan)
                st.success(f"✅ Dicatat: {fmt_rupiah(nominal)}")
                st.rerun()

    st.divider()
    st.markdown("#### Nominal Lainnya")
    c1, c2 = st.columns([2, 1])
    with c1:
        custom_val = st.number_input(
            "Masukkan nominal (Rp)", min_value=500, step=500,
            value=None, placeholder="contoh: 7500", label_visibility="collapsed", key="kasir_custom"
        )
    with c2:
        if st.button("➕ Catat", use_container_width=True, key="btn_custom"):
            if custom_val and custom_val >= 500:
                add_sale(int(custom_val), keterangan)
                st.success(f"✅ Dicatat: {fmt_rupiah(int(custom_val))}")
                st.rerun()
            else:
                st.warning("Masukkan nominal minimal Rp 500")

    st.divider()

    today_sales = sales_today()
    total = sum(s["nominal"] for s in today_sales)

    st.markdown(f"#### 📋 Riwayat Hari Ini &nbsp; — &nbsp; Total: **{fmt_rupiah(total)}**")

    if not today_sales:
        st.info("Belum ada penjualan hari ini. Mulai catat di atas!")
    else:
        for s in reversed(today_sales):
            ket = s.get("keterangan") or "—"
            c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
            c1.markdown(f"**{s['waktu']}**")
            c2.markdown(f"<span style='color:#16a34a;font-weight:600'>{fmt_rupiah(s['nominal'])}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color:#6b7280;font-size:0.9rem'>{ket}</span>", unsafe_allow_html=True)
            with c4:
                if st.button("🗑️", key=f"del_sale_{s['id']}", help="Hapus transaksi ini"):
                    delete_sale(s["id"])
                    st.rerun()
        st.caption(f"Total {len(today_sales)} transaksi")
