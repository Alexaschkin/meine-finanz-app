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
        <p>Alex Heide</p>
    </div>
    """, unsafe_allow_html=True)

# Eingabebereich oben
with st.expander("Eingabedaten hier anpassen", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        preis = st.number_input("Kaufpreis (€)", value=350000, step=5000)
        ek = st.number_input("Eigenkapital (€)", value=70000, step=5000)
        grunderwerb_p = st.number_input("Grunderwerbsteuer (%)", value=3.5, step=0.1)
        notar_p = st.number_input("Notar & Grundbuch (%)", value=2.0, step=0.1)
    with col_b:
        zins = st.number_input("Sollzins p.a. (%)", value=3.8, step=0.1, format="%.2f")
        sonti_p = st.number_input("Sondertilgung p.a. (%)", value=1.0, step=0.5)
        makler_an = st.checkbox("Makler (3,57% inkl. MwSt.)", value=True)

    # Berechnung der Nebenkosten
    m_kosten = preis * 0.0357 if makler_an else 0
    g_kosten = preis * (grunderwerb_p / 100)
    n_kosten = preis * (notar_p / 100)
    gesamtkosten = preis + m_kosten + g_kosten + n_kosten
    bedarf = gesamtkosten - ek

    st.markdown("---")
    st.write(f"**Kaufpreis:** {preis:,.2f} €")
    st.write(f"**Nebenkosten:** {m_kosten + g_kosten + n_kosten:,.2f} € (Steuer: {g_kosten:,.2f}€, Notar: {n_kosten:,.2f}€, Makler: {m_kosten:,.2f}€)")
    st.write(f"**Gesamtbedarf:** {gesamtkosten:,.2f} €")
    st.info(f"Rechnerischer Darlehensbedarf: {bedarf:,.2f} €")

    # Manuelle Darlehenseingabe
    darlehen = st.number_input("Tatsächliche Darlehenssumme (€)", value=float(round(bedarf, -2)), step=1000.0)

    st.markdown("---")
    t_art = st.radio("Tilgungswahl:", ["in % p.a.", "in € monatlich"], horizontal=True)
    label_tilg = "Anfängliche Tilgung (%)" if "%%" in t_art or "%" in t_art else "Zusatztilgung (€/Monat)"
    t_val = st.number_input(label_tilg, value=2.0 if "%" in t_art else 500.0, step=0.1 if "%" in t_art else 50.0)

# Rechnungslogik
if darlehen > 0:
    z_dez = zins / 100

    if "in % p.a." in t_art:
        rate_m = darlehen * (z_dez + (t_val / 100)) / 12
    else:
        zins_monat_start = darlehen * (z_dez / 12)
        rate_m = zins_monat_start + t_val

    # Metriken
    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Darlehenssumme", f"{darlehen:,.2f} €")
    m2.metric("Monatliche Rate", f"{rate_m:,.2f} €")

    view_m = st.toggle("Detaillierte Monatsansicht (Tabelle)", value=False)

    # Simulation
    plan = []
    rest = darlehen
    m = 1
    gz = 0
    s_euro = darlehen * (sonti_p / 100) # Sonti meist auf Darlehenssumme bezogen

    while rest > 0.1 and m <= 600:
        zm = rest * (z_dez / 12)
        tm = min(rest, rate_m - zm)
        sj = min(rest - tm, s_euro) if m % 12 == 0 and rest > s_euro else 0

        rest -= (tm + sj)
        gz += zm

        if view_m:
            plan.append({"Monat": m, "Zins": round(zm, 2), "Tilgung": round(tm + sj, 2), "Rest": round(max(0, rest), 2)})
        elif m % 12 == 0 or rest <= 0.1:
            jahr = int(m / 12 if m % 12 == 0 else m // 12 + 1)
            plan.append({"Jahr": jahr, "Rest": round(max(0, rest), 2)})
        m += 1

    df = pd.DataFrame(plan)

    # Statischer Chart mit Matplotlib (verhindert das Aufpoppen von Fenstern)
    fig, ax = plt.subplots(figsize=(8, 4))
    x_axis = "Monat" if view_m else "Jahr"
    ax.plot(df[x_axis], df["Rest"], color="blue", linewidth=2)
    ax.set_title("Restschuldverlauf")
    ax.set_xlabel(x_axis)
    ax.set_ylabel("Restbetrag (€)")
    ax.grid(True, linestyle="--", alpha=0.7)
    st.pyplot(fig)

    st.dataframe(df, use_container_width=True)
    st.success(f"**Zinsen gesamt:** {gz:,.2f} €  |  **Gesamtkosten:** {darlehen + gz:,.2f} €")
else:
    st.warning("Kein Darlehen erforderlich.")
