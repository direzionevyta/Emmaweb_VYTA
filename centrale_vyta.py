import streamlit as str
from datetime import datetime
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# Impostazioni della pagina Streamlit
str.set_page_config(page_title="VYTA Holding - Centrale", page_icon="🚑", layout="centered")

str.title("🚑 VYTA Holding")
str.subheader("Centrale Operativa Cloud H24 - Triage Logistico")

# --- CONFIGURAZIONE SICUREZZA GOOGLE CLOUD ---
NOME_FOGLIO_GOOGLE = "Centrale_VYTA_Cloud"

def connetti_a_google_sheets():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Per Streamlit Cloud, useremo i "Secrets" per non caricare il file JSON pubblico su GitHub
        if "google_credentials" in str.secrets:
            creds_dict = json.loads(str.secrets["google_credentials"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # Backup se provi in locale con il file json
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenziali_vyta.json", scope)
            
        client = gspread.authorize(creds)
        return client.open(NOME_FOGLIO_GOOGLE).sheet1
    except Exception as e:
        str.error(f"Errore di connessione a Google Sheets: {e}")
        return None

# --- INTERFACCIA UTENTE (Modulo Intervista) ---
str.write("Compila i dati durante la chiamata dell'utente:")

with str.form("modulo_triage", clear_on_submit=True):
    col1, col2 = str.columns(2)
    
    with col1:
        cognome = str.text_input("Cognome Paziente *")
        nome = str.text_input("Nome Paziente")
        nascita = str.text_input("Data di Nascita (GG/MM/AAAA)")
        cf = str.text_input("Codice Fiscale").upper()
        
    with col2:
        tel = str.text_input("Telefono (Chiamante/Pz)")
        email = str.text_input("Email per Fattura")
        tipo_richiesta = str.selectbox("Tipo di Richiesta *", [
            "Trasporto Sanitario Semplice", 
            "CMR (Centro Mobile Rianimazione)", 
            "Trasporto a lunga percorrenza", 
            "Visita specialistica"
        ])
        deamb = str.selectbox("Stato del Paziente *", ["Barellato", "Seggiolato", "Cammina (Deambulante)"])

    partenza = str.text_input("Partenza (Da) *")
    destinazione = str.text_input("Destinazione (A) *")
    note = str.text_area("Note Logistiche (Ascensore, Gradini, Reparto...)")
    
    str.markdown("### 🎯 Assegnazione Flotta")
    mezzo = str.selectbox("Assegna a Mezzo VYTA *", ["Ambulanza 1 - Twinline", "Ambulanza 2 - Delfis CR", "Ambulanza 3 - Tigis N20"])

    # Bottone di invio
    submit = str.form_submit_button("INVIA SERVIZIO AL CLOUD GOOGLE")

if submit:
    if not cognome or not partenza or not destinazione:
        str.warning("⚠️ Compila i campi obbligatori (*)")
    else:
        foglio_cloud = connetti_a_google_sheets()
        if foglio_cloud:
            nuovo_servizio = [
                datetime.now().strftime("%Y%m%d-%H%M%S"),
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                cognome, nome, nascita, cf, tel, email,
                tipo_richiesta, partenza, destinazione, deamb,
                note, mezzo, "IN ATTESA"
            ]
            try:
                foglio_cloud.append_row(nuovo_servizio)
                str.success(f"✅ Servizio registrato con successo! Assegnato a: {mezzo}")
            except Exception as e:
                str.error(f"Errore nell'invio dei dati: {e}")
