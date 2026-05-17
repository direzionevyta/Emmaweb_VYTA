import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="VYTA Centrale Operativa", layout="wide", page_icon="🚑")

# --- CONNESSIONE REALE A GOOGLE SHEETS ---
def carica_dati_realtime():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Apriamo il file principale
        cartella = client.open("Centrale_VYTA_Cloud")
        
        # Leggiamo i due fogli reali
        foglio_servizi = cartella.worksheet("Servizi")
        foglio_flotta = cartella.worksheet("Flotta")
        
        df_servizi = pd.DataFrame(foglio_servizi.get_all_records())
        df_flotta = pd.DataFrame(foglio_flotta.get_all_records())
        
        return df_servizi, df_flotta, foglio_servizi
    except Exception as e:
        st.error(f"Errore di connessione al database reale: {e}")
        return pd.DataFrame(), pd.DataFrame(), None

df_servizi, df_flotta, conn_servizi = carica_dati_realtime()

# --- SIDEBAR: MONITORAGGIO FLOTTA DAL VIVO ---
st.sidebar.title("🚑 Flotta VYTA (Live)")
st.sidebar.markdown("---")

if not df_flotta.empty:
    for index, row in df_flotta.iterrows():
        status_icon = "🟢" if row['Stato'] == "Libero" else "🔴" if row['Stato'] == "In Servizio" else "🟡"
        st.sidebar.markdown(f"**{status_icon} {row['Mezzo']}**")
        st.sidebar.caption(f"Stato: {row['Stato']}")
        st.sidebar.caption(f"Equipaggio: {row['Autista']} | {row['Soccorritore']} | {row['Sanitario']}")
        st.sidebar.caption(f"Ultimo segnale: {row['Ultimo_Aggiornamento']}")
        st.sidebar.markdown("---")

# --- NAVIGAZIONE CENTRALE ---
tab1, tab2, tab3 = st.tabs(["🌐 MAPPA INTERATTIVA LIVE", "📝 PRESA DELLA CHIAMATA", "📊 STORICO TRASPORTI"])

with tab1:
    st.header("Quadro Operativo Real-Time")
    
    if not df_flotta.empty:
        # Centro la mappa sulla media delle posizioni reali dei mezzi
        centro_lat = df_flotta['Latitudine'].median()
        centro_lon = df_flotta['Longitudine'].median()
        
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=10, tiles="CartoDB dark_matter")
        
        # Piazziamo i marker reali sulla mappa usando i dati del foglio
        for index, row in df_flotta.iterrows():
            if row['Latitudine'] != 0 and row['Longitudine'] != 0:
                color_marker = "green" if row['Stato'] == "Libero" else "red" if row['Stato'] == "In Servizio" else "orange"
                
                popup_text = f"""
                <b>{row['Mezzo']}</b><br>
                Stato: {row['Stato']}<br>
                Equipaggio: {row['Autista']}, {row['Soccorritore']}, {row['Sanitario']}<br>
                Aggiornato: {row['Ultimo_Aggiornamento']}
                """
                
                folium.Marker(
                    location=[row['Latitudine'], row['Longitudine']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=row['Mezzo'],
                    icon=folium.Icon(color=color_marker, icon="ambulance", prefix="fa")
                ).add_to(m)
        
        st_folium(m, width=1200, height=500)
    else:
        st.warning("Nessun dato flotta disponibile. Configura il foglio 'Flotta' su Google Drive.")

with tab2:
    st.header("Triage Logistico / Presa Chiamata")
    # Il modulo rimane identico, scrive nel foglio "Servizi"
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
        
        # Carica dinamicamente i mezzi reali dal foglio per il menu a tendina
        lista_mezzi = df_flotta['Mezzo'].tolist() if not df_flotta.empty else ["Nessun mezzo configurato"]
        mezzo_scelto = st.selectbox("Assegna a Mezzo", lista_mezzi)
        
        if st.form_submit_button("TRASMETTI SERVIZIO A BORDO"):
            if conn_servizi is not None and cognome and da and a:
                nuovo_record = [
                    datetime.now().strftime("%Y%m%d-%H%M%S"),
                    datetime.now().strftime("%d/%m/%Y %H:%M"),
                    cognome, nome, cf, tel, tipo, deamb, da, a, note, mezzo_scelto, "IN ATTESA"
                ]
                conn_servizi.append_row(nuovo_record)
                st.success(f"✅ Servizio trasmesso in tempo reale a: {mezzo_scelto}")
                st.rerun()
            else:
                st.error("Compila i campi obbligatori o verifica la connessione.")

with tab3:
    st.header("Archivio Storico VYTA")
    if not df_servizi.empty:
        st.dataframe(df_servizi, use_container_width=True)
    else:
        st.info("Nessun servizio registrato nello storico.")
