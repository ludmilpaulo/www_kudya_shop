from django.db import models
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
from datetime import datetime
from django.core.mail import send_mail


class Career(models.Model):
    title = models.CharField(max_length=100)
    description = CKEditor5Field("Text", config_name="extends")

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    resume = models.FileField(upload_to="resumes/")

    def __str__(self):
        return f"Application for {self.career.title} by {self.full_name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if this is a new application
        super(JobApplication, self).save(*args, **kwargs)
        if is_new:
            self.send_confirmation_email()

    def send_confirmation_email(self):
        subject = f"Recebemos sua candidatura para {self.career.title}"
        from_email = settings.DEFAULT_FROM_EMAIL
        message = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f4f4f4;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: auto;
                        background-color: #ffffff;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background-color: #4CAF50;
                        padding: 10px;
                        text-align: center;
                        color: white;
                        border-top-left-radius: 10px;
                        border-top-right-radius: 10px;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                    .content p {{
                        line-height: 1.6;
                    }}
                    .footer {{
                        margin-top: 20px;
                        text-align: center;
                        font-size: 12px;
                        color: #888888;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>Recebemos sua candidatura!</h1>
                    </div>
                    <div class="content">
                        <p>Olá {self.full_name},</p>
                        <p>Muito obrigado por se candidatar a fazer parte da nossa equipe na Kudya! Recebemos sua inscrição para a vaga de <strong>{self.career.title}</strong> e iremos revisar suas qualificações e experiência com muito cuidado.</p>
                        <p>Por favor, nos dê uma semana para processar sua candidatura. Se você não receber uma resposta nossa dentro de duas semanas, isso não significa que a jornada termina aqui! Estamos sempre em busca de talentos e manteremos sua candidatura em nossos arquivos para futuras oportunidades que combinem com suas habilidades e paixão.</p>
                        <p>Agradecemos seu interesse em se juntar à nossa equipe e desejamos muita sorte com sua candidatura.</p>
                        <p>Com os melhores cumprimentos,<br>Equipe Kudya</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {datetime.now().year} Kudya Todos os direitos reservados.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        send_mail(
            subject,
            "",
            from_email,
            [self.email],
            fail_silently=False,
            html_message=message,
        )
