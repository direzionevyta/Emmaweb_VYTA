import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURAZIONE DELLA PAGINA WEB ---
st.set_page_config(page_title="VYTA Centrale Operativa Live", layout="wide", page_icon="🚑")

# Stile CSS per un look moderno e scuro ("Tech")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .metric-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE REALE A GOOGLE SHEETS (File: Mezzi) ---
def carica_dati_realtime():
    try:
        # Definiamo i permessi di accesso a Google Drive
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Carichiamo le credenziali dai Secrets di Streamlit
        creds_dict = json.loads(st.secrets["https://docs.google.com/spreadsheets/d/1fB90cmSyBNn5Y_YW4nMD09z_RRLhkjN1UtvZHT9GpRM/edit?usp=sharing"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Apriamo il file principale usando il nome esatto ricavato dal tuo URL
        cartella = client.open("Mezzi")
        
        # Carichiamo i dati dalle due tab interne (fogli in basso)
        foglio_servizi = cartella.worksheet("Servizi")
        foglio_mezzi = cartella.worksheet("Mezzi")
        
        df_servizi = pd.DataFrame(foglio_servizi.get_all_records())
        df_mezzi = pd.DataFrame(foglio_mezzi.get_all_records())
        
        return df_servizi, df_mezzi, foglio_servizi
    except Exception as e:
        st.error(f"⚠️ Errore di connessione: verifica che nei 'Secrets' di Streamlit ci siano le credenziali e che le tab in basso su Google Sheets si chiamino esattamente 'Servizi' e 'Mezzi'. Dettaglio: {e}")
        return pd.DataFrame(), pd.DataFrame(), None

# Eseguiamo il caricamento live dei dati
df_servizi, df_mezzi, conn_servizi = carica_dati_realtime()

# --- BARRA LATERALE (SIDEBAR): MONITORAGGIO MEZZI IN DIRETTA ---
st.sidebar.title("🚑 Flotta VYTA (Live)")
st.sidebar.markdown("---")

if not df_mezzi.empty:
    for index, row in df_mezzi.iterrows():
        # Cambiamo il colore dell'icona in base allo stato reale del mezzo
        status_icon = "🟢" if row['Stato'] == "Libero" else "🔴" if row['Stato'] == "In Servizio" else "🟡"
        st.sidebar.markdown(f"**{status_icon} {row['Mezzo']}**")
        st.sidebar.caption(f"Stato: {row['Stato']}")
        st.sidebar.caption(f"Equipaggio: {row['Autista']} | {row['Soccorritore']} | {row['Sanitario']}")
        st.sidebar.caption(f"Ultimo segnale: {row['Ultimo_Aggiornamento']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.warning("Nessun mezzo trovato nel foglio 'Mezzi'.")

# --- NAVIGAZIONE PRINCIPALE A TAB ---
tab1, tab2, tab3 = st.tabs(["🌐 MAPPA INTERATTIVA LIVE", "📝 PRESA DELLA CHIAMATA", "📊 STORICO TRASPORTI"])

# --- TAB 1: LA MAPPA CON I MEZZI REALI ---
with tab1:
    st.header("Quadro Operativo Real-Time")
    
    # KPI di sintesi in alto
    c1, c2, c3 = st.columns(3)
    c1.metric("Mezzi Configurate", len(df_mezzi) if not df_mezzi.empty else 0)
    c2.metric("Servizi Totali", len(df_servizi) if not df_servizi.empty else 0)
    c3.metric("Stato Rete Cloud", "CONNESSO", delta="Google Drive OK")
    
    st.markdown("---")

    if not df_mezzi.empty:
        # Calcoliamo il centro della mappa in base alle coordinate dei mezzi inseriti
        centro_lat = df_mezzi['Latitudine'].median()
        centro_lon = df_mezzi['Longitudine'].median()
        
        # Creiamo la mappa scura professionale
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=10, tiles="CartoDB dark_matter")
        
        # Posizioniamo i marker per ogni mezzo reale
        for index, row in df_mezzi.iterrows():
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
        
        # Mostriamo la mappa a schermo intero nella dashboard
        st_folium(m, width=1200, height=500)
    else:
        st.warning("In attesa dei dati geografici. Assicurati che il foglio 'Mezzi' contenga le colonne Latitudine e Longitudine compilate.")

# --- TAB 2: IL MODULO DI TRIAGE PER PRENDERE LE CHIAMATE ---
with tab2:
    st.header("Triage Logistico / Presa della Chiamata")
    st.write("Compila l'intervista guidata mentre sei al telefono con l'utente:")
    
    with st.form("modulo_chiamata", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cognome = st.text_input("Cognome Paziente *")
            nome = st.text_input("Nome Paziente")
            cf = st.text_input("Codice Fiscale").upper()
            tel = st.text_input("Telefono Chiamante")
        with c2:
            tipo = st.selectbox("Tipo Richiesta *", ["Trasporto Semplice", "CMR", "Lunga Percorrenza", "Visita"])
            deamb = st.radio("Deambulazione *", ["Barellato", "Seggiolato", "Cammina"], horizontal=True)
            da = st.text_input("Da (Partenza) *")
            a = st.text_input("A (Destinazione) *")
            
        note = st.text_area("Note Logistiche (Scale, Ascensore, Gradini, Reparto ospedale...)")
        
        # Carichiamo dinamicamente la lista dei mezzi reali dal foglio per assegnare il servizio
        lista_mezzi = df_mezzi['Mezzo'].tolist() if not df_mezzi.empty else ["Nessun mezzo configurato"]
        mezzo_scelto = st.selectbox("Assegna a Mezzo VYTA *", lista_mezzi)
        
        # Tasto di invio
        if st.form_submit_button("TRASMETTI SERVIZIO A BORDO"):
            if conn_servizi is not None and cognome and da and a:
                # Creiamo la riga da appendere nel foglio "Servizi"
                nuovo_record = [
                    datetime.now().strftime("%Y%m%d-%H%M%S"),  # ID Servizio unico
                    datetime.now().strftime("%d/%m/%Y %H:%M"), # Data e ora chiamata
                    cognome, nome, cf, tel, tipo, deamb, da, a, note, mezzo_scelto, "IN ATTESA"
                ]
                # Invio al cloud
                conn_servizi.append_row(nuovo_record)
                st.success(f"✅ Servizio trasmesso in tempo reale all'equipaggio di: {mezzo_scelto}!")
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ Impossibile inviare. Compila tutti i campi obbligatori (*) e verifica la connessione.")

# --- TAB 3: LO STORICO COMPLETO DEI TRASPORTI ---
with tab3:
    st.header("Archivio Storico Servizi VYTA")
    if not df_servizi.empty:
        st.dataframe(df_servizi, use_container_width=True)
    else:
        st.info("Nessun servizio registrato nell'archivio della tab 'Servizi'.")
