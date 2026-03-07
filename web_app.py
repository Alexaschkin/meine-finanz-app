import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Seiteneinstellungen für Mobile-Optimierung
st.set_page_config(page_title="AH Finanz-Check", layout="wide")

# Blauer Header mit CSS (Design-Anpassung)
st.markdown("""
    <style>
    .main-header {
        background-color: blue;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 22px; /* Optimal für Handy-Displays */
    }
    .main-header p {
        color: white;
        margin: 0;
        font-style: italic;
    }
    </style>
    <div class="main-header">
        <h1>Finanz-Check</h1>
        <p>Alexander Heide</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar für Eingaben
with st.sidebar:
    st.header("Eingaben")
    preis = st.number_input("Kaufpreis (€)", value=350000, step=5000)
    ek = st.number_input("Eigenkapital (€)", value=70000, step=5000)
    zins = st.slider("Sollzins p.a. (%)", 0.0, 10.0, 3.8, 0.1)

    tilg_wahl = st.radio("Tilgung in:", ["%", "€"])
    tilg_val = st.number_input("Tilgungswert", value=2.0 if tilg_wahl == "%" else 1000.0)

    sonti_prozent = st.slider("Sondertilgung p.a. (%)", 0.0, 10.0, 1.0, 0.5)
    makler_check = st.checkbox("Makler (3,57% BW)", value=True)

    st.markdown("---")
    # NEU: Der Umschalter für die Ansicht
    view_monthly = st.checkbox("Monatliche Details anzeigen", value=False)

# Berechnung der Basisdaten
makler = preis * 0.0357 if makler_check else 0
notar_steuer = preis * 0.07
darlehen = (preis + makler + notar_steuer) - ek
z_dez = zins / 100

if tilg_wahl == "%":
    rate_m = darlehen * (z_dez + (tilg_val / 100)) / 12
else:
    zins_start = darlehen * (z_dez / 12)
    rate_m = zins_start + tilg_val

# Kacheln (Metriken) oben
c1, c2 = st.columns(2)
c1.metric("Darlehen", f"{darlehen:,.2f} €")
c2.metric("Rate/Monat", f"{rate_m:,.2f} €")

# Simulation des Tilgungsplans
data = []
rest = darlehen
m = 1
ges_zins = 0
sonti_euro = preis * (sonti_prozent / 100)

while rest > 0.1 and m <= 600:  # Max 50 Jahre
    zm = rest * (z_dez / 12)
    tm = min(rest, rate_m - zm)
    sj = sonti_euro if m % 12 == 0 and rest > sonti_euro else 0
    rest -= (tm + sj)
    ges_zins += zm

    # Logik für die Tabellen-Anzeige
    if view_monthly:
        # Jeden Monat einzeln speichern
        data.append({
            "Monat": m,
            "Zins (€)": round(zm, 2),
            "Tilgung (€)": round(tm + sj, 2),
            "Restschuld (€)": round(max(0, rest), 2)
        })
    elif m % 12 == 0 or rest <= 0.1:
        # Nur Jahres-Summen speichern
        data.append({
            "Jahr": int(m / 12 if m % 12 == 0 else m // 12 + 1),
            "Zins (€)": round(zm * 12, 2),
            "Tilgung (€)": round((tm * 12) + sj, 2),
            "Restschuld (€)": round(max(0, rest), 2)
        })
    m += 1

df = pd.DataFrame(data)

# Diagramm anzeigen
st.markdown("### Rückzahlungsverlauf")
fig, ax = plt.subplots(figsize=(8, 3))
x_axis = "Monat" if view_monthly else "Jahr"
ax.plot(df[x_axis], df["Restschuld (€)"], color="blue", linewidth=2)
ax.fill_between(df[x_axis], df["Restschuld (€)"], color="blue", alpha=0.1)
ax.set_ylabel("Euro")
ax.set_xlabel(x_axis)
st.pyplot(fig)

# Ergebnistabelle anzeigen
st.markdown(f"### {'Monatliche' if view_monthly else 'Jährliche'} Übersicht")
st.dataframe(df, use_container_width=True)

# Zusammenfassung am Ende
st.info(f"**Gesamtzinsen:** {ges_zins:,.2f} € | **Gesamtkosten:** {(darlehen + ges_zins):,.2f} €")
