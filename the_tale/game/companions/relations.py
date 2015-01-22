# coding: utf-8

from rels import Column
from rels.django import DjangoEnum

from the_tale.game.cards import relations as cards_relations


class STATE(DjangoEnum):
   records = ( (u'ENABLED', 0, u'в игре'),
               (u'DISABLED', 1, u'вне игры'),)


class TYPE(DjangoEnum):
   records = ( (u'LIVING', 0, u'живой'),
               (u'CONSTRUCT', 1, u'магомеханический'),
               (u'UNUSUAL', 2, u'необычный') )


class DEDICATION(DjangoEnum):
   records = ( (u'INDECISIVE', 0, u'нерешительный'),
               (u'BOLD', 1, u'смелый'),
               (u'BRAVE', 2, u'храбрый'),
               (u'VALIANT', 3, u'доблестный'),
               (u'HEROIC', 4, u'героический') )


class RARITY(DjangoEnum):
    card_rarity = Column()

    records = ( (u'COMMON', 0, u'обычный спутник', cards_relations.RARITY.COMMON),
                (u'UNCOMMON', 1, u'необычный спутник', cards_relations.RARITY.UNCOMMON),
                (u'RARE', 2, u'редкий спутник', cards_relations.RARITY.RARE),
                (u'EPIC', 3, u'эпический спутник', cards_relations.RARITY.EPIC),
                (u'LEGENDARY', 4, u'легендарный спутник', cards_relations.RARITY.LEGENDARY) )
