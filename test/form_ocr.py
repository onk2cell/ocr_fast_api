import streamlit as st
from streamlit_drawable_canvas import st_canvas
from pdf2image import convert_from_bytes
from reportlab.pdfgen import canvas as rl_canvas
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="PDF Field Filler", layout="wide")
st.title("📄 Interactive PDF Field Filler")

# Upload PDF
pdf_file = st.file_uploader("Upload your PDF form", type=["pdf"])

# Choose section
section_to_fill = st.selectbox("Select section to fill", ["Aadhar Info", "PAN Info", "Bank Info"])

# Let user enter custom data
default_data = {
    "Aadhar Info": "Name: Swapnil Kadam\nAadhar: 1234-5678-9012\nDOB: 01/01/1990\nAddress: Pune, Maharashtra",
    "PAN Info": "Name: Swapnil Kadam\nPAN: ABCDE1234F",
    "Bank Info": "Account Holder: Swapnil Kadam\nBank: SBI\nA/C: 123456789012\nIFSC: SBIN0001234"
}
user_input = st.text_area("✏️ Enter the text you want to inject", default_data[section_to_fill], height=150)

# Show canvas
if pdf_file:
    pdf_bytes = pdf_file.read()
    image = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, fmt="png")[0]
    w, h = image.size

    st.write("🖼️ Draw a rectangle over the area where the info should go:")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0.3)",
        stroke_width=2,
        stroke_color="#000000",
        background_image=image,
        update_streamlit=True,
        height=h,
        width=w,
        drawing_mode="rect",
        key="canvas"
    )

    # When rectangle is drawn
    if canvas_result.json_data and "objects" in canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
        obj = canvas_result.json_data["objects"][-1]
        left = obj["left"]
        top = obj["top"]
        y_flipped = h - top

        if st.button("🖊️ Fill PDF with above text in selected area"):
            # Create overlay with user input
            packet = BytesIO()
            c = rl_canvas.Canvas(packet, pagesize=(w, h))
            c.setFont("Helvetica", 10)
            for i, line in enumerate(user_input.split("\n")):
                c.drawString(left + 5, y_flipped - (i * 14), line)
            c.save()
            packet.seek(0)

            # Merge with original PDF
            overlay = PdfReader(packet)
            base_pdf = PdfReader(BytesIO(pdf_bytes))
            output = PdfWriter()
            page = base_pdf.pages[0]
            page.merge_page(overlay.pages[0])
            output.add_page(page)

            # Return file
            final_pdf = BytesIO()
            output.write(final_pdf)
            st.download_button(
                label="📥 Download Filled PDF",
                data=final_pdf.getvalue(),
                file_name="filled_form.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Draw a rectangle to select where the text should go.")
else:
    st.warning("Please upload a PDF to begin.")
