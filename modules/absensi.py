import streamlit as st
from datetime import datetime, date
from modules.db import (
    load_absensi, absen_masuk, absen_keluar, tambah_catatan_kegiatan,
    absensi_today, absensi_sedang_masuk_today
)

JAM_REMINDER = 3  # jam, interval reminder catatan kegiatan


def _jam_terakhir_dari_catatan(catatan: str):
    """Ambil timestamp [HH:MM] terakhir dari string log catatan."""
    if not catatan:
        return None
    try:
        last_entry = catatan.split("|")[-1].strip()
        jam_str = last_entry.split("]")[0].replace("[", "").strip()
        h, m = jam_str.split(":")
        now = datetime.now()
        return now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
    except Exception:
        return None


def show():
    st.markdown("""
    <div class="main-header">
        <h1>Absensi Anggota</h1>
        <p>Jam masuk, jam keluar, dan log kegiatan berkala</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "Catatan: fitur foto kegiatan otomatis belum aktif (menunggu setup upload). "
        "Untuk sementara, log kegiatan tiap 3 jam dicatat dalam bentuk teks.",
        icon="ℹ️"
    )

    today_absen = absensi_today()
    sedang_masuk = absensi_sedang_masuk_today()

    col1, col2 = st.columns(2)
    col1.metric("Anggota Tercatat Hari Ini", len(today_absen))
    col2.metric("Sedang Bertugas Sekarang", len(sedang_masuk))

    st.divider()

    # ── Absen masuk ──────────────────────────────────────────────────────
    st.markdown("#### Absen Masuk")
    c1, c2 = st.columns([3, 1])
    with c1:
        nama_masuk = st.text_input("Nama Anggota", placeholder="contoh: Budi", key="nama_absen_masuk")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Catat Masuk", use_container_width=True):
            if nama_masuk:
                absen_masuk(nama_masuk)
                st.success(f"{nama_masuk} tercatat masuk pukul {datetime.now().strftime('%H:%M')}")
                st.rerun()
            else:
                st.warning("Isi nama anggota terlebih dahulu.")

    st.divider()

    # ── Anggota sedang bertugas ──────────────────────────────────────────
    st.markdown("#### Sedang Bertugas")
    if not sedang_masuk:
        st.info("Tidak ada anggota yang sedang bertugas saat ini.")
    else:
        for a in sedang_masuk:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 3, 2])
                c1.markdown(f"**{a['nama']}**")
                c1.caption(f"Masuk: {a['jam_masuk']}")

                # cek reminder catatan kegiatan tiap 3 jam
                jam_masuk_dt = None
                try:
                    h, m = a["jam_masuk"].split(":")
                    jam_masuk_dt = datetime.now().replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                except Exception:
                    pass

                jam_acuan = _jam_terakhir_dari_catatan(a.get("catatan_kegiatan", "")) or jam_masuk_dt
                if jam_acuan:
                    selisih_jam = (datetime.now() - jam_acuan).total_seconds() / 3600
                    if selisih_jam >= JAM_REMINDER:
                        c2.warning(f"Sudah {selisih_jam:.1f} jam sejak log terakhir. Saatnya catat kegiatan!")
                    else:
                        c2.caption(f"Log kegiatan berikutnya dalam ~{JAM_REMINDER - selisih_jam:.1f} jam")

                with c3:
                    if st.button("Catat Keluar", key=f"keluar_{a['id']}", use_container_width=True):
                        absen_keluar(a["id"])
                        st.success(f"{a['nama']} tercatat keluar.")
                        st.rerun()

                catatan_baru = st.text_input(
                    "Catatan kegiatan (3 jam sekali)",
                    placeholder="contoh: sedang produksi es batch 2",
                    key=f"catatan_{a['id']}"
                )
                if st.button("Tambah Catatan", key=f"add_catatan_{a['id']}"):
                    if catatan_baru:
                        tambah_catatan_kegiatan(a["id"], catatan_baru)
                        st.success("Catatan ditambahkan.")
                        st.rerun()
                    else:
                        st.warning("Isi catatan kegiatan terlebih dahulu.")

                if a.get("catatan_kegiatan"):
                    with st.expander("Riwayat log kegiatan"):
                        for entry in a["catatan_kegiatan"].split("|"):
                            st.caption(entry.strip())

    st.divider()

    # ── Riwayat hari ini ─────────────────────────────────────────────────
    with st.expander("Riwayat absensi hari ini"):
        if not today_absen:
            st.info("Belum ada absensi hari ini.")
        else:
            for a in reversed(today_absen):
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.markdown(f"**{a['nama']}**")
                c2.caption(f"Masuk: {a['jam_masuk']} • Keluar: {a['jam_keluar'] or 'belum'}")
                c3.caption(f"{len(a.get('catatan_kegiatan', '').split('|')) if a.get('catatan_kegiatan') else 0} catatan kegiatan")
