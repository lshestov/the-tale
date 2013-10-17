# coding: utf-8
import random

import mock

from django.test import client
from django.core.urlresolvers import reverse

from dext.utils import s11n
from dext.utils.urls import url

from common.utils.testcase import TestCase
from common.postponed_tasks import PostponedTaskPrototype

from accounts.prototypes import AccountPrototype
from accounts.logic import register_user, login_url

from game.logic import create_test_map
from game.prototypes import TimePrototype

from game.heroes.prototypes import HeroPrototype

from game.pvp.models import Battle1x1, BATTLE_1X1_STATE
from game.pvp.tests.helpers import PvPTestsMixin
from game.pvp.abilities import ABILITIES


class TestRequestsBase(TestCase, PvPTestsMixin):

    def setUp(self):
        super(TestRequestsBase, self).setUp()
        create_test_map()

        result, account_id, bundle_id = register_user('test_user', 'test_user@test.com', '111111')
        self.account_1_id = account_id
        self.account_1 = AccountPrototype.get_by_id(account_id)
        self.hero_1 = HeroPrototype.get_by_account_id(self.account_1.id)

        result, account_id, bundle_id = register_user('test_user_2', 'test_user_2@test.com', '111111')
        self.account_2_id = account_id
        self.account_2 = AccountPrototype.get_by_id(account_id)
        self.hero_2 = HeroPrototype.get_by_account_id(self.account_2.id)

        self.client = client.Client()

        self.request_login('test_user@test.com')


class TestRequests(TestRequestsBase):

    def test_login_required(self):
        self.request_logout()
        self.check_redirect(reverse('game:pvp:'), login_url(reverse('game:pvp:')))

    def test_game_page_when_pvp_in_queue(self):
        self.pvp_create_battle(self.account_1, None)
        self.pvp_create_battle(self.account_2, None)
        self.check_redirect(reverse('game:pvp:'), reverse('game:'))

    def test_game_page_when_pvp_prepairing(self):
        self.pvp_create_battle(self.account_1, self.account_2)
        self.pvp_create_battle(self.account_2, self.account_1)
        self.check_html_ok(self.client.get(reverse('game:pvp:')), texts=[('pgf-change-name-warning', 1)])

    def test_game_page_when_pvp_processing(self):
        self.pvp_create_battle(self.account_1, self.account_2, BATTLE_1X1_STATE.PROCESSING)
        self.pvp_create_battle(self.account_2, self.account_1, BATTLE_1X1_STATE.PROCESSING)
        self.check_html_ok(self.client.get(reverse('game:pvp:')), texts=[('pgf-change-name-warning', 1)])

    def test_game_page__not_in_ratings(self):
        self.pvp_create_battle(self.account_1, self.account_2)
        self.pvp_create_battle(self.account_2, self.account_1)
        self.check_html_ok(self.client.get(reverse('game:pvp:')), texts=[('pgf-battle-not-in-rating', 1)])

    def test_game_page__in_ratings(self):
        self.pvp_create_battle(self.account_1, self.account_2, calculate_rating=True)
        self.pvp_create_battle(self.account_2, self.account_1, calculate_rating=True)
        self.check_html_ok(self.client.get(reverse('game:pvp:')), texts=[('pgf-battle-not-in-rating', 0)])

    @mock.patch('game.heroes.prototypes.HeroPrototype.is_name_changed', True)
    def test_game_page_when_pvp_processing_change_name_warning_hiden(self):
        self.pvp_create_battle(self.account_1, self.account_2, BATTLE_1X1_STATE.PROCESSING)
        self.pvp_create_battle(self.account_2, self.account_1, BATTLE_1X1_STATE.PROCESSING)
        self.check_html_ok(self.client.get(reverse('game:pvp:')), texts=[('pgf-change-name-warning', 0)])


class SayRequestsTests(TestRequestsBase):

    def test_no_battle(self):
        self.check_ajax_error(self.client.post(reverse('game:pvp:say'), {'text': u'some text'}), 'pvp.say.no_battle')

    def test_battle_not_in_processing_state(self):
        self.pvp_create_battle(self.account_1, None)
        self.check_ajax_error(self.client.post(reverse('game:pvp:say'), {'text': u'some text'}), 'pvp.say.no_battle')

    def test_form_errors(self):
        self.pvp_create_battle(self.account_1, self.account_2, BATTLE_1X1_STATE.PROCESSING)
        self.check_ajax_error(self.client.post(reverse('game:pvp:say'), {'text': u''}), 'pvp.say.form_errors')

    def test_success(self):
        self.pvp_create_battle(self.account_1, self.account_2, BATTLE_1X1_STATE.PROCESSING)
        response = self.client.post(reverse('game:pvp:say'), {'text': u'some text'})
        task = PostponedTaskPrototype._db_get_object(0)
        self.check_ajax_processing(response, task.status_url)


class UsePvPAbilityRequestsTests(TestRequestsBase):

    def setUp(self):
        super(UsePvPAbilityRequestsTests, self).setUp()
        self.ability = random.choice(ABILITIES.values())
        self.change_style_url = url('game:pvp:use-ability', ability=self.ability.TYPE)

    def test_no_battle(self):
        self.check_ajax_error(self.client.post(self.change_style_url), 'pvp.use_ability.no_battle')

    def test_battle_not_in_processing_state(self):
        self.pvp_create_battle(self.account_1, None)
        self.check_ajax_error(self.client.post(self.change_style_url), 'pvp.use_ability.no_battle')

    def test_wrong_style_id(self):
        self.pvp_create_battle(self.account_1, self.account_2, BATTLE_1X1_STATE.PROCESSING)
        self.pvp_create_battle(self.account_1, None)
        self.check_ajax_error(self.client.post(url('game:pvp:use-ability', ability=666)), 'pvp.ability.wrong_format')

    def test_success(self):
        self.pvp_create_battle(self.account_1, self.account_2, BATTLE_1X1_STATE.PROCESSING)
        response = self.client.post(self.change_style_url)
        task = PostponedTaskPrototype._db_get_object(0)
        self.check_ajax_processing(response, task.status_url)


class TestCallsPage(TestRequestsBase):

    def setUp(self):
        super(TestCallsPage, self).setUp()

    def test_anonimouse(self):
        self.request_logout()
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-level-restrictions-message', 0),
                                                                              ('pgf-unlogined-message', 1),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-fast-account-message', 0)])

    def test_fast_user(self):
        self.account_1.is_fast = True
        self.account_1.save()
        self.hero_1.is_fast = True
        self.hero_1.save()
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('common.fast_account', 0),
                                                                              ('pgf-level-restrictions-message', 0),
                                                                              ('pgf-unlogined-message', 0),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-fast-account-message', 1)])

    @mock.patch('game.heroes.prototypes.HeroPrototype.can_participate_in_pvp', False)
    def test_no_rights(self):
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pvp.no_rights', 0),
                                                                              ('pgf-level-restrictions-message', 0),
                                                                              ('pgf-unlogined-message', 0),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-fast-account-message', 1)])

    def test_normal_account(self):
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-level-restrictions-message', 1),
                                                                              ('pgf-unlogined-message', 0),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-fast-account-message', 0)])

    def test_no_battles(self):
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-no-calls-message', 1),
                                                                              ('pgf-no-current-battles-message', 1), ])

    def test_own_battle(self):
        self.pvp_create_battle(self.account_1, None, BATTLE_1X1_STATE.WAITING)
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-no-calls-message', 0),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-own-battle-message', 1)])

    def test_low_level_battle(self):
        self.hero_1._model.level = 100
        self.hero_1.save()
        self.pvp_create_battle(self.account_2, None, BATTLE_1X1_STATE.WAITING)
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-no-calls-message', 0),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-can-not-accept-call', 1)])

    def test_height_level_battle(self):
        self.hero_2._model.level = 100
        self.hero_2.save()
        self.pvp_create_battle(self.account_2, None, BATTLE_1X1_STATE.WAITING)
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-no-calls-message', 0),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-can-not-accept-call', 1)])

    def test_battle(self):
        self.pvp_create_battle(self.account_2, None, BATTLE_1X1_STATE.WAITING)
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-no-calls-message', 0),
                                                                              ('pgf-no-current-battles-message', 1),
                                                                              ('pgf-accept-battle', 1)])

    def test_current_battle(self):
        self.pvp_create_battle(self.account_2, self.account_1, BATTLE_1X1_STATE.PROCESSING)
        self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-no-calls-message', 1),
                                                                              ('pgf-no-current-battles-message', 0),
                                                                              ('pgf-accept-battle', 0),
                                                                              self.hero_1.name,
                                                                              self.hero_2.name])

    def test_only_waiting_and_processing_battles(self):
        for state in BATTLE_1X1_STATE._records:
            if state._is_WAITING or state._is_PROCESSING:
                continue
            self.pvp_create_battle(self.account_2, None, state)
            self.check_html_ok(self.client.get(reverse('game:pvp:calls')), texts=[('pgf-no-calls-message', 1), ('pgf-no-current-battles-message', 1)])
            Battle1x1.objects.all().delete()
