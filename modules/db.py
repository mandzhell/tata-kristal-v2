import json
import os
from datetime import date, datetime
from pathlib import Path

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ── GOOGLE SHEETS SETUP ────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_SALES       = "sales"
SHEET_PENGELUARAN = "pengeluaran"
SHEET_STOK        = "stok"
SHEET_BON         = "bon"
SHEET_ABSENSI     = "absensi"

SALES_HEADERS   = ["id", "tanggal", "waktu", "nominal", "keterangan"]
PENG_HEADERS    = ["id", "tanggal", "kategori", "nominal", "keterangan"]
STOK_HEADERS    = ["jumlah", "penuh", "kg_per_transaksi", "kg_terpakai_running"]
BON_HEADERS     = ["id", "tanggal", "nama_pelanggan", "nominal", "keterangan", "ttd_nama", "status", "tanggal_lunas", "foto_ttd_base64"]
ABSENSI_HEADERS = ["id", "nama", "tanggal", "jam_masuk", "jam_keluar", "catatan_kegiatan"]

DEFAULT_KG_PER_TRANSAKSI = 2.0
KG_PER_PLASTIK_ISI = 40  # 1 plastik penuh dianggap berisi 40kg pakai


@st.cache_resource(show_spinner=False)
def _get_client():
    """Buat koneksi ke Google Sheets (di-cache agar tidak reconnect terus)."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_spreadsheet():
    client = _get_client()
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])


def _get_sheet(name: str):
    """Ambil worksheet, buat otomatis kalau belum ada."""
    ss = _get_spreadsheet()
    try:
        return ss.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=1000, cols=10)
        if name == SHEET_SALES:
            ws.append_row(SALES_HEADERS)
        elif name == SHEET_PENGELUARAN:
            ws.append_row(PENG_HEADERS)
        elif name == SHEET_STOK:
            ws.append_row(STOK_HEADERS)
            ws.append_row([20, json.dumps([False] * 20), DEFAULT_KG_PER_TRANSAKSI, 0])
        elif name == SHEET_BON:
            ws.append_row(BON_HEADERS)
        elif name == SHEET_ABSENSI:
            ws.append_row(ABSENSI_HEADERS)
        return ws


# ── STOK (didefinisikan duluan karena dipakai sales & bon) ────────────────

def load_stok():
    default = {"jumlah": 20, "penuh": [False] * 20,
               "kg_per_transaksi": DEFAULT_KG_PER_TRANSAKSI, "kg_terpakai_running": 0.0}
    try:
        ws = _get_sheet(SHEET_STOK)
        records = ws.get_all_records()
        if not records:
            return default
        r = records[0]
        jumlah = int(r.get("jumlah", 20))
        penuh_raw = r.get("penuh", "[]")
        penuh = json.loads(penuh_raw) if isinstance(penuh_raw, str) else default["penuh"]
        while len(penuh) < jumlah:
            penuh.append(False)
        kg_per_transaksi = float(r.get("kg_per_transaksi", DEFAULT_KG_PER_TRANSAKSI) or DEFAULT_KG_PER_TRANSAKSI)
        kg_running = float(r.get("kg_terpakai_running", 0) or 0)
        return {"jumlah": jumlah, "penuh": penuh[:jumlah],
                "kg_per_transaksi": kg_per_transaksi, "kg_terpakai_running": kg_running}
    except Exception:
        return default


def save_stok(data: dict):
    ws = _get_sheet(SHEET_STOK)
    ws.clear()
    ws.append_row(STOK_HEADERS)
    ws.append_row([
        data["jumlah"], json.dumps(data["penuh"]),
        data.get("kg_per_transaksi", DEFAULT_KG_PER_TRANSAKSI),
        data.get("kg_terpakai_running", 0),
    ])


def consume_stok(kg: float):
    """Pakai stok otomatis sejumlah kg. Tiap akumulasi capai 40kg -> 1 plastik berubah jadi kosong."""
    if kg <= 0:
        return
    stok = load_stok()
    stok["kg_terpakai_running"] = stok.get("kg_terpakai_running", 0) + kg
    while stok["kg_terpakai_running"] >= KG_PER_PLASTIK_ISI:
        idx_terisi = next((i for i, v in enumerate(stok["penuh"]) if v), None)
        if idx_terisi is None:
            break  # tidak ada lagi plastik terisi, biarkan running menumpuk (akan jadi catatan kekurangan stok)
        stok["penuh"][idx_terisi] = False
        stok["kg_terpakai_running"] -= KG_PER_PLASTIK_ISI
    save_stok(stok)


# ── SALES ──────────────────────────────────────────────────────────────────

def load_sales():
    ws = _get_sheet(SHEET_SALES)
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append({
                "id": int(r["id"]),
                "tanggal": str(r["tanggal"]),
                "waktu": str(r["waktu"]),
                "nominal": int(r["nominal"]),
                "keterangan": str(r.get("keterangan", "")),
            })
        except Exception:
            pass
    return result


def save_sales(sales: list):
    ws = _get_sheet(SHEET_SALES)
    ws.clear()
    ws.append_row(SALES_HEADERS)
    for s in sales:
        ws.append_row([
            s["id"], s["tanggal"], s["waktu"],
            s["nominal"], s.get("keterangan", "")
        ])


def add_sale(nominal: int, keterangan: str = "", auto_consume_stok: bool = True):
    ws = _get_sheet(SHEET_SALES)
    now = datetime.now()
    ws.append_row([
        int(now.timestamp() * 1000),
        str(date.today()),
        now.strftime("%H:%M"),
        nominal,
        keterangan,
    ])
    if auto_consume_stok:
        stok = load_stok()
        consume_stok(stok.get("kg_per_transaksi", DEFAULT_KG_PER_TRANSAKSI))


def delete_sale(sale_id: int):
    ws = _get_sheet(SHEET_SALES)
    cell = ws.find(str(sale_id), in_column=1)
    if cell:
        ws.delete_rows(cell.row)


def sales_today():
    today = str(date.today())
    return [s for s in load_sales() if s["tanggal"] == today]


# ── PENGELUARAN ────────────────────────────────────────────────────────────

def load_pengeluaran():
    ws = _get_sheet(SHEET_PENGELUARAN)
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append({
                "id": int(r["id"]),
                "tanggal": str(r["tanggal"]),
                "kategori": str(r["kategori"]),
                "nominal": int(r["nominal"]),
                "keterangan": str(r.get("keterangan", "")),
            })
        except Exception:
            pass
    return result


def save_pengeluaran(data: list):
    ws = _get_sheet(SHEET_PENGELUARAN)
    ws.clear()
    ws.append_row(PENG_HEADERS)
    for p in data:
        ws.append_row([
            p["id"], p["tanggal"], p["kategori"],
            p["nominal"], p.get("keterangan", "")
        ])


def add_pengeluaran(tanggal: str, kategori: str, nominal: int, keterangan: str = ""):
    ws = _get_sheet(SHEET_PENGELUARAN)
    now = datetime.now()
    ws.append_row([
        int(now.timestamp() * 1000),
        tanggal, kategori, nominal, keterangan
    ])


def delete_pengeluaran(pid: int):
    ws = _get_sheet(SHEET_PENGELUARAN)
    cell = ws.find(str(pid), in_column=1)
    if cell:
        ws.delete_rows(cell.row)


def pengeluaran_today():
    today = str(date.today())
    return [p for p in load_pengeluaran() if p["tanggal"] == today]


# ── BON (PIUTANG PELANGGAN) ────────────────────────────────────────────────
# Bon = pelanggan ambil barang dulu, bayar belakangan.
# Saat bon dibuat: TIDAK dihitung sebagai pemasukan kas (karena belum dibayar),
# tapi stok tetap otomatis berkurang (barangnya sudah keluar).
# Saat bon dilunasi: baru dicatat sebagai pemasukan (masuk ke sheet sales).

def load_bon():
    ws = _get_sheet(SHEET_BON)
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append({
                "id": int(r["id"]),
                "tanggal": str(r["tanggal"]),
                "nama_pelanggan": str(r["nama_pelanggan"]),
                "nominal": int(r["nominal"]),
                "keterangan": str(r.get("keterangan", "")),
                "ttd_nama": str(r.get("ttd_nama", "")),
                "status": str(r.get("status", "belum_lunas")),
                "tanggal_lunas": str(r.get("tanggal_lunas", "")),
                "foto_ttd_base64": str(r.get("foto_ttd_base64", "")),
            })
        except Exception:
            pass
    return result


def save_bon(data: list):
    ws = _get_sheet(SHEET_BON)
    ws.clear()
    ws.append_row(BON_HEADERS)
    for b in data:
        ws.append_row([
            b["id"], b["tanggal"], b["nama_pelanggan"], b["nominal"],
            b.get("keterangan", ""), b.get("ttd_nama", ""),
            b.get("status", "belum_lunas"), b.get("tanggal_lunas", ""),
            b.get("foto_ttd_base64", ""),
        ])


def add_bon(nama_pelanggan: str, nominal: int, keterangan: str = "", ttd_nama: str = "",
            foto_ttd_base64: str = "", auto_consume_stok: bool = True):
    """Catat bon baru. Tanggal bon = hari ini otomatis."""
    ws = _get_sheet(SHEET_BON)
    now = datetime.now()
    ws.append_row([
        int(now.timestamp() * 1000),
        str(date.today()),
        nama_pelanggan,
        nominal,
        keterangan,
        ttd_nama,
        "belum_lunas",
        "",
        foto_ttd_base64,
    ])
    if auto_consume_stok:
        stok = load_stok()
        consume_stok(stok.get("kg_per_transaksi", DEFAULT_KG_PER_TRANSAKSI))


def encode_foto_to_base64(uploaded_file, max_size=(500, 500), quality=60):
    """Resize & compress foto TTD sebelum disimpan sebagai base64 di Google Sheets
    (sel Google Sheets dibatasi ~50.000 karakter, jadi foto wajib dikecilkan)."""
    from PIL import Image
    import io, base64

    img = Image.open(uploaded_file)
    img = img.convert("RGB")
    img.thumbnail(max_size)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded


def decode_base64_to_bytes(b64_string: str):
    import base64
    if not b64_string:
        return None
    try:
        return base64.b64decode(b64_string)
    except Exception:
        return None


def lunaskan_bon(bon_id: int):
    """Tandai bon lunas, dan catat nominalnya sebagai pemasukan (sales) hari ini."""
    bons = load_bon()
    target = None
    for b in bons:
        if b["id"] == bon_id:
            b["status"] = "lunas"
            b["tanggal_lunas"] = str(date.today())
            target = b
            break
    if target:
        save_bon(bons)
        add_sale(target["nominal"], f"Pelunasan bon - {target['nama_pelanggan']}", auto_consume_stok=False)


def delete_bon(bon_id: int):
    ws = _get_sheet(SHEET_BON)
    cell = ws.find(str(bon_id), in_column=1)
    if cell:
        ws.delete_rows(cell.row)


def bon_belum_lunas():
    return [b for b in load_bon() if b["status"] == "belum_lunas"]


def bon_today():
    today = str(date.today())
    return [b for b in load_bon() if b["tanggal"] == today]


def total_piutang():
    return sum(b["nominal"] for b in bon_belum_lunas())


# ── ABSENSI ANGGOTA ─────────────────────────────────────────────────────────

def load_absensi():
    ws = _get_sheet(SHEET_ABSENSI)
    records = ws.get_all_records()
    result = []
    for r in records:
        try:
            result.append({
                "id": int(r["id"]),
                "nama": str(r["nama"]),
                "tanggal": str(r["tanggal"]),
                "jam_masuk": str(r.get("jam_masuk", "")),
                "jam_keluar": str(r.get("jam_keluar", "")),
                "catatan_kegiatan": str(r.get("catatan_kegiatan", "")),
            })
        except Exception:
            pass
    return result


def save_absensi(data: list):
    ws = _get_sheet(SHEET_ABSENSI)
    ws.clear()
    ws.append_row(ABSENSI_HEADERS)
    for a in data:
        ws.append_row([
            a["id"], a["nama"], a["tanggal"],
            a.get("jam_masuk", ""), a.get("jam_keluar", ""),
            a.get("catatan_kegiatan", ""),
        ])


def absen_masuk(nama: str):
    ws = _get_sheet(SHEET_ABSENSI)
    now = datetime.now()
    ws.append_row([
        int(now.timestamp() * 1000),
        nama,
        str(date.today()),
        now.strftime("%H:%M"),
        "",
        "",
    ])


def absen_keluar(absensi_id: int):
    data = load_absensi()
    for a in data:
        if a["id"] == absensi_id:
            a["jam_keluar"] = datetime.now().strftime("%H:%M")
    save_absensi(data)


def tambah_catatan_kegiatan(absensi_id: int, catatan: str):
    """Tambah log kegiatan (pengganti foto tiap 3 jam, sementara foto belum aktif)."""
    data = load_absensi()
    waktu = datetime.now().strftime("%H:%M")
    for a in data:
        if a["id"] == absensi_id:
            existing = a.get("catatan_kegiatan", "")
            entry = f"[{waktu}] {catatan}"
            a["catatan_kegiatan"] = f"{existing} | {entry}" if existing else entry
    save_absensi(data)


def absensi_today():
    today = str(date.today())
    return [a for a in load_absensi() if a["tanggal"] == today]


def absensi_sedang_masuk_today():
    """Anggota yang sudah absen masuk tapi belum keluar hari ini."""
    return [a for a in absensi_today() if a["jam_masuk"] and not a["jam_keluar"]]


# ── HELPERS ────────────────────────────────────────────────────────────────

def fmt_rupiah(n: int) -> str:
    return f"Rp {n:,.0f}".replace(",", ".")


def all_dates():
    sales = load_sales()
    peng = load_pengeluaran()
    dates = set(s["tanggal"] for s in sales) | set(p["tanggal"] for p in peng)
    return sorted(dates, reverse=True)


KATEGORI_LABEL = {
    "listrik": "Listrik",
    "plastik": "Plastik",
    "gaji": "Gaji",
    "lainnya": "Lainnya",
}
