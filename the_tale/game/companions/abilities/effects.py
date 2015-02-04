# coding: utf-8
from rels import Column
from rels.django import DjangoEnum

from the_tale.game import relations as game_relations

from the_tale.game.balance import constants as c

from the_tale.game.heroes import relations as heroes_relations
from the_tale.game.heroes.habilities import battle as battle_abilities

from the_tale.game.companions.abilities import relations


class Base(object):
    TYPE = None

    def __init__(self):
        pass

    @property
    def uid(self):
        return (self.TYPE, None)

    def modify_attribute(self, modifier, value):
        return self._modify_attribute(modifier, value)

    def check_attribute(self, modifier):
        return self._check_attribute(modifier)

    def update_context(self, actor, enemy):
        return self._update_context(actor, enemy)


    def _modify_attribute(self, modifier, value):
        return value

    def _check_attribute(self, modifier):
        return False

    def _update_context(self, actor, enemy):
        pass


class Checker(Base):
    MODIFIER = None

    def _check_attribute(self, modifier):
        return modifier == self.MODIFIER


class Multiplier(Base):
    MODIFIER = None

    def __init__(self, multiplier):
        super(Multiplier, self).__init__()
        self.multiplier = multiplier

    def _modify_attribute(self, modifier, value):
        if modifier == self.MODIFIER:
            return value *self.multiplier
        return value


class Summand(Base):
    MODIFIER = None

    def __init__(self, summand):
        super(Summand, self).__init__()
        self.summand = summand

    def _modify_attribute(self, modifier, value):
        if modifier == self.MODIFIER:
            return value + self.summand
        return value



class CoherenceSpeed(Multiplier):
    TYPE = relations.EFFECT.COHERENCE_SPEED
    MODIFIER = heroes_relations.MODIFIERS.COHERENCE_EXPERIENCE


class ChangeHabits(Base):
    TYPE = relations.EFFECT.CHANGE_HABITS

    def __init__(self, habit_type, habit_sources, **kwargs):
        super(ChangeHabits, self).__init__(**kwargs)
        self.habit_type = habit_type
        self.habit_sources = frozenset(habit_sources)

    @property
    def uid(self):
        return (self.TYPE, self.habit_type)

    def _modify_attribute(self, modifier, value):
        if modifier.is_HABITS_SOURCES:
            return value | self.habit_sources
        return value


class QuestMoneyReward(Multiplier):
    TYPE = relations.EFFECT.QUEST_MONEY_REWARD
    MODIFIER = heroes_relations.MODIFIERS.QUEST_MONEY_REWARD


class MaxBagSize(Summand):
    TYPE = relations.EFFECT.MAX_BAG_SIZE
    MODIFIER = heroes_relations.MODIFIERS.MAX_BAG_SIZE


class PoliticsPower(Multiplier):
    TYPE = relations.EFFECT.POLITICS_POWER
    MODIFIER = heroes_relations.MODIFIERS.POWER


class MagicDamageBonus(Multiplier):
    TYPE = relations.EFFECT.MAGIC_DAMAGE_BONUS
    MODIFIER = heroes_relations.MODIFIERS.MAGIC_DAMAGE

class PhysicDamageBonus(Multiplier):
    TYPE = relations.EFFECT.PHYSIC_DAMAGE_BONUS
    MODIFIER = heroes_relations.MODIFIERS.PHYSIC_DAMAGE

class Speed(Multiplier):
    TYPE = relations.EFFECT.SPEED
    MODIFIER = heroes_relations.MODIFIERS.SPEED


class BattleAbility(Base):
    TYPE = relations.EFFECT.BATTLE_ABILITY

    def __init__(self, ability, **kwargs):
        super(BattleAbility, self).__init__(**kwargs)
        self.ability = ability(ability.MAX_LEVEL)

    @property
    def uid(self):
        return (self.TYPE, self.habit_type)

    def _modify_attribute(self, modifier, value):
        if modifier.is_INITIATIVE:
            return value * (1 + c.COMPANION_BATTLE_STRIKE_PROBABILITY)
        if modifier.is_ADDITIONAL_ABILITIES:
            value.append(self.ability)
            return value
        return value


class Initiative(Multiplier):
    TYPE = relations.EFFECT.INITIATIVE
    MODIFIER = heroes_relations.MODIFIERS.INITIATIVE


class BattleProbability(Summand):
    TYPE = relations.EFFECT.BATTLE_PROBABILITY
    MODIFIER = heroes_relations.MODIFIERS.BATTLES_PER_TURN


class LootProbability(Multiplier):
    TYPE = relations.EFFECT.LOOT_PROBABILITY
    MODIFIER = heroes_relations.MODIFIERS.LOOT_PROBABILITY


class CompanionDamage(Summand):
    TYPE = relations.EFFECT.COMPANION_DAMAGE
    MODIFIER = heroes_relations.MODIFIERS.COMPANION_DAMAGE

class CompanionDamageProbability(Multiplier):
    TYPE = relations.EFFECT.COMPANION_DAMAGE_PROBABILITY
    MODIFIER = heroes_relations.MODIFIERS.COMPANION_DAMAGE_PROBABILITY


class CompanionStealMoney(Checker):
    TYPE = relations.EFFECT.COMPANION_STEAL_MONEY
    MODIFIER = heroes_relations.MODIFIERS.COMPANION_STEAL_MONEY

class CompanionStealItem(Checker):
    TYPE = relations.EFFECT.COMPANION_STEAL_ITEM
    MODIFIER = heroes_relations.MODIFIERS.COMPANION_STEAL_ITEM


class ABILITIES(DjangoEnum):
    description = Column()
    only_start = Column(unique=False)
    effect = Column(single_type=False)

    records = (
        (u'OBSTINATE', 0, u'строптивый', u'очень медленный рост слаженности', True, CoherenceSpeed(multiplier=0.70)),
        (u'STUBBORN', 1, u'упрямый', u'медленный рост слаженности', True, CoherenceSpeed(multiplier=0.85)),
        (u'BONA_FIDE', 2, u'добросовестный', u'быстрый рост слаженности', True, CoherenceSpeed(multiplier=1.15)),
        (u'MANAGING', 3, u'исполнительный', u'очень быстрый рост слаженности', True, CoherenceSpeed(multiplier=1.30)),

        (u'AGGRESSIVE', 4, u'агрессивный', u'повышает агрессивность героя', True,
         ChangeHabits(habit_type=game_relations.HABIT_TYPE.PEACEFULNESS, habit_sources=(heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_AGGRESSIVE, ))),
        (u'PEACEFUL', 5, u'миролюбивый', u'понижает агрессивность героя', True,
         ChangeHabits(habit_type=game_relations.HABIT_TYPE.PEACEFULNESS, habit_sources=(heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_PEACEFULL,))),
        (u'RESERVED', 6, u'сдержанный', u'склоняет героя к сдержанности', True,
         ChangeHabits(habit_type=game_relations.HABIT_TYPE.PEACEFULNESS, habit_sources=(heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_PEACEFULL_NEUTRAL_1,
                                                                                        heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_PEACEFULL_NEUTRAL_2))),
        (u'CANNY', 7, u'себе на уме', u'склоняет героя быть себе на уме', True,
         ChangeHabits(habit_type=game_relations.HABIT_TYPE.HONOR, habit_sources=(heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_HONOR_NEUTRAL_1,
                                                                                 heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_HONOR_NEUTRAL_2))),
        (u'HONEST', 8, u'честный', u'повышает честь героя', True,
         ChangeHabits(habit_type=game_relations.HABIT_TYPE.HONOR, habit_sources=(heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_HONORABLE,))),
        (u'SNEAKY', 9, u'подлый', u'понижает честь героя', True,
         ChangeHabits(habit_type=game_relations.HABIT_TYPE.HONOR, habit_sources=(heroes_relations.HABIT_CHANGE_SOURCE.COMPANION_DISHONORABLE,))),

        (u'CHARMING', 10, u'очаровательный', u'симпатичен горожанам. Крупный бонус к денежной награде за квесты', True, QuestMoneyReward(multiplier=2.0)),
        (u'CUTE', 11, u'милый', u'симпатичен горожанам. Небольшой бонус к денежной награде за квесты', True, QuestMoneyReward(multiplier=1.5)),
        (u'FRIGHTFUL', 12, u'страшный', u'пугает горожан своим видом. Маленький штраф к оплате квестов.', True, QuestMoneyReward(multiplier=0.75)),
        (u'TERRIBLE', 13, u'мороз по коже', u'пугает горожан своим видом. Болшой штраф к оплате квестов.', True, QuestMoneyReward(multiplier=0.50)),

        (u'PACK', 14, u'вьючный', u'1 дополнительное место для лута', False, MaxBagSize(summand=1)),
        (u'FREIGHT', 15, u'грузовой', u'2 дополнительных места для лута', False, MaxBagSize(summand=2)),
        (u'DRAFT', 16, u'тягловой', u'3 дополнительных места для лута', False, MaxBagSize(summand=3)),

        (u'KNOWN', 17, u'известный', u'находит более политически важную работу', False, PoliticsPower(multiplier=1.5)),
        (u'CAD', 18, u'хам', u'хамит горожанам. Минус к влиянию заданий', True, PoliticsPower(multiplier=0.75)),

        (u'FIT_OF_ENERGY', 19, u'прилив сил', u'бонус к физическому урону, наносимому героем', False, MagicDamageBonus(multiplier=1.1)),
        (u'PEP', 20, u'бодрость духа', u'бонус к магическому урону, наносимому героем', False, PhysicDamageBonus(multiplier=1.1)),

        (u'SLED', 21, u'ездовой', u'постоянный небольшой бонус к скорости героя', False, Speed(multiplier=1.1)),
        (u'SLOW', 22, u'медлительный', u'постоянный небольшой штраф к скорости героя', True, Speed(multiplier=0.9)),
        (u'FOOTED_SLED', 23, u'быстроногий ездовой', u'постоянный большой бонус к скорости героя', False, Speed(multiplier=1.2)),

        (u'FIGHTER', 24, u'боец', u'увеличивает инициативу героя, в бою может применить способность «Удар»', False,
         BattleAbility(ability=battle_abilities.HIT)),
        (u'RAM', 25, u'громила', u'увеличивает инициативу героя, в бою может применить способность «тяжёлый удар»', False,
         BattleAbility(ability=battle_abilities.STRONG_HIT)),
        (u'HOUSEBREAKER', 26, u'таран', u'увеличивает инициативу героя, в бою может применить способность «Разбег-толчок»', False,
         BattleAbility(ability=battle_abilities.RUN_UP_PUSH)),
        (u'ARSONIST', 27, u'поджигатель', u'увеличивает инициативу героя, в бою может применить способность «Огненный шар»', False,
         BattleAbility(ability=battle_abilities.FIREBALL)),
        (u'POISONER', 28, u'отравитель', u'увеличивает инициативу героя, в бою может применить способность «Ядовитое облако»', False,
         BattleAbility(ability=battle_abilities.POISON_CLOUD)),
        (u'FROST', 29, u'морозко', u'увеличивает инициативу героя, в бою может применить способность «Заморозка»', False,
         BattleAbility(ability=battle_abilities.FREEZING)),

        (u'UNGAINLY', 30, u'неуклюжий', u'большой штраф к инициативе героя', True, Initiative(multiplier=0.8)),
        (u'CLUMSY', 31, u'неповоротливый', u'малый штраф к инициативе героя', True, Initiative(multiplier=0.9)),
        (u'CLEVER', 32, u'ловкий', u'малый бонус к инициативе героя', True, Initiative(multiplier=1.1)),
        (u'IMPETUOUS', 33, u'стремительный', u'большой бонус к инициативе героя', True, Initiative(multiplier=1.2)),

        (u'NOISY', 34, u'шумный', u'так сильно шумит, что привлекает внимание большего количесва врагов', True, BattleProbability(summand=0.05)),
        (u'DEATHY', 35, u'смертельно страшный', u'распугивает чудищ, вероятность встретить врага стремится к нулю', True, BattleProbability(summand=-1)),

        (u'TORTURER', 36, u'терзатель', u'растерзывает врагов в бою так сильно, что уменьшается шанс найти уцелевший лут с мобов', True, LootProbability(multiplier=0.8)),
        (u'HUNTER', 37, u'охотник', u'увеличивает шанс поднятия лута со всех врагов', False, LootProbability(multiplier=1.2)),

        (u'NOT_LIFER', 38, u'не жилец', u'получает дополнительную едину урона', True, CompanionDamage(summand=1)),
        (u'PUNY', 39, u'тщедушный', u'получает дополнительные 2 единицы урона', True, CompanionDamage(summand=2)),

        (u'CAMOUFLAGE', 40, u'камуфляж', u'реже получает урон в бою', False, CompanionDamageProbability(multiplier=0.9)),
        (u'FLYING', 41, u'летающий', u'значительно реже получает урон в бою', False, CompanionDamageProbability(multiplier=0.8)),

        (u'PICKPOCKET', 42, u'карманник', u'В каждом городе крадёт из карманов горожан немного денег', False, CompanionStealMoney()),
        (u'ROBBER', 43, u'грабитель', u'В каждом городе крадёт у горожан что-нибудь, возможно артефакт', False, CompanionStealItem()),
    )
