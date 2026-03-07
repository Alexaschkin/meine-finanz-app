import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Seiteneinstellungen
st.set_page_config(page_title="Finanzierungsrechner - Alexander Heide", layout="wide")

# Header
st.title("Finanzierungsprogramm")
st.subheader("Alexander Heide")
st.markdown("---")

# Sidebar für Eingaben
with st.sidebar:
    st.header("Eingabedaten")
    preis = st.number_input("Kaufpreis (€)", value=350000, step=5000)
    ek = st.number_input("Eigenkapital (€)", value=70000, step=5000)
    zins = st.slider("Sollzins p.a. (%)", 0.0, 10.0, 3.8, 0.1)

    tilg_wahl = st.radio("Tilgung angeben in:", ["Prozent (%)", "Euro (€)"])
    tilg_val = st.number_input("Anfängliche Tilgung", value=2.0 if tilg_wahl == "Prozent (%)" else 1000.0)

    sonti_prozent = st.slider("Sondertilgung p.a. (%)", 0.0, 10.0, 1.0, 0.5)
    makler_check = st.checkbox("Makler (3,57% BW)", value=True)

# Berechnung der Nebenkosten
makler = preis * 0.0357 if makler_check else 0
notar_steuer = preis * 0.07  # 5% Grunderwerb + 2% Notar
darlehen = (preis + makler + notar_steuer) - ek

# Ratenberechnung
z_dez = zins / 100
if tilg_wahl == "Prozent (%)":
    rate_m = darlehen * (z_dez + (tilg_val / 100)) / 12
else:
    rate_m = (darlehen * (z_dez / 12)) + tilg_val

# Anzeige der Basisdaten
col1, col2, col3 = st.columns(3)
col1.metric("Darlehenssumme", f"{darlehen:,.2f} €")
col2.metric("Monatliche Rate", f"{rate_m:,.2f} €")
col3.metric("Nebenkosten gesamt", f"{(makler + notar_steuer):,.2f} €")

# Tilgungsplan Simulation
data = []
rest = darlehen
m = 1
ges_zins = 0
sonti_euro = preis * (sonti_prozent / 100)

while rest > 0.1 and m <= 600:
    zm = rest * (z_dez / 12)
    tm = min(rest, rate_m - zm)
    sj = sonti_euro if m % 12 == 0 and rest > sonti_euro else 0
    rest -= (tm + sj)
    ges_zins += zm

    if m % 12 == 0 or rest <= 0.1:
        data.append({
            "Jahr": int(m / 12 if m % 12 == 0 else m // 12 + 1),
            "Zinsen (€)": round(zm * 12, 2),
            "Tilgung (€)": round((tm * 12) + sj, 2),
            "Restschuld (€)": round(max(0, rest), 2)
        })
    m += 1

df = pd.DataFrame(data)

# Visualisierung
st.markdown("### Rückzahlungsverlauf")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df["Jahr"], df["Restschuld (€)"], color="blue", linewidth=2)
ax.fill_between(df["Jahr"], df["Restschuld (€)"], color="blue", alpha=0.1)
ax.set_ylabel("Euro")
ax.set_xlabel("Jahre")
st.pyplot(fig)

# Tabelle & Zusammenfassung
st.markdown("### Jährliche Übersicht")
st.dataframe(df, use_container_width=True)

st.info(f"**Gesamtzinsen:** {ges_zins:,.2f} € | **Gesamtkosten:** {(darlehen + ges_zins):,.2f} €")
