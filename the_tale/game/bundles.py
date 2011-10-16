# coding utf-8
from django_next.utils.decorators import nested_commit_on_success

from .angels.prototypes import get_angel_by_id

from .models import Bundle, BundleMember, BUNDLE_TYPE

def get_bundle_by_id(id):
    bundle = Bundle.objects.get(id=id)
    return get_bundle_by_model(model=bundle)

def get_bundle_by_model(model):
    return BundlePrototype(model=model)

class BundlePrototype(object):

    def __init__(self, model):
        self.model = model

        self.angels = {}
        self.heroes = {}
        self.actions = {}

        self.load_data()

    @property
    def id(self): return self.model.id

    @property
    def type(self): return self.model.type

    def get_owner(self): return self.model.owner
    def set_owner(self, value): self.model.owner = value
    owner = property(get_owner, set_owner)

    def add_hero(self, hero):
        self.heroes[hero.id] = hero
        for action in hero.get_actions():
            self.add_action(action)

    def add_action(self, action):
        action.set_bundle(self)
        self.actions[action.id] = action

    def remove_action(self, action):
        del self.actions[action.id]
        action.set_bundle(None)

    def load_data(self):

        for member in self.model.members.all():
            angel = get_angel_by_id(member.angel_id)
            self.angels[angel.id] = angel

            for hero in angel.heroes():
                self.add_hero(hero)
      
    @nested_commit_on_success
    def save_data(self):
        
        for angel in self.angels.values():
            angel.save()

        for hero in self.heroes.values():
            hero.save()

        for action in self.actions.values():
            # TODO: we should save non-leader actions after creating new action
            # if not action.leader:
            #     continue
            action.save()


    @classmethod
    @nested_commit_on_success
    def create(cls, angel):
        
        bundle = Bundle.objects.create(type=BUNDLE_TYPE.BASIC)
        member = BundleMember.objects.create(angel=angel.model)
        bundle.members.add(member)

        return BundlePrototype(model=bundle)

    @nested_commit_on_success
    def save(self):
        self.model.save()

    def process_turn(self, turn_number):
        next_turn = None

        for angel in self.angels.values():
            next = angel.process_turn(turn_number)
            if next_turn is None and next or next < next_turn:
                next_turn = next

        for hero in self.heroes.values():
            next = hero.process_turn(turn_number)
            if next_turn is None and next or next < next_turn:
                next_turn = next

        for action in self.actions.values():
            if not action.leader:
                continue
            next = action.process_turn(turn_number)
            if next_turn is None and next or next < next_turn:
                next_turn = next

        self.save_data()

        return next_turn
