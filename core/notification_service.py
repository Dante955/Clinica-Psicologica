import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
from datetime import datetime, timedelta

from database.database_manager import session_scope
from database.models import Appointment
from sqlalchemy import func

class NotificationService:
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        self.smtp_server = self.config.get('email', 'smtp_server', fallback=None)
        self.port = self.config.getint('email', 'port', fallback=587)
        self.sender_email = self.config.get('email', 'sender_email', fallback=None)
        self.password = self.config.get('email', 'password', fallback=None)

    def is_configured(self):
        """Verifica si la configuración de email está completa."""
        return all([self.smtp_server, self.port, self.sender_email, self.password])

    def send_email(self, receiver_email, subject, body):
        if not self.is_configured():
            raise ConnectionError("La configuración de email está incompleta en config.ini.")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message.attach(MIMEText(body, "html"))

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, receiver_email, message.as_string())
            print(f"Correo de recordatorio enviado a {receiver_email}")
            return True
        except Exception as e:
            print(f"Error al enviar correo a {receiver_email}: {e}")
            return False

    def send_appointment_reminders(self):
        """Busca citas próximas y envía recordatorios."""
        tomorrow = datetime.now() + timedelta(days=1)
        day_after_tomorrow = tomorrow + timedelta(days=1)

        with session_scope() as session:
            # SQL Server: usar CAST para convertir datetime a date
            from sqlalchemy import cast, Date
            upcoming_appointments = session.query(Appointment).filter(
                cast(Appointment.appointment_time, Date) == tomorrow.date(),
                Appointment.status == 'programada'
            ).all()

            for appt in upcoming_appointments:
                if appt.patient and appt.patient.email:
                    subject = f"Recordatorio de Cita - {appt.patient.full_name}"
                    body = f"""
                    <html><body>
                    <p>Hola {appt.patient.full_name},</p>
                    <p>Te recordamos que tienes una cita programada para mañana, <b>{appt.appointment_time.strftime('%d-%m-%Y a las %H:%M')}</b>.</p>
                    <p>¡Te esperamos!</p>
                    </body></html>
                    """
                    self.send_email(appt.patient.email, subject, body)
