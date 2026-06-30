import streamlit as st
from datetime import date
from modules.db import (
    load_bon, add_bon, delete_bon, lunaskan_bon,
    bon_today, bon_belum_lunas, total_piutang, fmt_rupiah,
    encode_foto_to_base64, decode_base64_to_bytes
)


def show():
    st.markdown("""
    <div class="main-header">
        <h1>Sistem Bon</h1>
        <p>Catat piutang pelanggan dengan validasi tanda tangan</p>
    </div>
    """, unsafe_allow_html=True)

    piutang = total_piutang()
    today_bon = bon_today()
    total_bon_today = sum(b["nominal"] for b in today_bon)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Piutang Belum Lunas", fmt_rupiah(piutang))
    col2.metric("Bon Hari Ini", fmt_rupiah(total_bon_today))
    col3.metric("Jumlah Bon Belum Lunas", len(bon_belum_lunas()))

    st.divider()

    # ── Form tambah bon ─────────────────────────────────────────────────
    st.markdown("#### Catat Bon Baru")
    with st.form("form_bon", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            nama_pelanggan = st.text_input("Nama Pelanggan", placeholder="contoh: Bu Ani")
            nominal = st.number_input("Nominal (Rp)", min_value=0, step=500, value=None,
                                       placeholder="contoh: 15000")
        with c2:
            ttd_nama = st.text_input(
                "Nama Geleng yang Menyetujui (wajib)",
                placeholder="nama anggota yang menyaksikan/menyetujui bon ini"
            )
            keterangan = st.text_input("Keterangan", placeholder="contoh: 3 bungkus es kristal")

        st.caption(f"Tanggal bon otomatis: {date.today().strftime('%d/%m/%Y')}")

        foto_ttd = st.file_uploader(
            "Foto Tanda Tangan",
            type=["jpg", "jpeg", "png"]
        )
        if foto_ttd is not None:
            st.image(foto_ttd, caption="Preview — pastikan tulisan nama GELENG terlihat jelas", width=250)

        submitted = st.form_submit_button("Simpan Bon", use_container_width=True)
        if submitted:
            if not nama_pelanggan:
                st.warning("Nama pelanggan wajib diisi.")
            elif not nominal or nominal <= 0:
                st.warning("Masukkan nominal yang valid.")
            elif not ttd_nama:
                st.warning("Nama geleng yang menyetujui wajib diisi — ini validasi anti pemalsuan bon.")
            elif foto_ttd is None:
                st.warning("Foto tanda tangan wajib diupload. Pastikan ada tulisan nama 'GELENG' di foto.")
            else:
                foto_b64 = encode_foto_to_base64(foto_ttd)
                add_bon(nama_pelanggan, int(nominal), keterangan, ttd_nama, foto_ttd_base64=foto_b64)
                st.success(f"Bon tercatat: {nama_pelanggan} — {fmt_rupiah(int(nominal))} (disetujui oleh {ttd_nama}, foto TTD tersimpan)")
                st.rerun()

    st.divider()

    # ── Daftar bon belum lunas ───────────────────────────────────────────
    st.markdown("#### Bon Belum Lunas")
    belum_lunas = bon_belum_lunas()
    if not belum_lunas:
        st.success("Tidak ada piutang yang belum lunas. Mantap!")
    else:
        for b in reversed(belum_lunas):
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.markdown(f"**{b['nama_pelanggan']}**")
                c1.caption(f"{b['tanggal']} • disetujui: {b['ttd_nama'] or '—'}")
                c2.markdown(f"<span style='color:#dc2626;font-weight:600'>{fmt_rupiah(b['nominal'])}</span>", unsafe_allow_html=True)
                c2.caption(b.get("keterangan") or "—")
                with c3:
                    if st.button("Tandai Lunas", key=f"lunas_{b['id']}", use_container_width=True):
                        lunaskan_bon(b["id"])
                        st.success("Bon dilunasi, dicatat sebagai pemasukan hari ini.")
                        st.rerun()
                with c4:
                    if st.button("Hapus", key=f"del_bon_{b['id']}", use_container_width=True):
                        delete_bon(b["id"])
                        st.rerun()

                foto_bytes = decode_base64_to_bytes(b.get("foto_ttd_base64", ""))
                if foto_bytes:
                    with st.expander("Lihat foto tanda tangan"):
                        st.image(foto_bytes, width=300, caption="Verifikasi: pastikan ada tulisan nama GELENG")

    st.divider()

    # ── Riwayat semua bon ────────────────────────────────────────────────
    with st.expander("Lihat semua riwayat bon (termasuk yang sudah lunas)"):
        all_bon = load_bon()
        if not all_bon:
            st.info("Belum ada bon tercatat.")
        else:
            for b in reversed(all_bon):
                status_label = "Lunas" if b["status"] == "lunas" else "Belum Lunas"
                status_color = "#16a34a" if b["status"] == "lunas" else "#dc2626"
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.markdown(f"**{b['nama_pelanggan']}** — {b['tanggal']}")
                c2.markdown(fmt_rupiah(b['nominal']))
                c3.markdown(f"<span style='color:{status_color};font-weight:600'>{status_label}</span>", unsafe_allow_html=True)
                c4.caption(f"TTD: {b['ttd_nama'] or '—'}")
