import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Mobile Optimierung
st.set_page_config(page_title="Finanz-Check AH", layout="centered")

# Schmaler blauer Header
st.markdown("""
    <style>
    .main-header {
        background-color: blue;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        color: white;
        margin-bottom: 15px;
    }
    .main-header h2 { margin: 0; font-size: 20px; }
    .main-header p { margin: 0; font-size: 14px; font-style: italic; }
    </style>
    <div class="main-header">
        <h2>Finanz-Check</h2>
        <p>Alexander Heide</p>
    </div>
    """, unsafe_allow_html=True)

# Eingabebereich oben
with st.expander("Eingabedaten hier anpassen", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        preis = st.number_input("Kaufpreis (€)", value=350000, step=1000)
        ek = st.number_input("Eigenkapital (€)", value=70000, step=1000)
    with col_b:
        zins = st.number_input("Sollzins p.a. (%)", value=3.8, step=0.1, format="%.2f")
        sonti_p = st.number_input("Sondertilgung p.a. (%)", value=1.0, step=0.5)

    # Korrigierte Tilgungswahl
    t_art = st.radio("Tilgungswahl:", ["in % p.a.", "in € monatlich"], horizontal=True)

    # Dynamische Beschriftung des Feldes
    label_tilg = "Tilgungssatz (%)" if "%%" in t_art or "%" in t_art else "Zusatztilgung (€/Monat)"
    t_val = st.number_input(label_tilg, value=2.0 if "%" in t_art else 500.0, step=0.1 if "%" in t_art else 50.0)

    makler_an = st.checkbox("Makler (3,57% BW) berücksichtigen", value=True)

# Rechnungslogik
m_kosten = preis * 0.0357 if makler_an else 0
n_kosten = preis * 0.07  # Notar + Steuer
darlehen = (preis + m_kosten + n_kosten) - ek

if darlehen > 0:
    z_dez = zins / 100

    # RECHNUNG KORRIGIERT
    if "in % p.a." in t_art:
        # Klassische Annuität: Rate = Darlehen * (Zins + Tilgung) / 12
        rate_m = darlehen * (z_dez + (t_val / 100)) / 12
    else:
        # Euro-Wahl: Rate = Monatliche Zinsen + gewählte Euro-Tilgung
        zins_monat_start = darlehen * (z_dez / 12)
        rate_m = zins_monat_start + t_val

    # Metriken
    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Darlehenssumme", f"{darlehen:,.2f} €")
    m2.metric("Monatliche Rate", f"{rate_m:,.2f} €")

    # Umschalter Ansicht
    st.markdown("---")
    view_m = st.toggle("Detaillierte Monatsansicht (Tabelle)", value=False)

    # Tilgungsplan Simulation
    plan = []
    rest = darlehen
    m = 1
    gz = 0
    s_euro = preis * (sonti_p / 100)

    while rest > 0.1 and m <= 600:
        zm = rest * (z_dez / 12)
        tm = min(rest, rate_m - zm)
        # Sondertilgung immer im Dezember (Monat 12, 24, 36...)
        sj = min(rest - tm, s_euro) if m % 12 == 0 and rest > s_euro else 0

        rest -= (tm + sj)
        gz += zm

        if view_m:
            plan.append(
                {"Monat": m, "Zins": round(zm, 2), "Tilgung": round(tm + sj, 2), "Rest": round(max(0, rest), 2)})
        elif m % 12 == 0 or rest <= 0.1:
            jahr = int(m / 12 if m % 12 == 0 else m // 12 + 1)
            plan.append({"Jahr": jahr, "Zins": round(zm * 12, 2), "Tilgung": round((tm * 12) + sj, 2),
                         "Rest": round(max(0, rest), 2)})
        m += 1

    df = pd.DataFrame(plan)

    # Chart & Tabelle
    st.line_chart(df.set_index("Monat" if view_m else "Jahr")["Rest"])
    st.dataframe(df, use_container_width=True)

    # Zusammenfassung
    st.success(f"**Zinsen gesamt:** {gz:,.2f} €  |  **Gesamtkosten:** {darlehen + gz:,.2f} €")
else:
    st.warning("Kein Darlehen nötig!")
