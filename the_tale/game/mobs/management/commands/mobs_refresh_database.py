# coding: utf-8
import os
import pymorphy

from django.core.management.base import BaseCommand

from dext.utils import s11n

from ...models import MobConstructor
from ...conf import mobs_settings

from ....heroes.habilities import ABILITIES
from ....artifacts.models import ArtifactConstructor
from ....map.places.models import TERRAIN_STR_2_ID

from ....textgen.templates import Dictionary
from ....textgen.words import WordBase
from ....textgen.logic import get_tech_vocabulary
from ....textgen.conf import textgen_settings

morph = pymorphy.get_morph(textgen_settings.PYMORPHY_DICTS_DIRECTORY)


class Command(BaseCommand):

    help = 'load mobs fixtures into database'

    def handle(self, *args, **options):

        dictionary = Dictionary()
        dictionary.load()
        tech_vocabulary = get_tech_vocabulary()

        MobConstructor.objects.all().delete()
        
        for filename in os.listdir(mobs_settings.DEFS_DIRECTORY):

            if not filename.endswith('.json'):
                continue

            def_path = os.path.join(mobs_settings.DEFS_DIRECTORY, filename)

            if not os.path.isfile(def_path):
                continue

            with open(def_path) as f:
                data = s11n.from_json(f.read())

                uuid = filename[:-5]

                print 'load %s' % uuid

                # check abilities
                for ability in data['abilities']:
                    if ability not in ABILITIES:
                        raise Exception('unknown ability id: "%s"' % ability)

                # check loot
                for loot_priority, item_uuid in data['loot_list']:
                    if not ArtifactConstructor.objects.filter(uuid=item_uuid).exists():
                        raise Exception('unknown loot id: "%s"' % item_uuid)

                word = WordBase.create_from_string(morph, data['normalized_name'], tech_vocabulary)
                dictionary.add_word(word)
                    
                MobConstructor.objects.create( uuid=uuid,
                                               name=data['name'],
                                               normalized_name=data['normalized_name'],
                                               health_relative_to_hero=data['health_relative_to_hero'],
                                               initiative=data['initiative'],
                                               power_per_level=data['power_per_level'],
                                               damage_dispersion=data['damage_dispersion'],
                                               terrain=TERRAIN_STR_2_ID[data['terrain']],
                                               abilities=s11n.to_json(data['abilities']),
                                               loot_list=s11n.to_json(data['loot_list']) )

        dictionary.save()
