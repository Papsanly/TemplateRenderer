import base64
import qrcode
from io import BytesIO
from jinja2 import Environment, FileSystemLoader

# Setup
env = Environment(loader=FileSystemLoader('renderer/templates'))
template = env.get_template('wefly_certificate.html')

# Generate QR
qr = qrcode.QRCode(version=1, box_size=10, border=0)
qr.add_data("https://wefly.aero/activate/PDLEDC")
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
buffer = BytesIO()
img.save(buffer, format="PNG")
buffer.seek(0)
qr_code = f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"

# Render
html = template.render(
    code="PDLEDC",
    expiration="11/30/2026",
    gate="Boeing 737 MAX",
    duration="120",
    seat_class="First Class",
    qr_code=qr_code,
    is_birthday=True
)

with open('renderer/templates/test_temp.html', 'w') as f:
    f.write(html)

print("HTML saved to renderer/templates/test_temp.html")
