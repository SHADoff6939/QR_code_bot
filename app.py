import qrcode
import telebot
from PIL import Image
from io import BytesIO

API_KEY = 'ADD YOUR API HERE'
bot = telebot.TeleBot(API_KEY)

# Dictionary to track user data for QR code (text, fill color, background color, and logo)
user_data = {}

# /start command handler
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     '*Hello!*\nThis bot generates QR codes from your text. '
                     'Use /generate to create your QR code.',
                     parse_mode='Markdown')

# /generate command handler to ask user for text input
@bot.message_handler(commands=['generate'])
def ask_for_text(message):
    bot.send_message(message.chat.id, 'Please send the text you want to convert into a QR code:')
    user_data[message.chat.id] = {'text': None, 'fill': 'black', 'back': 'white', 'logo': None}  # Set default colors

# Handler to capture text input
@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]['text'] is None)
def capture_text(message):
    user_data[message.chat.id]['text'] = message.text  # Store the user input text
    bot.send_message(message.chat.id, 'Now, please send the fill color for the QR code (default is black):')

# Handler to capture the fill color
@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]['fill'] == 'black')
def capture_fill_color(message):
    fill_color = message.text
    user_data[message.chat.id]['fill'] = fill_color
    bot.send_message(message.chat.id, 'Please send the background color for the QR code (default is white):')

# Handler to capture the background color
@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]['back'] == 'white')
def capture_back_color(message):
    back_color = message.text
    user_data[message.chat.id]['back'] = back_color
    bot.send_message(message.chat.id, 'You can upload an image (optional) to embed into the QR code, or send /skip.')

# Handler to capture the logo image
@bot.message_handler(content_types=['photo'])
def capture_logo(message):
    # Download the image sent by the user
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Save the downloaded logo image into user_data
    user_data[message.chat.id]['logo'] = Image.open(BytesIO(downloaded_file))

    # Proceed to generate the QR code
    generate_qr_code(message)

# Skip the logo if not provided
@bot.message_handler(commands=['skip'])
def skip_logo(message):
    generate_qr_code(message)

# Function to generate and send the QR code
def generate_qr_code(message):
    # Retrieve data from user_data
    qr_text = user_data[message.chat.id]['text']
    fill_color = user_data[message.chat.id]['fill']
    back_color = user_data[message.chat.id]['back']
    logo = user_data[message.chat.id]['logo']

    # Create a QRCode instance
    qr = qrcode.QRCode(version=3, box_size=10, border=5)
    qr.add_data(qr_text)
    qr.make(fit=True)

    # Create the image with user-specified colors
    img = qr.make_image(fill=fill_color, back_color=back_color).convert('RGB')

    # If a logo was provided, overlay it onto the QR code
    if logo:
        # Ensure the logo has an alpha (transparency) channel
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')

        # Resize the logo
        logo_size = (img.size[0] // 4, img.size[1] // 4)  # Resize to 1/4th of the QR code size
        logo = logo.resize(logo_size)

        # Create a mask for the logo's transparency
        logo_mask = logo.split()[3]  # Extract the alpha channel as the mask

        # Calculate position to paste the logo (center)
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)

        # Paste the logo into the QR code using the alpha channel as a mask
        img.paste(logo, pos, mask=logo_mask)

    # Convert the image to a format Telegram can send
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Send the QR code image to the user
    bot.send_photo(message.chat.id, img_byte_arr, caption="Here is your QR code!")

    # Clear user data after sending the QR code
    del user_data[message.chat.id]

# Start polling for updates
bot.polling()
