import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="VYTA Centrale H24", layout="wide", page_icon="🚑")

# Stile CSS per rendere l'interfaccia "Tech"
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .metric-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNESSIONE GOOGLE SHEETS ---
def get_cloud_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Assicurati che il foglio si chiami esattamente così
        sheet = client.open("Centrale_VYTA_Cloud").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data), sheet
    except:
        # Fallback per test locale se non ci sono i secrets
        return pd.DataFrame(), None

df_servizi, sheet_conn = get_cloud_data()

# --- SIDEBAR: STATO FLOTTA ---
st.sidebar.title("🚑 Flotta VYTA")
st.sidebar.markdown("---")

# Simuliamo i dati della flotta (In un'app reale questi sarebbero su un altro foglio Google)
flotta = {
    "Ambulanza 1 - Twinline": {"Stato": "Libero", "Equipaggio": "Socc. Rossi / Inf. Bianchi", "Pos": [45.52, 9.59]},
    "Ambulanza 2 - Delfis CR": {"Stato": "In Servizio", "Equipaggio": "Socc. Verdi / Med. Neri", "Pos": [45.43, 9.12]},
    "Ambulanza 3 - Tigis N20": {"Stato": "Libero", "Equipaggio": "Socc. Esposito / Inf. Greco", "Pos": [45.54, 10.21]}
}

for mezzo, info in flotta.items():
    color = "🟢" if info["Stato"] == "Libero" else "🔴"
    st.sidebar.markdown(f"**{color} {mezzo}**")
    st.sidebar.caption(f"Staff: {info['Equipaggio']}")
    st.sidebar.progress(100 if info["Stato"] == "Libero" else 40)

# --- NAVIGAZIONE PRINCIPALE ---
tab1, tab2, tab3 = st.tabs(["🌐 HOME - MAPPA LIVE", "📝 NUOVA CHIAMATA", "📊 ARCHIVIO SERVIZI"])

with tab1:
    st.header("Centrale Operativa VYTA - Monitoraggio Real-Time")
    
    # 1. KPI Superiori
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mezzi Operativi", "3/3", "100%")
    c2.metric("Servizi Oggi", len(df_servizi) if not df_servizi.empty else 0)
    c3.metric("Tempo Medio Presa Carico", "4.2 min")
    c4.metric("Stato Zoll/Lucas", "OK", delta="In Carica")

    # 2. MAPPA (Utilizziamo Folium)
    st.subheader("Localizzazione Mezzi (Hinterland BG-BS)")
    m = folium.Map(location=[45.5, 9.8], zoom_start=9, tiles="CartoDB dark_matter")
    
    # Aggiungiamo i mezzi sulla mappa
    for mezzo, info in flotta.items():
        icon_color = "green" if info["Stato"] == "Libero" else "red"
        folium.Marker(
            location=info["Pos"],
            popup=f"{mezzo}\n{info['Equipaggio']}",
            tooltip=mezzo,
            icon=folium.Icon(color=icon_color, icon="ambulance", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width=1200, height=450)

    # 3. Tabella Servizi in corso
    st.subheader("📋 Servizi Attivi")
    if not df_servizi.empty:
        # Mostriamo solo gli ultimi 5 servizi attivi
        attivi = df_servizi[df_servizi['Stato_Servizio'] != 'CONCLUSO'].tail(5)
        st.dataframe(attivi[['ID_Servizio', 'Cognome', 'Partenza_Da', 'Destinazione_A', 'Assegnazione_Mezzo', 'Stato_Servizio']], use_container_width=True)
    else:
        st.info("Nessun servizio attivo al momento.")

with tab2:
    st.header("Intervista Triage Logistico")
    with st.form("nuovo_servizio", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            cognome = st.text_input("Cognome Paziente *")
            nome = st.text_input("Nome Paziente")
            cf = st.text_input("Codice Fiscale").upper()
            tel = st.text_input("Telefono Chiamante")
        with col_b:
            tipo = st.selectbox("Tipologia", ["T. Semplice", "CMR", "Lunga Percorrenza", "Visita"])
            deamb = st.radio("Deambulazione", ["Barellato", "Seggiolato", "Cammina"], horizontal=True)
            da = st.text_input("Partenza (Da)")
            a = st.text_input("Arrivo (A)")
        
        note = st.text_area("Note (Scale, Ascensore, Reparto...)")
        mezzo_assegnato = st.selectbox("Assegna Mezzo", list(flotta.keys()))
        
        if st.form_submit_button("INVIA ALL'AMBULANZA"):
            if sheet_conn:
                nuovo = [datetime.now().strftime("%H:%M"), cognome, nome, cf, tel, tipo, deamb, da, a, note, mezzo_assegnato, "IN ATTESA"]
                sheet_conn.append_row(nuovo)
                st.success("Servizio inviato correttamente!")
                st.balloons()

with tab3:
    st.header("Storico Trasporti")
    if not df_servizi.empty:
        st.dataframe(df_servizi)
        st.download_button("Scarica Report Excel", df_servizi.to_csv(), "report_vyta.csv")
    else:
        st.warning("Archivio vuoto.")
