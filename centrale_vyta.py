import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import requests
import json

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="VYTA Centrale", layout="wide", page_icon="🚑")

# URL Cloud temporaneo per scambiare le coordinate tra Telefono e Mac
KV_URL = "https://kvdb.io/MN98H9A8yHaa89Hah91A/ambulanza_1"

# --- BARRA LATERALE ---
st.sidebar.title("🚑 VYTA Holding")
modalita = st.sidebar.radio("Seleziona il dispositivo attuale:", ["💻 CENTRALONE (Mac)", "📱 MEZZO IN VIAGGIO (Telefono)"])

# ---------------------------------------------------------
# INTERFACCIA TELEFONO (TRASMETTITORE GPS)
# ---------------------------------------------------------
if modalita == "📱 MEZZO IN VIAGGIO (Telefono)":
    st.title("📱 Pannello di Bordo Ambulanza")
    stato_mezzo = st.radio("Stato Operativo:", ["Libero", "In Servizio", "Fuori Servizio"], horizontal=True)

    # Invia la posizione dell'antenna del telefono ogni 5 secondi al cloud
    js_telefono = f"""
    <script>
    function inviaGps() {{
        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(function(pos) {{
                fetch("{KV_URL}", {{
                    method: "POST",
                    body: JSON.stringify({{
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        stato: "{stato_mezzo}",
                        ora: new Date().toLocaleTimeString()
                    }})
                }});
            }}, null, {{ enableHighAccuracy: true }});
        }}
    }}
    setInterval(inviaGps, 5000);
    </script>
    <div style="text-align: center; padding: 30px; background: #1e293b; border-radius: 10px; border: 2px dashed #2563eb;">
        <h2 style="color: #2563eb; margin: 0;">📡 TRASMISSIONE ATTIVA</h2>
        <p style="color: #94a3b8; margin: 5px 0 0 0;">Il telefono sta inviando le coordinate alla centrale...</p>
    </div>
    """
    components.html(js_telefono, height=160)

# ---------------------------------------------------------
# INTERFACCIA MAC (CENTRALE OPERATIVA COMPLETA)
# ---------------------------------------------------------
else:
    # Ricarica la pagina del Mac solo ogni 10 secondi per evitare refresh troppo scattosi
    components.html("""
    <script>
    setInterval(function(){ 
        const tabMappa = window.parent.document.querySelector('[aria-selected="true"]');
        if (tabMappa && tabMappa.textContent.includes("MAPPA INTERATTIVA LIVE")) {
            window.parent.location.reload(); 
        }
    }, 10 * 1000);
    </script>
    """, height=0, width=0)

    st.title("💻 VYTA Centrale Operativa")

    # Lettura delle coordinate inviate dallo smartphone
    try:
        res = requests.get(KV_URL)
        dati = json.loads(res.text) if res.status_code == 200 and res.text else {}
        lat = float(dati.get("lat", 45.5212))
        lon = float(dati.get("lon", 9.5924))
        stato = dati.get("stato", "In attesa")
        ora = dati.get("ora", "--:--")
    except:
        lat, lon, stato, ora = 45.5212, 9.5924, "Connessione Cloud...", "--:--"

    # Creazione delle 3 TAB classiche
    tab1, tab2, tab3 = st.tabs(["🌐 MAPPA INTERATTIVA LIVE", "📝 PRESA DELLA CHIAMATA", "📊 STORICO TRASPORTI"])

    with tab1:
        st.subheader("Flotta in Movimento")
        c1, c2, c3 = st.columns(3)
        c1.metric("Mezzo", "Ambulanza 1")
        c2.metric("Stato Live", stato)
        c3.metric("Ultimo Segnale", ora)
        
        st.markdown("---")
        
        # Mappa Folium aggiornata
        colore = "green" if stato == "Libero" else "red" if stato == "In Servizio" else "orange"
        m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB dark_matter")
        folium.Marker(
            location=[lat, lon],
            popup=f"Ambulanza 1 ({stato})",
            icon=folium.Icon(color=colore, icon="ambulance", prefix="fa")
        ).add_to(m)
        st_folium(m, width=1200, height=500)

    with tab2:
        st.subheader("Registrazione Servizio")
        with st.form("chiamata"):
            col_a, col_b = st.columns(2)
            cognome = col_a.text_input("Cognome Paziente *")
            nome = col_a.text_input("Nome Paziente")
            partenza = col_b.text_input("Da (Partenza) *")
            destinazione = col_b.text_input("A (Destinazione) *")
            note = st.text_area("Note Logistiche")
            
            if st.form_submit_button("INVIA ALL'AMBULANZA"):
                if cognome and partenza and destinazione:
                    st.success("✅ Servizio salvato nella centrale.")
                else:
                    st.error("Riempi i campi obbligatori (*)")

    with tab3:
        st.subheader("Archivio Storico VYTA")
        df_vuoto = pd.DataFrame(columns=["Orario", "Paziente", "Tratta", "Mezzo"])
        st.dataframe(df_vuoto, use_container_width=True)
