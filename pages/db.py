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

SHEET_SALES      = "sales"
SHEET_PENGELUARAN = "pengeluaran"
SHEET_STOK       = "stok"

SALES_HEADERS      = ["id", "tanggal", "waktu", "nominal", "keterangan"]
PENG_HEADERS       = ["id", "tanggal", "kategori", "nominal", "keterangan"]
STOK_HEADERS       = ["jumlah", "penuh"]


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
            ws.append_row([20, json.dumps([False] * 20)])
        return ws


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


def add_sale(nominal: int, keterangan: str = ""):
    ws = _get_sheet(SHEET_SALES)
    now = datetime.now()
    ws.append_row([
        int(now.timestamp() * 1000),
        str(date.today()),
        now.strftime("%H:%M"),
        nominal,
        keterangan,
    ])


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


# ── STOK ───────────────────────────────────────────────────────────────────

def load_stok():
    default = {"jumlah": 20, "penuh": [False] * 20}
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
        return {"jumlah": jumlah, "penuh": penuh[:jumlah]}
    except Exception:
        return default


def save_stok(data: dict):
    ws = _get_sheet(SHEET_STOK)
    ws.clear()
    ws.append_row(STOK_HEADERS)
    ws.append_row([data["jumlah"], json.dumps(data["penuh"])])


# ── HELPERS ────────────────────────────────────────────────────────────────

def fmt_rupiah(n: int) -> str:
    return f"Rp {n:,.0f}".replace(",", ".")


def all_dates():
    sales = load_sales()
    peng = load_pengeluaran()
    dates = set(s["tanggal"] for s in sales) | set(p["tanggal"] for p in peng)
    return sorted(dates, reverse=True)


KATEGORI_LABEL = {
    "listrik": "⚡ Listrik",
    "plastik": "🛍️ Plastik",
    "gaji": "👤 Gaji",
    "lainnya": "📋 Lainnya",
}
