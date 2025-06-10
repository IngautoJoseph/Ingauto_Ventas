
import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime
import os

# Configuración inicial
st.set_page_config(page_title="Pedidos Ingatuo", layout="centered")
st.image("https://www.ingauto.com.ec/wp-content/uploads/2019/06/logo-Ingauto-T.png", width=250)
st.title("📦 Registro de Pedidos - Ingatuo Loja")

# Cargar precios
@st.cache_data
def cargar_productos():
    return pd.read_excel("precios_ingatuo.xlsx")

productos_df = cargar_productos()

# Seleccionar productos y cantidades
st.subheader("📝 Formulario de Pedido")
with st.form("pedido_form"):
    nombre = st.text_input("Nombre del cliente *")
    cedula = st.text_input("Cédula *")
    telefono = st.text_input("Teléfono / WhatsApp *")
    correo = st.text_input("Correo electrónico *")

    seleccion = []
    for i, row in productos_df.iterrows():
        cantidad = st.number_input(f"{row['Producto']} - ${row['Precio']} (Cantidad)", min_value=0, max_value=100, step=1, key=f"prod_{i}")
        if cantidad > 0:
            seleccion.append({
                "Producto": row["Producto"],
                "Descripción": row["Descripción"],
                "Precio": row["Precio"],
                "Cantidad": cantidad,
                "Subtotal": cantidad * row["Precio"]
            })

    comentario = st.text_area("Comentario adicional")
    enviar = st.form_submit_button("✅ Enviar Pedido")

# Guardar en Excel y generar PDF
if enviar:
    if not (nombre and cedula and telefono and correo and seleccion):
        st.error("Por favor completa todos los campos obligatorios y selecciona al menos un producto.")
    else:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = sum(item["Subtotal"] for item in seleccion)

        pedido_data = {
            "Fecha": fecha, "Nombre": nombre, "Cédula": cedula, "Teléfono": telefono, "Correo": correo,
            "Comentario": comentario, "Total": total, "Productos": seleccion
        }

        # Guardar en Excel
        archivo_excel = "pedidos_ingatuo.xlsx"
        if Path(archivo_excel).exists():
            df_antiguo = pd.read_excel(archivo_excel)
        else:
            df_antiguo = pd.DataFrame()
        fila = pd.DataFrame([{
            "Fecha": fecha, "Nombre": nombre, "Cédula": cedula, "Teléfono": telefono,
            "Correo": correo, "Comentario": comentario, "Total": total
        }])
        df_nuevo = pd.concat([df_antiguo, fila], ignore_index=True)
        df_nuevo.to_excel(archivo_excel, index=False)

        # Generar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.image("https://www.ingauto.com.ec/wp-content/uploads/2019/06/logo-Ingauto-T.png", x=70, y=10, w=70)
        pdf.set_font("Arial", "B", 14)
        pdf.ln(35)
        pdf.cell(0, 10, f"PEDIDO - {nombre}", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Cédula: {cedula} | Tel: {telefono} | Correo: {correo}", ln=True)
        pdf.cell(0, 10, f"Fecha: {fecha}", ln=True)
        pdf.cell(0, 10, f"Comentario: {comentario}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 10, "Producto", 1)
        pdf.cell(80, 10, "Descripción", 1)
        pdf.cell(30, 10, "Cantidad", 1)
        pdf.cell(40, 10, "Subtotal", 1)
        pdf.ln()
        pdf.set_font("Arial", "", 12)
        for item in seleccion:
            pdf.cell(40, 10, item["Producto"], 1)
            pdf.cell(80, 10, item["Descripción"][:40], 1)
            pdf.cell(30, 10, str(item["Cantidad"]), 1)
            pdf.cell(40, 10, f"${item['Subtotal']:.2f}", 1)
            pdf.ln()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(150, 10, "Total", 1)
        pdf.cell(40, 10, f"${total:.2f}", 1)
        pdf_file = f"pedido_{cedula}.pdf"
        pdf.output(pdf_file)

        # Enviar correo
        msg = EmailMessage()
        msg["Subject"] = "Nuevo Pedido - Ingatuo Loja"
        msg["From"] = "accesoriossd@ingauto.com.ec"
        msg["To"] = correo
        msg["Cc"] = "accesoriossd@ingauto.com.ec"
        msg.set_content(f"Hola {nombre},

Adjunto encontrarás el PDF de tu pedido realizado.

Gracias por confiar en Ingatuo Loja.")
        with open(pdf_file, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=pdf_file)
        with smtplib.SMTP_SSL("smtp.zoho.com", 465) as smtp:
            smtp.login("accesoriossd@ingauto.com.ec", "51TBdC375q")
            smtp.send_message(msg)

        with open(pdf_file, "rb") as f:
            st.download_button("📄 Descargar PDF del Pedido", f, file_name=pdf_file)
        st.success("✅ Pedido enviado y registrado correctamente.")
