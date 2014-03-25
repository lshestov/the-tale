# coding: utf-8
import contextlib

import mock

from the_tale.common.utils import testcase

from the_tale.accounts.prototypes import AccountPrototype
from the_tale.accounts.logic import register_user

from the_tale.game.logic import create_test_map

from the_tale.game.logic_storage import LogicStorage

from the_tale.game.heroes.conf import heroes_settings


class HeroLogicAccessorsTest(testcase.TestCase):

    def setUp(self):
        super(HeroLogicAccessorsTest, self).setUp()
        self.place_1, self.place_2, self.place_3 = create_test_map()

        result, account_id, bundle_id = register_user('test_user', 'test@test.com', '111111')

        self.storage = LogicStorage()
        self.storage.load_account_data(AccountPrototype.get_by_id(account_id))
        self.hero = self.storage.accounts_to_heroes[account_id]


    def check_can_process_turn(self, expected_result, banned=False, bot=False, active=False, premium=False, single=True, idle=False, sinchronized_turn=True):

        if sinchronized_turn:
            turn_number = 6 * heroes_settings.INACTIVE_HERO_DELAY + self.hero.id
        else:
            turn_number = 6 * heroes_settings.INACTIVE_HERO_DELAY + self.hero.id + 1

        with contextlib.nested(
                mock.patch('the_tale.game.heroes.prototypes.HeroPrototype.is_banned', banned),
                mock.patch('the_tale.game.heroes.prototypes.HeroPrototype.is_bot', bot),
                mock.patch('the_tale.game.heroes.prototypes.HeroPrototype.is_active', active),
                mock.patch('the_tale.game.heroes.prototypes.HeroPrototype.is_premium', premium),
                mock.patch('the_tale.game.actions.container.ActionsContainer.is_single', single),
                mock.patch('the_tale.game.actions.container.ActionsContainer.number', 1 if idle else 2)):
            self.assertEqual(self.hero.can_process_turn(turn_number), expected_result)


    def test_can_process_turn__banned(self):
        self.check_can_process_turn(True, banned=True)
        self.check_can_process_turn(False, banned=True, idle=True)
        self.check_can_process_turn(True, active=True)
        self.check_can_process_turn(True, premium=True)
        self.check_can_process_turn(True, single=False)
        self.check_can_process_turn(True, sinchronized_turn=True)
        self.check_can_process_turn(False, sinchronized_turn=False)


    def test_prefered_quest_markers__no_markers(self):
        self.assertTrue(self.hero.habit_honor.interval.is_NEUTRAL)
        self.assertTrue(self.hero.habit_peacefulness.interval.is_NEUTRAL)

        markers = set()

        for i in xrange(1000):
            markers |= self.hero.prefered_quest_markers()

        self.assertEqual(markers, set())


    def test_prefered_quest_markers__has_markers(self):
        from questgen.relations import OPTION_MARKERS

        self.hero.habit_honor.change(500)
        self.hero.habit_peacefulness.change(500)

        self.assertTrue(self.hero.habit_honor.interval.is_RIGHT_2)
        self.assertTrue(self.hero.habit_peacefulness.interval.is_RIGHT_2)

        markers = set()

        for i in xrange(1000):
            markers |= self.hero.prefered_quest_markers()

        self.hero.habit_honor.change(-1000)
        self.hero.habit_peacefulness.change(-1000)

        self.assertTrue(self.hero.habit_honor.interval.is_LEFT_2)
        self.assertTrue(self.hero.habit_peacefulness.interval.is_LEFT_2)

        for i in xrange(1000):
            markers |= self.hero.prefered_quest_markers()

        self.assertEqual(markers, set([OPTION_MARKERS.HONORABLE,
                                       OPTION_MARKERS.DISHONORABLE,
                                       OPTION_MARKERS.AGGRESSIVE,
                                       OPTION_MARKERS.UNAGGRESSIVE]))