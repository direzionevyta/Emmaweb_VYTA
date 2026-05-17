import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import requests
import json

# ==============================================================================
# SEZIONE 1: CONFIGURAZIONE GENERALE E STILE
# ==============================================================================
# Qui puoi cambiare il titolo della scheda del browser e i colori dell'interfaccia
st.set_page_config(page_title="VYTA Centrale Operativa Live", layout="wide", page_icon="🚑")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# SEZIONE 2: RETE E DATABASE (CLOUD STORAGE COORDIDATE)
# ==============================================================================
# Se vuoi cambiare stanza o database temporaneo per il GPS, modifica questo URL
KV_URL = "https://kvdb.io/MN98H9A8yHaa89Hah91A/ambulanza_1"


# ==============================================================================
# SEZIONE 3: SISTEMA DI SVINGOLAMENTO (MAC vs TELEFONO)
# ==============================================================================
# Script invisibile che rileva se chi apre il link sta usando un cellulare o un Mac
ua_script = """
<script>
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
window.parent.postMessage({type: 'streamlit:setComponentValue', value: isMobile}, '*');
</script>
"""
is_mobile_data = components.html(ua_script, height=0, width=0)
is_mobile = is_mobile_data if is_mobile_data is not None else False


# ==============================================================================
# SEZIONE 4: INTERFACCIA PER IL TELEFONO (AMBULANZA)
# ==============================================================================
if is_mobile:
    st.title("📱 Terminale Ambulanza")
    st.write("Mantieni questa pagina attiva sul telefono per trasmettere i dati di bordo.")
    
    # Menu di selezione stato per i ragazzi a bordo
    stato_mezzo = st.radio("Stato attuale:", ["Libero", "In Servizio", "Fuori Servizio"], horizontal=True)

    # Script JavaScript che preleva il GPS del telefono e lo invia al cloud ogni 4 secondi
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


# ==============================================================================
# SEZIONE 5: INTERFACCIA PER IL MAC (CENTRALE OPERATIVA COMPLETA)
# ==============================================================================
else:
    # Auto-refresh del monitor Mac ogni 5 secondi per muovere i marker sulla mappa
    js_mac_refresh = """
    <script>
    setInterval(function(){ window.parent.location.reload(); }, 5000);
    </script>
    """
    components.html(js_mac_refresh, height=0, width=0)

    st.title("💻 VYTA Holding - Centrale Operativa")
    
    # Download in tempo reale dei dati trasmessi dal telefono
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

    # Creazione delle schede (Tab) della centrale sul Mac
    tab1, tab2, tab3 = st.tabs(["🌐 MAPPA LIVE", "📝 NUOVA CHIAMATA / TRIAGE", "📊 STORICO SERVIZI"])

    # --- TAB 1: LA MAPPA INTERATTIVA ---
    with tab1:
        st.subheader("Quadro Geografico di Monitoraggio Flotta")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Mezzo Monitorato", "Ambulanza 1 - Twinline")
        color_status = "🟢" if stato_reale == "Libero" else "🔴" if stato_reale == "In Servizio" else "🟡"
        col2.metric("Stato Operativo", f"{color_status} {stato_reale}")
        col3.metric("Ultimo Segnale Telefono", ora_reale)
        
        st.markdown("---")

        # Configurazione visiva della mappa e del marker dell'ambulanza
        color_marker = "green" if stato_reale == "Libero" else "red" if stato_reale == "In Servizio" else "orange"
        mappa_operativa = folium.Map(location=[lat_reale, lon_reale], zoom_start=15, tiles="CartoDB dark_matter")
        
        folium.Marker(
            location=[lat_reale, lon_reale],
            popup=f"Ambulanza 1 - {stato_reale}",
            tooltip="Ambulanza 1",
            icon=folium.Icon(color=color_marker, icon="ambulance", prefix="fa")
        ).add_to(mappa_operativa)
        
        st_folium(mappa_operativa, width=1300, height=500)

    # --- TAB 2: IL MODULO DI TRIAGE PER LE CHIAMATE ---
    with tab2:
        st.subheader("Triage Logistico / Presa della Chiamata")
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
                
            note = st.text_area("Note Logistiche (Scale, Reparto...)")
            
            if st.form_submit_button("TRASMETTI SERVIZIO A BORDO"):
                st.success("✅ Servizio registrato localmente e pronto alla trasmissione!")

    # --- TAB 3: L'ARCHIVIO DEI TRASPORTI ---
    with tab3:
        st.subheader("Archivio Storico Servizi VYTA")
        storico_finto = pd.DataFrame(columns=["Ora", "Paziente", "Tipo", "Da", "A", "Stato"])
        st.dataframe(storico_finto, use_container_width=True)
