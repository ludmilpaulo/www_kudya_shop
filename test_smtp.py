import smtplib
import ssl

def test_smtp_connection():
    smtp_server = 'smtpout.secureserver.net'
    port = 465  # For SSL
    login = 'support@maindodigital.com'  # Your email
    password = 'Maitland@2024'  # Your email password

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.set_debuglevel(1)  # Show communication with the server
            server.login(login, password)
            print("Successfully connected to the SMTP server and logged in.")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_smtp_connection()
