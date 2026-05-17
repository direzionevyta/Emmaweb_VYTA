import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from datetime import datetime
import requests
import json

# ==============================================================================
# SEZIONE 1: CONFIGURAZIONE GENERALE E STILE
# ==============================================================================
st.set_page_config(page_title="VYTA Centrale Operativa Live", layout="wide", page_icon="🚑")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .metric-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# SEZIONE 2: CANALE DI COMUNICAZIONE CLOUD (TELEFONO -> MAC)
# ==============================================================================
# Questo URL permette al telefono di inviare le coordinate e al Mac di leggerle
KV_URL = "https://kvdb.io/MN98H9A8yHaa89Hah91A/ambulanza_1"


# ==============================================================================
# SEZIONE 3: CONTROLLO DISPOSITIVO (BARRA LATERALE)
# ==============================================================================
st.sidebar.title("🚑 VYTA Ecosystem")
st.sidebar.markdown("---")

# Selettore manuale: decidi tu se quel dispositivo deve trasmettere (Telefono) o ricevere (Mac)
modalita = st.sidebar.radio(
    "Dispositivo in uso:", 
    ["💻 SCHERMO CENTRALE (Mac)", "📱 AMBULANZA A BORDO (Telefono)"]
)


# ==============================================================================
# SEZIONE 4: INTERFACCIA TELEFONO (TRASMETTITORE GPS)
# ==============================================================================
if modalita == "📱 AMBULANZA A BORDO (Telefono)":
    st.title("📱 Terminale di Bordo - Ambulanza Live")
    st.write("Mantieni questa schermata aperta sul telefono per aggiornare la centrale.")
    
    stato_mezzo = st.radio("Cambia il tuo Stato Operativo:", ["Libero", "In Servizio", "Fuori Servizio"], horizontal=True)

    # JavaScript che prende il GPS del telefono e lo spara nel Cloud per il Mac
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
    // Aggiorna ogni 4 secondi
    setInterval(inviaPosizioneContinuo, 4000);
    </script>
    <div style="text-align: center; padding: 25px; background-color: #1e293b; border-radius: 10px; border: 2px dashed #2563eb;">
        <h3 style="color: #2563eb; margin: 0 0 10px 0;">📡 TRASMISSIONE REALE ATTIVA</h3>
        <p style="color: #94a3b8; font-size: 15px; margin: 0;">Il telefono sta inviando la posizione al Mac...</p>
    </div>
    """
    components.html(js_gps_transmitter, height=150)


# ==============================================================================
# SEZIONE 5: INTERFACCIA MAC (CENTRALE OPERATIVA COMPLETA)
# ==============================================================================
else:
    # Auto-refresh invisibile per il Mac: ricarica la pagina ogni 5 secondi per aggiornare la mappa
    js_mac_refresh = """
    <script>
    setInterval(function(){ 
        const activeTab = window.parent.document.querySelector('[aria-selected="true"]');
        if (activeTab && activeTab.textContent.includes("MAPPA INTERATTIVA LIVE")) {
            window.parent.location.reload(); 
        }
    }, 5000);
    </script>
    """
    components.html(js_mac_refresh, height=0, width=0)

    st.title("💻 VYTA Holding - Centrale Operativa")
    
    # Scarichiamo i dati in tempo reale inviati dal telefono
    try:
        res = requests.get(KV_URL)
        if res.status_code == 200 and res.text:
            dati_ambulanza = json.loads(res.text)
            lat_reale = float(dati_ambulanza.get("lat", 45.5212))
            lon_reale = float(dati_ambulanza.get("lon", 9.5924))
            stato_reale = dati_ambulanza.get("stato", "Disconnesso")
            ora_reale = dati_ambulanza.get("ora", "--:--")
        else:
            lat_reale, lon_reale, stato_reale, ora_reale = 45.5212, 9.5924, "In attesa", "Nessuna"
    except:
        lat_reale, lon_reale, stato_reale, ora_reale = 45.5212, 9.5924, "Errore Cloud", "Nessuna"

    # Struttura iniziale a 3 TAB
    tab1, tab2, tab3 = st.tabs(["🌐 MAPPA INTERATTIVA LIVE", "📝 PRESA DELLA CHIAMATA", "📊 STORICO TRASPORTI"])

    # --- TAB 1: MAPPA LIVE ---
    with tab1:
        st.header("Quadro Operativo Real-Time")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Mezzo Monitorato", "Ambulanza 1 - Twinline")
        color_status = "🟢" if stato_reale == "Libero" else "🔴" if stato_reale == "In Servizio" else "🟡"
        c2.metric("Stato Operativo", f"{color_status} {stato_reale}")
        c3.metric("Ultimo Segnale", ora_reale)
        
        st.markdown("---")

        # Disegniamo la mappa con le coordinate del telefono
        color_marker = "green" if stato_reale == "Libero" else "red" if stato_reale == "In Servizio" else "orange"
        m = folium.Map(location=[lat_reale, lon_reale], zoom_start=14, tiles="CartoDB dark_matter")
        
        folium.Marker(
            location=[lat_reale, lon_reale],
            popup=f"<b>Ambulanza 1</b><br>Stato: {stato_reale}<br>Aggiornato: {ora_reale}",
            tooltip="Ambulanza 1",
            icon=folium.Icon(color=color_marker, icon="ambulance", prefix="fa")
        ).add_to(m)
        
        st_folium(m, width=1200, height=500)

    # --- TAB 2: MODULO CHIAMATA ---
    with tab2:
        st.header("Triage Logistico / Presa Chiamata")
        with st.form("modulo_chiamata", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                cognome = st.text_input("Cognome Paziente *")
                nome = st.text_input("Nome Paziente")
                cf = st.text_input("Codice Fiscale").upper()
                tel = st.text_input("Telefono Chiamante")
            with c2:
                tipo = st.selectbox("Tipo Richiesta", ["Trasporto Semplice", "CMR", "Lunga Percorrenza", "Visita"])
                deamb = st.radio("Deambulazione", ["Barellato", "Seggiolato", "Cammina"], horizontal=True)
                da = st.text_input("Da (Partenza)")
                a = st.text_input("A (Destinazione)")
                
            note = st.text_area("Note Logistiche (Scale, Ascensore, Reparto...)")
            mezzo_scelto = st.selectbox("Assegna a Mezzo", ["Ambulanza 1 - Twinline"])
            
            if st.form_submit_button("TRASMETTI SERVIZIO A BORDO"):
                st.success(f"✅ Servizio registrato per: {mezzo_scelto}")

    # --- TAB 3: STORICO ---
    with tab3:
        st.header("Archivio Storico VYTA")
        storico_vuoto = pd.DataFrame(columns=["ID", "Data", "Paziente", "Tipo", "Da", "A", "Mezzo"])
        st.dataframe(storico_vuoto, use_container_width=True)
