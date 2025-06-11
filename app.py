
import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Sistema de Pedidos - Ingatuo", layout="wide")
st.image("https://www.ingauto.com.ec/wp-content/uploads/2019/06/logo-Ingauto-T.png", width=300)
st.title("🛠️ Sistema de Pedidos - Ingatuo Loja")

@st.cache_data
def cargar_productos():
    return pd.read_excel("precios_ingatuo_definitivo.xlsx")

productos_df = cargar_productos()
if "carrito" not in st.session_state:
    st.session_state.carrito = []

st.subheader("🧍 Información del Cliente")
with st.form("formulario_cliente"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre completo *")
        cedula = st.text_input("Cédula *")
    with col2:
        telefono = st.text_input("Teléfono / WhatsApp *")
        correo = st.text_input("Correo electrónico *")
    comentario = st.text_area("Comentario adicional")
    enviar = st.form_submit_button("✅ Confirmar Pedido")

st.subheader("🛒 Selección de Productos")
producto_sel = st.selectbox("Selecciona un producto", productos_df["Producto"])
cantidad = st.number_input("Cantidad", min_value=1, step=1)

if st.button("➕ Agregar al carrito"):
    prod = productos_df[productos_df["Producto"] == producto_sel].iloc[0]
    if cantidad >= 12:
        precio_unitario = prod["PrecioX12"]
    elif cantidad >= 6:
        precio_unitario = prod["PrecioX6"]
    elif cantidad >= 3:
        precio_unitario = prod["PrecioX3"]
    else:
        precio_unitario = prod["PrecioBase"]

    st.session_state.carrito.append({
        "Producto": prod["Producto"],
        "Descripcion": prod["Descripcion"],
        "Cantidad": cantidad,
        "PrecioUnitario": precio_unitario,
        "Subtotal": round(precio_unitario * cantidad, 2)
    })

# Mostrar carrito
if st.session_state.carrito:
    st.subheader("📦 Resumen del Pedido")
    total = 0
    for i, item in enumerate(st.session_state.carrito):
        cols = st.columns([5, 2, 2, 2, 1])
        cols[0].write(f"🔹 {item['Producto']}")
        cols[1].write(f"{item['Cantidad']} und")
        cols[2].write(f"${item['PrecioUnitario']:.2f}")
        cols[3].write(f"${item['Subtotal']:.2f}")
        total += item["Subtotal"]
        if cols[4].button("❌", key=f"del_{i}"):
            st.session_state.carrito.pop(i)
            st.experimental_rerun()

    st.markdown(f"### 💰 Total: ${total:.2f}")

    if enviar:
        if not (nombre and cedula and telefono and correo):
            st.error("⚠️ Completa todos los campos obligatorios.")
        else:
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            archivo_pdf = f"pedido_{cedula}.pdf"

            # Crear PDF
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
            pdf.cell(60, 10, "Producto", 1)
            pdf.cell(30, 10, "Cant", 1)
            pdf.cell(40, 10, "Precio", 1)
            pdf.cell(40, 10, "Subtotal", 1)
            pdf.ln()
            pdf.set_font("Arial", "", 12)
            for item in st.session_state.carrito:
                pdf.cell(60, 10, item["Producto"][:30], 1)
                pdf.cell(30, 10, str(item["Cantidad"]), 1)
                pdf.cell(40, 10, f"${item['PrecioUnitario']:.2f}", 1)
                pdf.cell(40, 10, f"${item['Subtotal']:.2f}", 1)
                pdf.ln()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(130, 10, "TOTAL", 1)
            pdf.cell(40, 10, f"${total:.2f}", 1)
            pdf.output(archivo_pdf)

            # Enviar por correo
            msg = EmailMessage()
            msg["Subject"] = "Nuevo Pedido - Ingatuo Loja"
            msg["From"] = "accesoriossd@ingauto.com.ec"
            msg["To"] = correo
            msg["Cc"] = "accesoriossd@ingauto.com.ec"
            msg.set_content(f"""Hola {nombre},

Adjunto encontrarás el PDF de tu pedido realizado.

Gracias por confiar en Ingatuo Loja.
""")
            with open(archivo_pdf, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=archivo_pdf)
            with smtplib.SMTP_SSL("mail.ingauto.com.ec", 465) as smtp:
                smtp.login("accesoriossd@ingauto.com.ec", "Joseph2002*jm")
                smtp.send_message(msg)

            with open(archivo_pdf, "rb") as f:
                st.download_button("📄 Descargar PDF del Pedido", f, file_name=archivo_pdf)
            st.success("✅ Pedido enviado correctamente y registrado.")
