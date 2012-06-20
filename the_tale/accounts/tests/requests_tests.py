# coding: utf-8
from django.test import TestCase, client
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth import authenticate as django_authenticate

from dext.utils import s11n

from common.utils.fake import FakeLogger

from accounts.logic import register_user
from accounts.models import RegistrationTask, REGISTRATION_TASK_STATE, CHANGE_CREDENTIALS_TASK_STATE, ChangeCredentialsTask
from accounts.prototypes import RegistrationTaskPrototype, AccountPrototype

from game.logic import create_test_map

class TestRequests(TestCase):

    def setUp(self):
        create_test_map()
        register_user('test_user', 'test_user@test.com', '111111')
        self.client = client.Client()

    def login(self, email, password):
        response = self.client.post(reverse('accounts:login'), {'email': email, 'password': password})
        self.assertEqual(response.status_code, 200)

    def test_introduction_page(self):
        response = self.client.get(reverse('accounts:introduction'))
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_after_login(self):
        self.login('test_user@test.com', '111111')
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)

    def test_login_command(self):
        self.login('test_user@test.com', '111111')

    def test_logout_command(self):
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['Content-Type'])
        self.assertEqual(s11n.from_json(response.content), {'status': 'ok'})

        response = self.client.get(reverse('accounts:logout'))
        self.assertTrue('text/html' in response['Content-Type'])
        self.assertEqual(response.status_code, 302)


class TestRegistrationRequests(TestCase):

    def setUp(self):
        create_test_map()
        register_user('test_user', 'test_user@test.com', '111111')
        self.client = client.Client()


    def test_fast_registration_processing(self):
        response = self.client.post(reverse('accounts:fast-registration'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content), {'status': 'processing',
                                                            'status_url': reverse('accounts:fast-registration-status')})
        self.assertEqual(RegistrationTask.objects.all().count(), 1)

    def test_fast_registration_for_logged_in_user(self):
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.post(reverse('accounts:fast-registration'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')

    def test_fast_registration_second_request(self):
        response = self.client.post(reverse('accounts:fast-registration'))
        response = self.client.post(reverse('accounts:fast-registration'))
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')
        self.assertEqual(RegistrationTask.objects.all().count(), 1)

    def test_fast_registration_second_request_after_error(self):
        response = self.client.post(reverse('accounts:fast-registration'))

        task = RegistrationTask.objects.all().order_by('id')[0]
        task.state = REGISTRATION_TASK_STATE.UNPROCESSED
        task.save()
        response = self.client.post(reverse('accounts:fast-registration'))
        self.assertEqual(s11n.from_json(response.content)['status'], 'processing')
        self.assertEqual(RegistrationTask.objects.all().count(), 2)

        task = RegistrationTask.objects.all().order_by('id')[1]
        task.state = REGISTRATION_TASK_STATE.ERROR
        task.save()
        response = self.client.post(reverse('accounts:fast-registration'))
        self.assertEqual(s11n.from_json(response.content)['status'], 'processing')
        self.assertEqual(RegistrationTask.objects.all().count(), 3)

        task = RegistrationTask.objects.all().order_by('id')[2]
        task.delete()
        response = self.client.post(reverse('accounts:fast-registration'))
        self.assertEqual(s11n.from_json(response.content)['status'], 'processing')
        self.assertEqual(RegistrationTask.objects.all().count(), 3)

    def test_fast_registration_status_after_login(self):
        response = self.client.post(reverse('accounts:fast-registration'))
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.get(reverse('accounts:fast-registration-status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content), {'status': 'ok'})

    def test_fast_registration_status_without_registration(self):
        response = self.client.get(reverse('accounts:fast-registration-status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')

    def test_fast_registration_status_waiting(self):
        response = self.client.post(reverse('accounts:fast-registration'))
        response = self.client.get(reverse('accounts:fast-registration-status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content), {'status': 'processing',
                                                            'status_url': reverse('accounts:fast-registration-status')})

    def test_fast_registration_status_timeout(self):
        response = self.client.post(reverse('accounts:fast-registration'))

        task = RegistrationTask.objects.all()[0]
        task.state = REGISTRATION_TASK_STATE.UNPROCESSED
        task.save()

        response = self.client.get(reverse('accounts:fast-registration-status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')

    def test_fast_registration_status_error(self):
        response = self.client.post(reverse('accounts:fast-registration'))

        task = RegistrationTask.objects.all()[0]
        task.state = REGISTRATION_TASK_STATE.ERROR
        task.save()

        response = self.client.get(reverse('accounts:fast-registration-status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')


    def test_fast_registration_status_ok(self):
        response = self.client.post(reverse('accounts:fast-registration'))

        task_model = RegistrationTask.objects.all()[0]
        task = RegistrationTaskPrototype.get_by_id(task_model.id)
        task.process(FakeLogger())

        response = self.client.get(reverse('accounts:fast-registration-status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content), {'status': 'ok'})


class TestProfileRequests(TestCase):

    def setUp(self):
        create_test_map()
        self.client = client.Client()

        result, account_id, bundle_id = register_user('test_user', 'test_user@test.com', '111111')
        self.account = AccountPrototype.get_by_id(account_id)

    def test_profile_page_unlogined(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_page_logined(self):
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_edited(self):
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.get(reverse('accounts:profile-edited'))
        self.assertEqual(response.status_code, 200)

    def test_profile_confirm_email_request(self):
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.get(reverse('accounts:confirm-email-request'))
        self.assertEqual(response.status_code, 200)

    def test_profile_update_password(self):
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.post(reverse('accounts:profile-update'), {'email': 'test_user@test.com', 'password': '222222'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content), {'status': 'ok', 'data': {'next_url': reverse('accounts:profile-edited')}})
        self.assertEqual(ChangeCredentialsTask.objects.all().count(), 1)
        self.assertEqual(ChangeCredentialsTask.objects.all()[0].state, CHANGE_CREDENTIALS_TASK_STATE.PROCESSED)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(django_authenticate(username='test_user', password='222222').id, self.account.user.id)

    def test_profile_update_email(self):
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.post(reverse('accounts:profile-update'), {'email': 'test_user@test.ru'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content), {'status': 'ok', 'data': {'next_url': reverse('accounts:confirm-email-request')}})
        self.assertEqual(ChangeCredentialsTask.objects.all().count(), 1)
        self.assertEqual(ChangeCredentialsTask.objects.all()[0].state, CHANGE_CREDENTIALS_TASK_STATE.EMAIL_SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(django_authenticate(username='test_user', password='111111').id, self.account.user.id)
        self.assertEqual(django_authenticate(username='test_user', password='111111').email, 'test_user@test.com')

    def test_profile_update_duplicate_email(self):
        register_user('duplicated_user', 'duplicated@test.com', '111111')
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.post(reverse('accounts:profile-update'), {'email': 'duplicated@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')
        self.assertEqual(ChangeCredentialsTask.objects.all().count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(django_authenticate(username='test_user', password='111111').id, self.account.user.id)
        self.assertEqual(django_authenticate(username='test_user', password='111111').email, 'test_user@test.com')

    def test_profile_update_fast_errors(self):
        response = self.client.post(reverse('accounts:fast-registration'))

        response = self.client.post(reverse('accounts:profile-update'), {'email': 'test_user@test.ru'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')

        response = self.client.post(reverse('accounts:profile-update'), {'password': '111111'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(s11n.from_json(response.content)['status'], 'error')

        self.assertEqual(ChangeCredentialsTask.objects.all().count(), 0)
        self.assertEqual(len(mail.outbox), 0)


    def test_profile_confirm_email(self):
        response = self.client.post(reverse('accounts:login'), {'email': 'test_user@test.com', 'password': '111111'})
        response = self.client.post(reverse('accounts:profile-update'), {'email': 'test_user@test.ru'})

        uuid = ChangeCredentialsTask.objects.all()[0].uuid

        response = self.client.get(reverse('accounts:confirm-email')+'?uuid='+uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChangeCredentialsTask.objects.all().count(), 1)
        self.assertEqual(ChangeCredentialsTask.objects.all()[0].state, CHANGE_CREDENTIALS_TASK_STATE.PROCESSED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(django_authenticate(username='test_user', password='111111').email, 'test_user@test.ru')
