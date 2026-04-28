import qrcode

url = "https://tsamuel33-tech.github.io/wedding-gospel/"
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill='black', back_color='white')
img.save('wedding_qr.png')
print("QR code generated as wedding_qr.png")