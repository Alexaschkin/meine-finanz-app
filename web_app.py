import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

# Mobile Optimierung & Layout
st.set_page_config(page_title="Finanz-Check AH", layout="centered")


# Hilfsfunktion für deutsches Zahlenformat
def format_de(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


# CSS für Styling inkl. exakter Button-Zentrierung
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

    div.stDownloadButton > button {
        background-color: #ff4b4b !important; 
        color: white !important; 
        border-radius: 8px !important;
        padding: 10px 15px !important; 
        font-size: 14px !important; 
        font-weight: bold !important;
        border: none !important; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    }
    </style>
    <div class="main-header">
        <h2>Finanz-Check</h2>
        <p>Alex Heide</p>
    </div>
    """, unsafe_allow_html=True)

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
        <div class="flex-row"><span>Grunderwerbsteuer ({grunderwerb_p}%):</span><span>{format_de(g_kosten)}</span></div>
        <div class="flex-row"><span>Notar & Grundbuch ({notar_p}%):</span><span>{format_de(n_kosten)}</span></div>
        <div class="flex-row"><span>Maklergebühr ({makler_p if makler_aktiv else 0}%):</span><span>{format_de(m_kosten)}</span></div>
        <div class="flex-row"><span>Eigenkapital:</span><span>- {format_de(ek)}</span></div>
        <div class="flex-row total-row"><span>GESAMTBEDARF:</span><span>{format_de(gesamtkosten)}</span></div>
        <div class="flex-row" style="color: blue; font-weight: bold;"><span>DARLEHENSBEDARF:</span><span>{format_de(rechnerischer_bedarf)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    darlehen = st.number_input("Tatsächliche Darlehenssumme (€)", value=float(round(rechnerischer_bedarf, -2)),
                               step=1000.0)
    t_art = st.radio("Tilgungswahl:", ["in % p.a.", "in € monatlich"], horizontal=True)
    t_val = st.number_input("Tilgungswert", value=2.0 if "%" in t_art else 500.0)

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

    st.markdown('<div class="view-toggle-box">', unsafe_allow_html=True)
    view_m = st.toggle("🔍 Monatsansicht aktivieren", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    current_df = pd.DataFrame(plan_m) if view_m else pd.DataFrame(plan_j)
    x_ax_label = "Monat" if view_m else "Jahr"

    fig, ax1 = plt.subplots(figsize=(8, 4))
    l1, = ax1.plot(current_df[x_ax_label], current_df["Restschuld"], color="blue", label="Restschuld")
    ax1.set_ylabel("Restschuld (€)", color="blue")
    ax1.set_xlabel("Laufzeit in Jahren" if not view_m else "Laufzeit in Monaten", fontsize=10, fontweight='bold')

    ax2 = ax1.twinx()
    l2, = ax2.plot(current_df[x_ax_label], current_df["Zins"], color="red", linestyle="--", label="Zins")

    if view_m and s_euro > 0:
        reg_tilg = current_df["Tilgung"].copy()
        for i in range(len(reg_tilg)):
            if (i + 1) % 12 == 0: reg_tilg.iloc[i] -= s_euro
        l3, = ax2.plot(current_df[x_ax_label], reg_tilg, color="green", linestyle="-.", label="Tilgung")
    else:
        l3, = ax2.plot(current_df[x_ax_label], current_df["Tilgung"], color="green", linestyle="-.", label="Tilgung")

    ax2.set_ylabel("Zins / Tilgung (€)")
    ax1.legend(handles=[l1, l2, l3], loc='upper center', bbox_to_anchor=(0.5, -0.28), ncol=3, frameon=False)
    st.pyplot(fig)

    with st.expander("📊 Tabelle anzeigen", expanded=False):
        st.dataframe(current_df.map(lambda x: format_de(x) if isinstance(x, (int, float)) and x > 50 else x),
                     use_container_width=True, hide_index=True)

    lz_t = f"{m // 12} J. {m % 12} M."
    st.markdown(f"""
    <div class="result-container">
        <div class="result-card"><span class="card-label">Ges. Zinsen</span><span class="card-value">{format_de(gz)}</span></div>
        <div class="result-card"><span class="card-label">Gesamtkosten</span><span class="card-value">{format_de(darlehen + gz)}</span></div>
        <div class="result-card"><span class="card-label">Laufzeit in Jahren</span><span class="card-value">{lz_t}</span></div>
    </div>
    """, unsafe_allow_html=True)


    # --- PDF LOGIK MIT TEMPORÄRER DATEI (SICHERSTE METHODE) ---
    def generate_pdf_final(df_data, d_sum, z_g, lz_text, x_label, figure):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 15, "Finanzprognose", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Darlehenssumme: {format_de(d_sum).replace('€', 'EUR')}", ln=True)
        pdf.cell(0, 8, f"Gesamtzinsen: {format_de(z_g).replace('€', 'EUR')}", ln=True)
        pdf.cell(0, 8, f"Laufzeit: {lz_text}", ln=True)
        pdf.ln(5)

        # Diagramm als echte Datei speichern
        tmp_img_path = os.path.join(tempfile.gettempdir(), "plot.png")
        figure.savefig(tmp_img_path, format="png", bbox_inches='tight', dpi=120)

        # Bild in PDF laden
        pdf.image(tmp_img_path, x=15, w=180)
        pdf.ln(5)

        # Tabelle
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(25, 10, x_label, border=1, fill=True)
        pdf.cell(50, 10, "Zins (EUR)", border=1, fill=True)
        pdf.cell(50, 10, "Tilgung (EUR)", border=1, fill=True)
        pdf.cell(50, 10, "Restschuld (EUR)", border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for _, row in df_data.iterrows():
            if pdf.get_y() > 265: pdf.add_page()
            pdf.cell(25, 7, str(int(row[x_label])), border=1)
            pdf.cell(50, 7, format_de(row["Zins"]).replace('€', '').strip(), border=1)
            pdf.cell(50, 7, format_de(row["Tilgung"]).replace('€', '').strip(), border=1)
            pdf.cell(50, 7, format_de(row["Restschuld"]).replace('€', '').strip(), border=1)
            pdf.ln()

        pdf_out = bytes(pdf.output())

        # Temp Datei löschen
        if os.path.exists(tmp_img_path):
            os.remove(tmp_img_path)

        return pdf_out


    # PDF Erzeugung versuchen
    try:
        pdf_data = generate_pdf_final(current_df, darlehen, gz, lz_t, x_ax_label, fig)

        # Download-Button in zentrierter Spalte
        col1, col2, col3 = st.columns(3)
        with col2:
            st.download_button(
                label="📄 PDF speichern?",
                data=pdf_data,
                file_name="Finanzprognose.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Fehler bei der PDF-Erstellung: {e}")

else:
    st.warning("Kein Darlehen erforderlich.")
