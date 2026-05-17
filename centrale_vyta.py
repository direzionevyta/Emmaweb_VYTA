import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from io import StringIO

# --- CONFIGURAZIONE DELLA PAGINA WEB ---
st.set_page_config(page_title="VYTA Centrale Operativa Live", layout="wide", page_icon="🚑")

# Stile CSS Tech
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .metric-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAZIONE LINK GOOGLE SHEETS ---
# ID del tuo file ricavato dal tuo URL
SPREADSHEET_ID = "1fB90cmSyBNn5Y_YW4nMD09z_RRLhkjN1UtvZHT9GpRM"

# Funzione per leggere i fogli tramite URL CSV (Metodo Alternativo senza chiavi API)
def carica_foglio_via_csv(nome_tab):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nome_tab}"
        response = requests.get(url)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Errore di caricamento tab {nome_tab}: {e}")
        return pd.DataFrame()

# Caricamento dati in tempo reale
df_servizi = carica_foglio_via_csv("Servizi")
df_mezzi = carica_foglio_via_csv("Mezzi")

# --- BARRA LATERALE (SIDEBAR): MONITORAGGIO MEZZI IN DIRETTA ---
st.sidebar.title("🚑 Flotta VYTA (Live)")
st.sidebar.markdown("---")

if not df_mezzi.empty and 'Mezzo' in df_mezzi.columns:
    for index, row in df_mezzi.iterrows():
        # Controllo di sicurezza per evitare righe vuote nel foglio
        if pd.isna(row['Mezzo']) or row['Mezzo'] == "":
            continue
        status_icon = "🟢" if row['Stato'] == "Libero" else "🔴" if row['Stato'] == "In Servizio" else "🟡"
        st.sidebar.markdown(f"**{status_icon} {row['Mezzo']}**")
        st.sidebar.caption(f"Stato: {row['Stato']}")
        st.sidebar.caption(f"Equipaggio: {row['Autista']} | {row['Soccorritore']} | {row['Sanitario']}")
        st.sidebar.caption(f"Ultimo segnale: {row['Ultimo_Aggiornamento']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.warning("Nessun mezzo trovato o errore di intestazione nel foglio 'Mezzi'.")

# --- NAVIGAZIONE PRINCIPALE A TAB ---
tab1, tab2, tab3 = st.tabs(["🌐 MAPPA INTERATTIVA LIVE", "📝 FUNZIONI DI SCRITTURA", "📊 STORICO TRASPORTI"])

# --- TAB 1: LA MAPPA CON I MEZZI REALI ---
with tab1:
    st.header("Quadro Operativo Real-Time")
    
    c1, c2, c3 = st.columns(3)
    c2.metric("Mezzi Configurate", len(df_mezzi) if not df_mezzi.empty else 0)
    c3.metric("Servizi Totali", len(df_servizi) if not df_servizi.empty else 0)
    
    st.markdown("---")

    if not df_mezzi.empty and 'Latitudine' in df_mezzi.columns:
        # Pulizia dati da eventuali righe nulle
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
                        
                        popup_text = f"""
                        <b>{row['Mezzo']}</b><br>
                        Stato: {row['Stato']}<br>
                        Equipaggio: {row['Autista']}, {row['Soccorritore']}, {row['Sanitario']}<br>
                        Aggiornato: {row['Ultimo_Aggiornamento']}
                        """
                        
                        folium.Marker(
                            location=[lat, lon],
                            popup=folium.Popup(popup_text, max_width=300),
                            tooltip=row['Mezzo'],
                            icon=folium.Icon(color=color_marker, icon="ambulance", prefix="fa")
                        ).add_to(m)
                except ValueError:
                    continue
            
            st_folium(m, width=1200, height=500)
        else:
            st.warning("Inserisci delle coordinate GPS valide nel foglio 'Mezzi' per attivare la mappa.")
    else:
        st.warning("In attesa dei dati geografici della flotta.")

# --- TAB 2: INFORMAZIONI DI COLLEGAMENTO ---
with tab2:
    st.header("Gestione Flotta e Inserimenti")
    st.info("ℹ️ Con questo metodo di lettura semplificato via Web, la Centrale legge i dati dal cloud in tempo reale.")
    st.write("Per inserire nuovi servizi o fare in modo che i telefoni aggiornino le posizioni, usa l'applicazione mobile o compila direttamente le righe sul tuo file Google Sheets dal browser.")

# --- TAB 3: LO STORICO COMPLETO DEI TRASPORTI ---
with tab3:
    st.header("Archivio Storico Servizi VYTA")
    if not df_servizi.empty:
        st.dataframe(df_servizi, use_container_width=True)
    else:
        st.info("Nessun servizio registrato nell'archivio della tab 'Servizi'.")
