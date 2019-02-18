# coding: utf-8
from scrapy.mail import MailSender
from brand_spider import settings


def send_mail(subject, body):
        mailer = MailSender(
            smtphost=settings.MAIL_HOST,
            mailfrom=settings.MAIL_FROM,
            smtpuser=settings.MAIL_USER,
            smtppass=settings.MAIL_PASS,
            smtpport=25
        )
        to = settings.MAIL_TO
        mailer.send(to=to, subject=subject.encode('utf-8'), body=body.encode('utf-8'))


if __name__ == '__main__':
    send_mail(u'Scrapy状态测试', u'Scrapy当前的状态，Hello world!')