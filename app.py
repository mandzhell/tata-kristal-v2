import streamlit as st

st.set_page_config(
    page_title="TATA Kristal - UMKM Manager",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Catatan: warna dipaksa eksplisit (bukan mengikuti variabel tema Streamlit)
# supaya tampilan tetap konsisten terbaca baik di light maupun dark mode sistem.
# .streamlit/config.toml juga memaksa base theme = light sebagai lapisan proteksi utama.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #1e293b !important; }
    h1, h2, h3, h4, .stMetric label { font-family: 'Syne', sans-serif !important; color: #0f172a !important; }

    .stApp { background-color: #ffffff !important; }

    .main-header {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%);
        padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
        box-shadow: 0 6px 24px rgba(14,165,233,0.25);
    }
    .main-header h1 { color: #ffffff !important; font-size: 1.8rem !important; margin: 0 !important; font-weight: 800 !important; }
    .main-header p { color: rgba(255,255,255,0.9) !important; margin: 0; font-size: 0.95rem; }

    .stMetric {
        background: #ffffff; padding: 1rem 1.2rem; border-radius: 10px;
        border: 1px solid #e0f2fe; box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; font-weight: 700; color: #0284c7 !important; }
    div[data-testid="stMetricLabel"] { color: #475569 !important; }

    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9, #0284c7); color: #ffffff !important;
        border: none; border-radius: 8px; font-weight: 600; padding: 0.5rem 1.2rem; transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(14,165,233,0.4); }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%) !important; }
    [data-testid="stSidebar"] * { color: #0f172a !important; }

    .sale-card {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;
        padding: 0.75rem 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between;
        color: #14532d !important;
    }
    .peng-card {
        background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px;
        padding: 0.75rem 1rem; margin-bottom: 0.5rem; color: #7c2d12 !important;
    }

    .stDataFrame { border-radius: 10px; overflow: hidden; }

    p, span, div, label { color: inherit; }
</style>
""", unsafe_allow_html=True)

if "prediction_status" not in st.session_state:
    st.session_state["prediction_status"] = "ready"

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### TATA Kristal")
    st.markdown("**UMKM Manager v2.1**")
    st.divider()

    menu = st.radio(
        "Navigasi",
        options=[
            "Beranda",
            "Kasir / POS",
            "Bon",
            "Stok Plastik",
            "Absensi",
            "Pengeluaran",
            "Laporan",
            "Prediksi AI",
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.success("Mode: Prediksi Rule-Based (tidak perlu internet/API)")

    st.divider()
    st.caption("Dibuat oleh Armanda Putra Rilda Lubis")
    st.caption("untuk UMKM TATA Kristal")

# ── PAGE ROUTING ───────────────────────────────────────────────────────────
if menu == "Beranda":
    from modules import beranda; beranda.show()
elif menu == "Kasir / POS":
    from modules import kasir; kasir.show()
elif menu == "Bon":
    from modules import bon; bon.show()
elif menu == "Stok Plastik":
    from modules import stok; stok.show()
elif menu == "Absensi":
    from modules import absensi; absensi.show()
elif menu == "Pengeluaran":
    from modules import pengeluaran; pengeluaran.show()
elif menu == "Laporan":
    from modules import laporan; laporan.show()
elif menu == "Prediksi AI":
    from modules import prediksi; prediksi.show()
