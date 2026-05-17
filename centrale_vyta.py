import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# --- CONFIGURAZIONE PAGINA CENTRALE ---
st.set_page_config(page_title="VYTA Centrale Operativa Mac", layout="wide", page_icon="🚑")

# Stile CSS Scuro Professionale
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .css-17l273f { background-color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- MEMORIA DI SESSIONE PER TRASMISSIONE DATI ---
if "lat" not in st.session_state:
    st.session_state.lat = 45.5212
if "lon" not in st.session_state:
    st.session_state.lon = 9.5924
if "nome_mezzo" not in st.session_state:
    st.session_state.nome_mezzo = "Ambulanza 1 - Twinline"
if "stato_mezzo" not in st.session_state:
    st.session_state.stato_mezzo = "Libero"

# --- RILEVAMENTO TIPOLOGIA DISPOSITIVO ---
# Usiamo un piccolo script per capire se l'utente è da Mobile o da Desktop
ua_script = """
<script>
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
window.parent.postMessage({type: 'streamlit:setComponentValue', value: isMobile}, '*');
</script>
"""
is_mobile_data = components.html(ua_script, height=0, width=0)
is_mobile = is_mobile_data if is_mobile_data is not None else False

# ---------------------------------------------------------
# SPREAD INTERFACCIA: SE SEI SUL TELEFONO (AMBULANZA)
# ---------------------------------------------------------
if is_mobile:
    st.title("📱 VYTA - Terminale di Bordo")
    st.write("Mantieni questa schermata aperta sul telefono per trasmettere la posizione dell'ambulanza.")
    
    st.session_state.nome_mezzo = st.selectbox("Seleziona il tuo Mezzo:", ["Ambulanza 1 - Twinline", "Ambulanza 2 - Delfis CR", "Ambulanza 3 - Tigis N20"])
    st.session_state.stato_mezzo = st.radio("Stato Operativo attuale:", ["Libero", "In Servizio", "Fuori Servizio"], horizontal=True)

    # JavaScript per agganciare il GPS nativo del telefono
    js_gps_transmitter = """
    <script>
    function inviaPosizioneContinuo() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const dati = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: dati}, '*');
                },
                function(error) { alert("Attiva il GPS e autorizza il browser!"); },
                { enableHighAccuracy: true }
            );
        }
    }
    // Avvia la trasmissione
    setInterval(inviaPosizioneContinuo, 3000);
    </script>
    <div style="text-align: center; padding: 20px; background-color: #1e293b; border-radius: 10px; border: 2px dashed #3b82f6;">
        <h3 style="color: #3b82f6; margin-0;">📡 TRASMISSIONE GPS ATTIVA</h3>
        <p style="color: #94a3b8; font-size: 14px;">Il telefono sta inviando le coordinate alla centrale...</p>
    </div>
    """
    
    dati_gps = components.html(js_gps_transmitter, height=120)
    
    if dati_gps:
        st.session_state.lat = dati_gps.get("latitude", st.session_state.lat)
        st.session_state.lon = dati_gps.get("longitude", st.session_state.lon)
        st.toast("📍 Coordinate GPS inviate alla centrale Mac!", icon="✅")

# ---------------------------------------------------------
# SPREAD INTERFACCIA: SE SEI SUL MAC (CENTRALE OPERATIVA)
# ---------------------------------------------------------
else:
    # Auto-refresh della centrale ogni 5 secondi per catturare gli spostamenti del telefono automaticamente
    components.html("""
        <script>
        setInterval(function(){ window.parent.location.reload(); }, 5000);
        </script>
    """, height=0, width=0)

    st.title("💻 VYTA Holding - Centrale Operativa H24")
    st.subheader("Quadro Geografico di Monitoraggio Flotta")
    
    # Visualizzazione dello Stato Attuale del Mezzo Mobile
    col1, col2, col3 = st.columns(3)
    col1.metric("Mezzo Monitorato", st.session_state.nome_mezzo)
    
    color_status = "🟢" if st.session_state.stato_mezzo == "Libero" else "🔴" if st.session_state.stato_mezzo == "In Servizio" else "🟡"
    col2.metric("Stato Operativo", f"{color_status} {st.session_state.stato_mezzo}")
    col3.metric("Aggiornamento Automatico", "Attivo (5s)")
    
    st.markdown("---")

    # Configurazione Colore Segnaposto sulla mappa
    color_marker = "green" if st.session_state.stato_mezzo == "Libero" else "red" if st.session_state.stato_mezzo == "In Servizio" else "orange"

    # Generazione Mappa Scura fissa sul Mac
    mappa_mac = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=14, tiles="CartoDB dark_matter")
    
    # Disegniamo il Marker dell'ambulanza (telefono) sulla mappa del Mac
    folium.Marker(
        location=[st.session_state.lat, st.session_state.lon],
        popup=f"<b>{st.session_state.nome_mezzo}</b><br>Stato: {st.session_state.stato_mezzo}",
        tooltip=st.session_state.nome_mezzo,
        icon=folium.Icon(color=color_marker, icon="ambulance", prefix="fa")
    ).add_to(mappa_mac)
    
    # Mostriamo la mappa a pieno schermo sul Mac
    st_folium(mappa_mac, width=1300, height=600)
    
    st.caption(f"Ultima coordinata ricevuta dal telefono a bordo: Lat {st.session_state.lat} | Lon {st.session_state.lon}")
