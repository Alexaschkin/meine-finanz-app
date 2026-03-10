import streamlit as st
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt

# 1. Layout-Einstellungen
st.set_page_config(page_title="Finanz-Check AH", layout="centered")


# 2. Hilfsfunktion für deutsches Zahlenformat
def format_de(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


# 3. CSS für Styling und Mobile-Optimierung
st.markdown("""
    <style>
    .main-header { background-color: blue; padding: 10px; border-radius: 8px; text-align: center; color: white; margin-bottom: 20px; }
    .main-header h2 { margin: 0; font-size: 20px; }
    .main-header p { margin: 0; font-size: 14px; font-style: italic; }
    .kosten-liste { background-color: #f8f9fa; padding: 15px; border-radius: 12px; font-size: 0.9rem; border: 1px solid #e9ecef; margin-bottom: 20px; }
    .flex-row { display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 4px 0; }
    .total-row { border-top: 2px solid #333; margin-top: 8px; padding-top: 8px; font-weight: bold; }
    .view-toggle-box { background-color: #e8f0fe; padding: 10px; border-radius: 8px; border: 1px solid blue; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; }
    .result-container { display: flex; justify-content: space-between; gap: 8px; margin: 20px 0 5px 0; flex-wrap: wrap; }
    .result-card { background: white; padding: 10px; border-radius: 10px; text-align: center; flex: 1; min-width: 100px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #f0f0f0; }
    .card-label { font-size: 0.7rem; color: #666; font-weight: 800; text-transform: uppercase; display: block; }
    .card-value { font-size: 0.95rem; color: #1a1a1a; font-weight: 800; display: block; margin-top: 3px; }

    /* PDF Button Design - Rot und Mobil-optimiert */
    div.stDownloadButton { display: flex; justify-content: center; width: 100%; margin-top: 20px; margin-bottom: 50px; }
    div.stDownloadButton > button { 
        width: 100% !important; 
        background-color: #ff4b4b !important; 
        color: white !important; 
        padding: 18px !important; 
        font-weight: bold !important; 
        border-radius: 12px !important; 
        border: none !important; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important; 
    }
    </style>
    <div class="main-header">
        <h2>Finanz-Check</h2>
        <p>Alex Heide</p>
    </div>
    """, unsafe_allow_html=True)

# 4. Eingabebereich
with st.expander("📝 Eingabedaten anpassen", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        preis = st.number_input("Kaufpreis (€)", value=350000, step=5000)
        ek = st.number_input("Eigenkapital (€)", value=70000, step=5000)
        grunderwerb_p = st.number_input("Grunderwerbsteuer (%)", value=3.5, step=0.1)
        notar_p = st.number_input("Notar & Grundbuch (%)", value=2.0, step=0.1)
    with col_b:
        zins = st.number_input("Sollzins p.a. (%)", value=3.8, step=0.1, format="%.2f")
        sonti_p = st.number_input("Sondertilgung p.a. (%)", value=1.0, step=0.5)
        makler_aktiv = st.checkbox("Makler beteiligt", value=True)
        makler_p = st.number_input("Maklerprovision (%)", value=3.57, step=0.01, disabled=not makler_aktiv)

    m_kosten = preis * (makler_p / 100) if makler_aktiv else 0
    g_kosten = preis * (grunderwerb_p / 100)
    n_kosten = preis * (notar_p / 100)
    nebenkosten_gesamt = m_kosten + g_kosten + n_kosten
    gesamtkosten = preis + nebenkosten_gesamt
    rechnerischer_bedarf = gesamtkosten - ek

    # Kostenliste HTML
    html_liste = f'<div class="flex-row"><span>Kaufpreis:</span><span>{format_de(preis)}</span></div>'
    html_liste += f'<div class="flex-row"><span>Grunderwerbsteuer ({grunderwerb_p}%):</span><span>{format_de(g_kosten)}</span></div>'
    html_liste += f'<div class="flex-row"><span>Notar & Grundbuch ({notar_p}%):</span><span>{format_de(n_kosten)}</span></div>'
    if makler_aktiv:
        html_liste += f'<div class="flex-row"><span>Maklerprovision ({makler_p}%):</span><span>{format_de(m_kosten)}</span></div>'
    html_liste += f'<div class="flex-row" style="font-style: italic; color: #555;"><span>Nebenkosten gesamt:</span><span>{format_de(nebenkosten_gesamt)}</span></div>'
    html_liste += f'<div class="flex-row"><span>Eigenkapital:</span><span>- {format_de(ek)}</span></div>'
    html_liste += f'<div class="flex-row total-row"><span>GESAMTBEDARF:</span><span>{format_de(gesamtkosten)}</span></div>'
    html_liste += f'<div class="flex-row" style="color: blue; font-weight: bold;"><span>DARLEHENSBEDARF:</span><span>{format_de(rechnerischer_bedarf)}</span></div>'

    st.markdown(f'<div class="kosten-liste">{html_liste}</div>', unsafe_allow_html=True)

    darlehen = st.number_input("Tatsächliche Darlehenssumme (€)", value=float(round(rechnerischer_bedarf, -2)),
                               step=1000.0)
    t_art = st.radio("Tilgungswahl:", ["in % p.a.", "in € monatlich"], horizontal=True)
    t_val = st.number_input("Tilgungswert", value=2.0 if "%" in t_art else 500.0)

    # MONATLICHE RATE BERECHNUNG
    z_dez_calc = zins / 100
    if "in % p.a." in t_art:
        rate_m_anzeige = (darlehen * (z_dez_calc + (t_val / 100)) / 12)
    else:
        rate_m_anzeige = (darlehen * (z_dez_calc / 12) + t_val)

    # RATE SICHTBAR MACHEN
    st.markdown(f"""
        <div style="margin-top: 10px; padding: 15px; border-radius: 10px; background-color: #e3f2fd; border: 2px solid blue; text-align: center;">
            <span style="font-size: 0.85rem; color: #555; font-weight: bold; text-transform: uppercase;">Monatliche Rate:</span><br>
            <span style="font-size: 1.4rem; color: blue; font-weight: 900;">{format_de(rate_m_anzeige)}</span>
        </div>
    """, unsafe_allow_html=True)

# 5. Berechnung
if darlehen > 0:
    z_dez = zins / 100
    rate_m = rate_m_anzeige
    plan_m, plan_j = [], []
    rest, m, gz = darlehen, 1, 0
    s_euro = darlehen * (sonti_p / 100)
    j_zins, j_tilg, j_rate = 0, 0, 0

    while rest > 0.01 and m <= 600:
        zm = rest * (z_dez / 12)
        tm = min(rest, rate_m - zm)
        sj = min(rest - tm, s_euro) if m % 12 == 0 and (rest - tm) > 0 else 0
        cur_tilg = tm + sj
        rest -= cur_tilg
        gz += zm
        j_zins += zm
        j_tilg += cur_tilg
        j_rate += rate_m

        plan_m.append({"Monat": m, "Rate": rate_m, "Zins": zm, "Tilgung": tm, "Gesamt_Tilgung": cur_tilg,
                       "Restschuld": max(0, rest)})
        if m % 12 == 0 or rest <= 0.01:
            plan_j.append({"Jahr": (m // 12 if m % 12 == 0 else m // 12 + 1), "Rate (Jahr)": j_rate, "Zins": j_zins,
                           "Tilgung": j_tilg,
                           "Restschuld": max(0, rest)})
            j_zins, j_tilg, j_rate = 0, 0, 0
        if rest <= 0.01: break
        m += 1

    st.markdown('<div class="view-toggle-box">', unsafe_allow_html=True)
    view_m = st.toggle("🔍 Monatsansicht aktivieren (Grafik & Tabelle)", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    fig, ax1 = plt.subplots(figsize=(8, 4))
    df_plot = pd.DataFrame(plan_m) if view_m else pd.DataFrame(plan_j)
    x_label = "Monat" if view_m else "Jahr"

    ax1.plot(df_plot[x_label], df_plot["Restschuld"], color="blue", linewidth=2, label="Restschuld")
    ax1.set_ylabel("Restschuld (€)", color="blue", fontweight='bold')
    ax2 = ax1.twinx()
    ax2.plot(df_plot[x_label], df_plot["Zins"], color="red", linestyle="--", alpha=0.6, label="Zins")
    ax2.plot(df_plot[x_label], df_plot["Tilgung"], color="green", linestyle="-.", alpha=0.6, label="Tilgung")
    ax1.legend(loc='upper right')
    st.pyplot(fig)

    with st.expander("📊 Tabelle anzeigen", expanded=False):
        tab_df = df_plot.copy()
        if "Gesamt_Tilgung" in tab_df.columns:
            tab_df["Tilgung"] = tab_df["Gesamt_Tilgung"]
            tab_df = tab_df.drop(columns=["Gesamt_Tilgung"])
        st.dataframe(tab_df.map(lambda x: format_de(x) if isinstance(x, (int, float)) and x > 50 else x),
                     use_container_width=True, hide_index=True)

    lz_t = f"{m // 12} J. {m % 12} M."
    st.markdown(f"""
    <div class="result-container">
        <div class="result-card"><span class="card-label">ZINSEN</span><span class="card-value">{format_de(gz)}</span></div>
        <div class="result-card"><span class="card-label">GESAMT</span><span class="card-value">{format_de(gz + darlehen)}</span></div>
        <div class="result-card"><span class="card-label">LAUFZEIT</span><span class="card-value">{lz_t}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # PDF EXPORT FIX & BUTTON BEZEICHNUNG
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Finanz-Check Ergebnis", ln=True, align='C')

    pdf_output = pdf.output(dest='S')
    st.download_button(label="📥 PDF-Export", data=bytes(pdf_output), file_name="Finanz-Check.pdf")
