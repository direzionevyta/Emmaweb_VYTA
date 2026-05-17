import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import requests
import json

# --- CONFIGURAZIONE PAGINA CENTRALE ---
st.set_page_config(page_title="VYTA Centrale Operativa Live", layout="wide", page_icon="🚑")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

# URL del database temporaneo Key-Value
KV_URL = "https://kvdb.io/MN98H9A8yHaa89Hah91A/ambulanza_1"

# --- RILEVAMENTO TIPOLOGIA DISPOSITIVO ---
ua_script = """
<script>
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
window.parent.postMessage({type: 'streamlit:setComponentValue', value: isMobile}, '*');
</script>
"""
is_mobile_data = components.html(ua_script, height=0, width=0)
is_mobile = is_mobile_data if is_mobile_data is not None else False

# ---------------------------------------------------------
# INTERFACCIA TELEFONO (INVIA GPS)
# ---------------------------------------------------------
if is_mobile:
    st.title("📱 Terminale Ambulanza")
    st.write("Mantieni questa pagina attiva sul telefono.")
    
    stato_mezzo = st.radio("Stato attuale:", ["Libero", "In Servizio", "Fuori Servizio"], horizontal=True)

    # Raddoppiate tutte le parentesi graffe del codice JavaScript per non mandare in crash la f-string di Python
    js_gps_transmitter = f"""
    <script>
    function inviaPosizioneContinuo() {{
        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(
                function(position) {{
                    const payload = {{
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        stato: "{stato_mezzo}",
                        ora: new Date().toLocaleTimeString()
                    }};
                    
                    fetch("{KV_URL}", {{
                        method: "POST",
                        body: JSON.stringify(payload)
                    }});
                }},
                function(error) {{ console.log("Errore GPS"); }},
                {{ enableHighAccuracy: true }}
            );
        }}
    }}
    setInterval(inviaPosizioneContinuo, 4000);
    </script>
    <div style="text-align: center; padding: 25px; background-color: #1e293b; border-radius: 10px; border: 2px dashed #2563eb;">
        <h3 style="color: #2563eb; margin: 0 0 10px 0;">📡 TRASMISSIONE REALE ATTIVA</h3>
        <p style="color: #94a3b8; font-size: 15px; margin: 0;">Il telefono sta inviando i dati del posizionamento...</p>
    </div>
    """
    components.html(js_gps_transmitter, height=150)

# ---------------------------------------------------------
# INTERFACCIA MAC (MOSTRA MAPPA LIVE)
# ---------------------------------------------------------
else:
    # Auto-refresh del monitor ogni 5 secondi
    components.html("""
        <script>
        setInterval(function(){ window.parent.location.reload(); }, 5000);
        </script>
    """, height=0, width=0)

    st.title("💻 VYTA Holding - Monitoraggio Monitor Mac")
    
    # Recuperiamo l'ultimo dato inviato dal telefono nel database cloud
    try:
        res = requests.get(KV_URL)
        if res.status_code == 200 and res.text:
            dati_ambulanza = json.loads(res.text)
            lat_reale = float(dati_ambulanza.get("lat", 45.5212))
            lon_reale = float(dati_ambulanza.get("lon", 9.5924))
            stato_reale = dati_ambulanza.get("stato", "Disconnesso")
            ora_reale = dati_ambulanza.get("ora", "--:--")
        else:
            lat_reale, lon_reale, stato_reale, ora_reale = 45.5212, 9.5924, "In attesa di segnale", "Nessuna"
    except:
        lat_reale, lon_reale, stato_reale, ora_reale = 45.5212, 9.5924, "Errore connessione storage", "Nessuna"

    # Box Informazioni
    col1, col2, col3 = st.columns(3)
    col1.metric("Mezzo Rilevato", "Ambulanza 1 - Twinline")
    
    color_status = "🟢" if stato_reale == "Libero" else "🔴" if stato_reale == "In Servizio" else "🟡"
    col2.metric("Stato Operativo", f"{color_status} {stato_reale}")
    col3.metric("Ultimo Segnale Telefono", ora_reale)
    
    st.markdown("---")

    # Mappa Folium basata sulle coordinate inviate dal telefono
    color_marker = "green" if stato_reale == "Libero" else "red" if stato_reale == "In Servizio" else "orange"
    
    mappa_operativa = folium.Map(location=[lat_reale, lon_reale], zoom_start=15, tiles="CartoDB dark_matter")
    
    folium.Marker(
        location=[lat_reale, lon_reale],
        popup=f"Ambulanza 1 - {stato_reale}",
        tooltip="Ambulanza 1",
        icon=folium.Icon(color=color_marker, icon="ambulance", prefix="fa")
    ).add_to(mappa_operativa)
    
    st_folium(mappa_operativa, width=1300, height=550)
