import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from io import StringIO
import json

# --- CONFIGURAZIONE DELLA PAGINA ---
st.set_page_config(page_title="VYTA Ecosystem", layout="wide", page_icon="🚑")

# ID del tuo foglio Google ricavato dall'URL
SPREADSHEET_ID = "1fB90cmSyBNn5Y_YW4nMD09z_RRLhkjN1UtvZHT9GpRM"

# Funzione di lettura dal Cloud
def carica_foglio_via_csv(nome_tab):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nome_tab}"
        response = requests.get(url)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# Selettore di modalità nell'interfaccia
st.sidebar.title("🎮 VYTA Control Mode")
modalita = st.sidebar.radio("Seleziona il dispositivo attuale:", ["💻 SCHERMO CENTRALE (Mac)", "📱 DISPOSITIVO A BORDO (Telefono)"])

# ---------------------------------------------------------
# MODALITÀ TELEFONO: IL TUO CELLULARE È L'AMBULANZA
# ---------------------------------------------------------
if modalita == "📱 DISPOSITIVO A BORDO (Telefono)":
    st.header("Interfaccia Mobile - Ambulanza Real-Time")
    st.write("Usa questa schermata sul telefono per inviare la tua posizione alla centrale.")
    
    mezzo_selezionato = st.selectbox("Seleziona quale mezzo sei:", [
        "Ambulanza 1 - Twinline", 
        "Ambulanza 2 - Delfis CR", 
        "Ambulanza 3 - Tigis N20"
    ])
    
    stato_mezzo = st.radio("Cambia il tuo stato operativo:", ["Libero", "In Servizio", "Fuori Servizio"], horizontal=True)

    # JavaScript per estrarre la posizione esatta dal chip GPS del telefono
    js_gps = """
    <script>
    function inviaPosizione() {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            // Creiamo un messaggio visibile a Streamlit
            const dati = {latitude: lat, longitude: lon, t: Date.now()};
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: dati}, '*');
        }, function(error) {
            alert("Per favore, attiva il GPS del telefono e dai i permessi al browser.");
        });
    }
    </script>
    <button onclick="inviaPosizione()" style="background-color: #2563eb; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; width: 100%; cursor: pointer;">
        📍 TRASMETTI COORDIDATE GPS LIVE
    </button>
    """
    
    st.markdown("---")
    st.subheader("Passo 1: Rileva Posizione")
    # Pulsante speciale che attiva l'antenna GPS dello smartphone
    valore_gps = st.components.v1.html(js_gps, height=80)
    
    st.subheader("Passo 2: Invia i dati")
    st.write("Dopo aver premuto il tasto blu sopra, conferma l'invio qui sotto per sincronizzare la mappa.")
    
    if st.button("AGGIORNA SULLA MAPPA DELLA CENTRALE"):
        st.success(f"Posizione inviata! Il mezzo {mezzo_selezionato} è ora impostato come '{stato_mezzo}'.")
        st.info("Nota: Per salvare la posizione sul foglio Google anche dal telefono senza chiavi API, apri direttamente l'app Google Fogli sul telefono e modifica i valori di Latitudine e Longitudine.")

# ---------------------------------------------------------
# MODALITÀ CENTRALE: IL MONITOR SUL MAC
# ---------------------------------------------------------
else:
    st.header("Centrale Operativa - Monitoraggio Flotta")
    
    # Carichiamo i dati inseriti nel foglio
    df_mezzi = carica_foglio_via_csv("Mezzi")
    df_servizi = carica_foglio_via_csv("Servizi")
    
    tab1, tab2 = st.tabs(["🌐 MAPPA LIVE", "📊 STORICO"])
    
    with tab1:
        if not df_mezzi.empty and 'Latitudine' in df_mezzi.columns:
            df_mappa = df_mezzi.dropna(subset=['Latitudine', 'Longitudine'])
            
            if not df_mappa.empty:
                centro_lat = df_mappa['Latitudine'].median()
                centro_lon = df_mappa['Longitudine'].median()
                
                m = folium.Map(location=[centro_lat, centro_lon], zoom_start=10, tiles="CartoDB dark_matter")
                
                for index, row in df_mappa.iterrows():
                    try:
                        lat = float(row['Latitudine'])
                        lon = float(row['Longitudine'])
                        
                        if lat != 0 and lon != 0:
                            color_marker = "green" if row['Stato'] == "Libero" else "red" if row['Stato'] == "In Servizio" else "orange"
                            
                            folium.Marker(
                                location=[lat, lon],
                                popup=f"<b>{row['Mezzo']}</b><br>Stato: {row['Stato']}<br>Staff: {row['Autista']}",
                                tooltip=str(row['Mezzo']),
                                icon=folium.Icon(color=color_marker, icon="ambulance", prefix="fa")
                            ).add_to(m)
                    except ValueError:
                        continue
                
                st_folium(m, width=1200, height=500)
            else:
                st.warning("Nessuna coordinata valida trovata nel foglio 'Mezzi'.")
        else:
            st.warning("Caricamento della flotta in corso...")
            
    with tab2:
        if not df_servizi.empty:
            st.dataframe(df_servizi, use_container_width=True)
        else:
            st.info("Nessun servizio attivo.")
