from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from fcm_django.fcm import fcm_send_topic_message
from datetime import datetime


def convert_str_to_date(string, format_string="%d/%m/%Y"):
    return datetime.strptime(string, format_string)


def send_to_fb_topic(topic, data_message):
    result = fcm_send_topic_message(topic_name=topic,
                                    data_message=data_message)

    return result


def send_email(send_to, subject, html_message, attachment_location=None):
    if settings.ALLOW_SEND_EMAIL:
        subject, from_email, to = subject, settings.EMAIL_HOST_USER, send_to
        text_content = html_message
        html_content = html_message
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        if attachment_location is not None:
            msg.attach_file(attachment_location)
        msg.send()
    else:
        print('Sending email %s, %s' % (subject, html_message))
