import streamlit as st

st.set_page_config(
    page_title="TATA Kristal - UMKM Manager",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3, .stMetric label { font-family: 'Syne', sans-serif !important; }
    .main-header {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%);
        padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
        box-shadow: 0 6px 24px rgba(14,165,233,0.25);
    }
    .main-header h1 { color: white !important; font-size: 1.8rem !important; margin: 0 !important; font-weight: 800 !important; }
    .main-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }
    .stMetric { background: white; padding: 1rem 1.2rem; border-radius: 10px; border: 1px solid #e0f2fe; box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
    div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; font-weight: 700; color: #0284c7; }
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9, #0284c7); color: white;
        border: none; border-radius: 8px; font-weight: 600; padding: 0.5rem 1.2rem; transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(14,165,233,0.4); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%); }
    .sale-card {
        background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;
        padding: 0.75rem 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between;
    }
    .peng-card {
        background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px;
        padding: 0.75rem 1rem; margin-bottom: 0.5rem;
    }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .api-key-box {
        background: #fefce8; border: 1px solid #fde68a; border-radius: 8px;
        padding: 0.6rem 0.8rem; margin-top: 0.5rem; font-size: 0.8rem; color: #92400e;
    }
</style>
""", unsafe_allow_html=True)

# ── API KEY MANAGEMENT ─────────────────────────────────────────────────────
# Coba baca dari secrets dulu, fallback ke session_state (input manual)
def get_api_key():
    return "local"

if "prediction_status" not in st.session_state:
    st.session_state["prediction_status"] = "ready"

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧊 TATA Kristal")
    st.markdown("**UMKM Manager v2.0**")
    st.divider()

    menu = st.radio(
        "Navigasi",
        options=["🏠 Beranda", "🧾 Kasir / POS", "📦 Stok Plastik", "💸 Pengeluaran", "📊 Laporan", "🤖 Prediksi AI"],
        label_visibility="collapsed"
    )

    st.divider()
    
    st.success("✅ Mode: Prediksi Rule-Based (tidak perlu internet/API)")

    st.divider()
    st.caption("Dibuat dengan ❤️ oleh Armanda Putra Rilda Lubis")
    st.caption("untuk UMKM TATA Kristal")

# ── PAGE ROUTING ───────────────────────────────────────────────────────────
if menu == "🏠 Beranda":
    from pages import beranda; beranda.show()
elif menu == "🧾 Kasir / POS":
    from pages import kasir; kasir.show()
elif menu == "📦 Stok Plastik":
    from pages import stok; stok.show()
elif menu == "💸 Pengeluaran":
    from pages import pengeluaran; pengeluaran.show()
elif menu == "📊 Laporan":
    from pages import laporan; laporan.show()
elif menu == "🤖 Prediksi AI":
    from pages import prediksi; prediksi.show()
