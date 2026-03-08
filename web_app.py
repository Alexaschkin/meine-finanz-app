import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

# Mobile Optimierung
st.set_page_config(page_title="Finanz-Check AH", layout="centered")


# Hilfsfunktion für deutsches Zahlenformat
def format_de(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


# CSS für Styling
st.markdown("""
    <style>
    .main-header { background-color: blue; padding: 10px; border-radius: 8px; text-align: center; color: white; margin-bottom: 15px; }
    .main-header h2 { margin: 0; font-size: 20px; }
    .main-header p { margin: 0; font-size: 14px; font-style: italic; }
    .kosten-liste { background-color: #f0f2f6; padding: 12px; border-radius: 10px; font-size: 0.85rem; font-weight: bold; line-height: 1.4; }
    .flex-row { display: flex; justify-content: space-between; border-bottom: 1px solid #ddd; padding: 2px 0; }
    .total-row { border-top: 2px solid #333; margin-top: 5px; padding-top: 5px; font-size: 0.95rem; }
    </style>
    <div class="main-header">
        <h2>Finanz-Check</h2>
        <p>Alex Heide</p>
    </div>
    """, unsafe_allow_html=True)

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
        makler_an = st.checkbox("Makler (3,57%)", value=True)

    m_kosten = preis * 0.0357 if makler_an else 0
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
        <div class="flex-row"><span>Maklergebühr (3,57%):</span><span>{format_de(m_kosten)}</span></div>
        <div class="flex-row"><span>Eigenkapital:</span><span>- {format_de(ek)}</span></div>
        <div class="flex-row total-row"><span>GESAMTBEDARF:</span><span>{format_de(gesamtkosten)}</span></div>
        <div class="flex-row" style="color: blue;"><span>DARLEHENSBEDARF:</span><span>{format_de(rechnerischer_bedarf)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    darlehen = st.number_input("Tatsächliche Darlehenssumme zur Berechnung (€)",
                               value=float(round(rechnerischer_bedarf, -2)),
                               step=1000.0)

    st.markdown("---")
    t_art = st.radio("Tilgungswahl:", ["in % p.a.", "in € monatlich"], horizontal=True)
    label_tilg = "Anfängliche Tilgung (%)" if "%" in t_art else "Zusatztilgung (€/Monat)"
    t_val = st.number_input(label_tilg, value=2.0 if "%" in t_art else 500.0, step=0.1 if "%" in t_art else 50.0)

if darlehen > 0:
    z_dez = zins / 100
    rate_m = (darlehen * (z_dez + (t_val / 100)) / 12) if "in % p.a." in t_art else (darlehen * (z_dez / 12) + t_val)

    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Gewähltes Darlehen", format_de(darlehen))
    m2.metric("Monatliche Rate", format_de(rate_m))

    view_m = st.toggle("Detaillierte Monatsansicht", value=False)

    plan = []
    rest = darlehen
    m = 1
    gz = 0
    s_euro = darlehen * (sonti_p / 100)
    jahr_zins_akk, jahr_tilg_akk = 0, 0

    while rest > 0.1 and m <= 600:
        zm = rest * (z_dez / 12)
        tm = min(rest, rate_m - zm)
        sj = min(rest - tm, s_euro) if m % 12 == 0 and rest > s_euro else 0
        rest -= (tm + sj)
        gz += zm
        jahr_zins_akk += zm
        jahr_tilg_akk += (tm + sj)

        if view_m:
            plan.append({"Monat": m, "Zins": zm, "Tilgung": (tm + sj), "Restschuld": max(0.0, rest)})

        if m % 12 == 0 or rest <= 0.1:
            if not view_m:
                jahr = int(m / 12 if m % 12 == 0 else m // 12 + 1)
                plan.append(
                    {"Jahr": jahr, "Zins": jahr_zins_akk, "Tilgung": jahr_tilg_akk, "Restschuld": max(0.0, rest)})
            jahr_zins_akk, jahr_tilg_akk = 0, 0
        m += 1

    df = pd.DataFrame(plan)

    # Grafik
    fig, ax = plt.subplots(figsize=(8, 3))
    x_axis = "Monat" if view_m else "Jahr"
    ax.plot(df[x_axis], df["Restschuld"], color="blue", linewidth=2)
    ax.set_ylabel("Restbetrag (€)")
    ax.grid(True, linestyle="--", alpha=0.6)
    st.pyplot(fig)

    # Tabelle formatieren
    df_display = df.copy()
    for col in ["Zins", "Tilgung", "Restschuld"]:
        df_display[col] = df_display[col].apply(format_de)

    st.dataframe(df_display, use_container_width=True, hide_index=True)
    st.success(f"**Zinsen gesamt:** {format_de(gz)} | **Gesamtkosten:** {format_de(darlehen + gz)}")


    # --- PDF LOGIK ---
    def generate_pdf(data, d_sum, r_m, z_g):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Finanzierungsprognose - Alex Heide", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"Darlehenssumme: {format_de(d_sum).replace('€', 'EUR')}", ln=True)
        pdf.cell(0, 10, f"Monatliche Rate: {format_de(r_m).replace('€', 'EUR')}", ln=True)
        pdf.cell(0, 10, f"Gesamtzinsen: {format_de(z_g).replace('€', 'EUR')}", ln=True)
        pdf.ln(5)

        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(25, 10, "Zeit", border=1, fill=True)
        pdf.cell(50, 10, "Zins (EUR)", border=1, fill=True)
        pdf.cell(50, 10, "Tilgung (EUR)", border=1, fill=True)
        pdf.cell(50, 10, "Restschuld (EUR)", border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 10)
        for _, row in data.iterrows():
            pdf.cell(25, 8, str(row[x_axis]), border=1)
            pdf.cell(50, 8, row["Zins"].replace('€', '').strip(), border=1)
            pdf.cell(50, 8, row["Tilgung"].replace('€', '').strip(), border=1)
            pdf.cell(50, 8, row["Restschuld"].replace('€', '').strip(), border=1)
            pdf.ln()

        return pdf.output()


    # Download Button
    pdf_bytes = generate_pdf(df_display, darlehen, rate_m, gz)
    st.download_button(
        label="📄 Ergebnis als PDF speichern",
        data=bytes(pdf_bytes),  # Wichtig für Online-Server
        file_name="Finanzcheck_Ergebnis.pdf",
        mime="application/pdf"
    )

else:
    st.warning("Kein Darlehen erforderlich.")
