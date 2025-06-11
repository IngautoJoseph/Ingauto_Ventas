
import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Sistema de Pedidos - Ingatuo", layout="wide")
st.image("https://www.ingauto.com.ec/wp-content/uploads/2019/06/logo-Ingauto-T.png", width=300)
st.title("🛠️ Sistema de Pedidos Profesionales - Ingatuo Loja")

@st.cache_data
def cargar_productos():
    return pd.read_excel("precios_ingatuo_limpio_final.xlsx")

productos_df = cargar_productos()

st.subheader("🧍 Información del Cliente")
with st.form("datos_cliente"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre completo *")
        cedula = st.text_input("Cédula *")
    with col2:
        telefono = st.text_input("Teléfono / WhatsApp *")
        correo = st.text_input("Correo electrónico *")
    comentario = st.text_area("Comentario adicional")
    enviado = st.form_submit_button("✅ Confirmar Datos")

# Inicializar estado de carrito
if "carrito" not in st.session_state:
    st.session_state.carrito = []

st.subheader("🛒 Catálogo de Productos")
with st.expander("Seleccionar productos por categoría"):
    categorias = productos_df["Producto"].apply(lambda x: x.split()[0]).unique()
    categoria_sel = st.selectbox("Elige una categoría:", sorted(categorias))
    filtrado = productos_df[productos_df["Producto"].str.startswith(categoria_sel)]
    producto_sel = st.selectbox("Producto:", filtrado["Producto"].values)
    cantidad_sel = st.number_input("Cantidad:", min_value=1, max_value=100, step=1)
    if st.button("➕ Agregar al pedido"):
        prod = productos_df[productos_df["Producto"] == producto_sel].iloc[0]
        st.session_state.carrito.append({
            "Producto": prod["Producto"],
            "Descripcion": prod["Descripcion"],
            "Precio": prod["Precio"],
            "Cantidad": cantidad_sel,
            "Subtotal": round(prod["Precio"] * cantidad_sel, 2)
        })

# Mostrar tabla del pedido con posibilidad de editar/eliminar
if st.session_state.carrito:
    st.subheader("📦 Resumen del Pedido")
    df_carrito = pd.DataFrame(st.session_state.carrito)
    total = df_carrito["Subtotal"].sum()
    st.dataframe(df_carrito[["Producto", "Cantidad", "Precio", "Subtotal"]], use_container_width=True)
    st.markdown(f"### 💰 Total: ${total:.2f}")

    if st.button("🗑️ Borrar todo el pedido"):
        st.session_state.carrito = []

    if enviado and nombre and cedula and telefono and correo and total > 0:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        archivo_pdf = f"pedido_{cedula}.pdf"
        archivo_excel = "pedidos_ingatuo.xlsx"

        # Guardar Excel de registro
        try:
            prev = pd.read_excel(archivo_excel)
        except:
            prev = pd.DataFrame()
        nuevo = pd.DataFrame([{
            "Fecha": fecha, "Nombre": nombre, "Cédula": cedula, "Teléfono": telefono,
            "Correo": correo, "Comentario": comentario, "Total": total
        }])
        pd.concat([prev, nuevo], ignore_index=True).to_excel(archivo_excel, index=False)

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
            pdf.cell(40, 10, f"${item['Precio']:.2f}", 1)
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
    elif enviado:
        st.error("❌ Por favor completa todos los campos obligatorios y agrega productos al carrito.")
