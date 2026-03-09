import streamlit as st
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
import io

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
    .view-toggle-box { background-color: #e8f0fe; padding: 10px; border-radius: 8px; border: 1px solid blue; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; }
    .result-container { display: flex; justify-content: space-between; gap: 8px; margin: 20px 0 5px 0; flex-wrap: wrap; }
    .result-card { background: white; padding: 10px; border-radius: 10px; text-align: center; flex: 1; min-width: 100px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #f0f0f0; }
    .card-label { font-size: 0.65rem; color: #666; font-weight: 600; text-transform: uppercase; display: block; }
    .card-value { font-size: 0.95rem; color: #1a1a1a; font-weight: 800; display: block; margin-top: 3px; }

    /* PDF Button - Volle Breite für Smartphone */
    div.stDownloadButton { display: flex; justify-content: center; width: 100%; margin-top: 15px; margin-bottom: 40px; }
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

# 4. Eingaben
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
        makler_aktiv = st.checkbox("Makler involviert", value=True)
        makler_p = st.number_input("Maklerprovision (%)", value=3.57, step=0.01, disabled=not makler_aktiv)

    m_kosten = preis * (makler_p / 100) if makler_aktiv else 0
    g_kosten = preis * (grunderwerb_p / 100)
    n_kosten = preis * (notar_p / 100)
    nebenkosten_gesamt = m_kosten + g_kosten + n_kosten
    gesamtkosten = preis + nebenkosten_gesamt
    rechnerischer_bedarf = gesamtkosten - ek

    st.markdown(f"""
    <div class="kosten-liste">
        <div class="flex-row"><span>Kaufpreis:</span><span>{format_de(preis)}</span></div>
        <div class="flex-row"><span>Nebenkosten:</span><span>{format_de(nebenkosten_gesamt)}</span></div>
        <div class="flex-row"><span>Eigenkapital:</span><span>- {format_de(ek)}</span></div>
        <div class="flex-row total-row"><span>GESAMTBEDARF:</span><span>{format_de(gesamtkosten)}</span></div>
        <div class="flex-row" style="color: blue; font-weight: bold;"><span>DARLEHENSBEDARF:</span><span>{format_de(rechnerischer_bedarf)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    darlehen = st.number_input("Tatsächliche Darlehenssumme (€)", value=float(round(rechnerischer_bedarf, -2)),
                               step=1000.0)
    t_art = st.radio("Tilgungswahl:", ["in % p.a.", "in € monatlich"], horizontal=True)
    t_val = st.number_input("Tilgungswert", value=2.0 if "%" in t_art else 500.0)

# 5. Berechnung
if darlehen > 0:
    z_dez = zins / 100
    rate_m = (darlehen * (z_dez + (t_val / 100)) / 12) if "in % p.a." in t_art else (darlehen * (z_dez / 12) + t_val)
    plan_m, plan_j = [], []
    rest, m, gz = darlehen, 1, 0
    s_euro = darlehen * (sonti_p / 100)
    j_zins, j_tilg = 0, 0

    while rest > 0.01 and m <= 600:
        zm = rest * (z_dez / 12)
        tm = min(rest, rate_m - zm)
        sj = min(rest - tm, s_euro) if m % 12 == 0 and (rest - tm) > 0 else 0
        cur_tilg = tm + sj
        rest -= cur_tilg
        gz += zm
        j_zins += zm
        j_tilg += cur_tilg
        plan_m.append({"Monat": m, "Zins": zm, "Tilgung": cur_tilg, "Restschuld": max(0, rest)})
        if m % 12 == 0 or rest <= 0.01:
            plan_j.append({"Jahr": (m // 12 if m % 12 == 0 else m // 12 + 1), "Zins": j_zins, "Tilgung": j_tilg,
                           "Restschuld": max(0, rest)})
            j_zins, j_tilg = 0, 0
        if rest <= 0.01: break
        m += 1

    # Graph
    fig, ax1 = plt.subplots(figsize=(8, 4))
    df_p = pd.DataFrame(plan_j)
    ax1.plot(df_p["Jahr"], df_p["Restschuld"], color="blue", label="Restschuld")
    ax1.set_ylabel("Restschuld (€)", color="blue")
    ax1.set_xlabel("Laufzeit in Jahren", fontweight='bold')
    ax2 = ax1.twinx()
    ax2.plot(df_p["Jahr"], df_p["Zins"], color="red", linestyle="--", label="Zins")
    ax2.plot(df_p["Jahr"], df_p["Tilgung"], color="green", linestyle="-.", label="Tilgung")
    ax2.set_ylabel("Zins / Tilgung (€)")
    ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.28), ncol=3, frameon=False)
    st.pyplot(fig)

    # 6. Ergebnisse anzeigen
    lz_t = f"{m // 12} J. {m % 12} M."
    st.markdown(f"""
    <div class="result-container">
        <div class="result-card"><span class="card-label">Ges. Zinsen</span><span class="card-value">{format_de(gz)}</span></div>
        <div class="result-card"><span class="card-label">Gesamtkosten</span><span class="card-value">{format_de(darlehen + gz)}</span></div>
        <div class="result-card"><span class="card-label">Laufzeit</span><span class="card-value">{lz_t}</span></div>
    </div>
    """, unsafe_allow_html=True)


    # 7. PDF Logik (Fix: kein .encode() auf bytearray)
    def generate_pdf_bytes(data_list, d_sum, z_g, lz_text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Finanz-Check AH - Ergebnis", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"Darlehenssumme: {format_de(d_sum).replace('€', 'EUR')}", ln=True)
        pdf.cell(0, 10, f"Gesamtzinsen: {format_de(z_g).replace('€', 'EUR')}", ln=True)
        pdf.cell(0, 10, f"Laufzeit: {lz_text}", ln=True)
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 10, "Jahr", border=1)
        pdf.cell(45, 10, "Zins (EUR)", border=1)
        pdf.cell(45, 10, "Tilgung (EUR)", border=1)
        pdf.cell(45, 10, "Restschuld (EUR)", border=1, ln=True)

        pdf.set_font("Helvetica", "", 10)
        for row in data_list[:120]:
            pdf.cell(30, 8, str(row.get("Jahr", row.get("Monat"))), border=1)
            pdf.cell(45, 8, format_de(row["Zins"]).replace('€', ''), border=1)
            pdf.cell(45, 8, format_de(row["Tilgung"]).replace('€', ''), border=1)
            pdf.cell(45, 8, format_de(row["Restschuld"]).replace('€', ''), border=1, ln=True)

        # In neueren fpdf-Versionen ist die Ausgabe direkt binär (bytearray)
        return pdf.output()


    # 8. Download & Ballons
    try:
        final_pdf = generate_pdf_bytes(plan_j, darlehen, gz, lz_t)

        if st.download_button(
                label="📄 Als PDF speichern",
                data=bytes(final_pdf),  # Konvertiert bytearray sicher in bytes
                file_name="Finanzcheck_AH.pdf",
                mime="application/pdf"
        ):
            st.balloons()
    except Exception as e:
        st.error(f"Fehler bei der PDF-Erstellung: {e}")
