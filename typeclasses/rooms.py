"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
import random
from evennia import TICKER_HANDLER
from collections import defaultdict
from typeclasses.characters import Character
from config.configlists import DIRGE_INDOOR_AMBIENCE_STRINGS


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    def return_appearance(self, looker, **kwargs):
        if not looker:
            return ""
        visible = (con for con in self.contents if con != looker and con.access(looker, "view"))
        exits, users, things = [], [], defaultdict(list)
        for con in visible:
            key = con.get_display_name(looker)
            if con.destination:
                exits.append(key)
            elif con.is_typeclass(Character):
                users.append("|c%s|n %s" % (key, con.db.idlepose))
            else:
                things[key].append(con)
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        if desc:
            string += "%s" % desc
        if users:
            string += "\n|n" + ' '.join(users)
        if things:
            thing_strings = []
            for key, itemlist in sorted(things.items()):
                nitem = len(itemlist)
                if nitem == 1:
                    key, _ = itemlist[0].get_numbered_name(nitem, looker, key=key)
                else:
                    key = [item.get_numbered_name(nitem, looker, key=key)[1] for item in itemlist][0]
                thing_strings.append(key)
            string += "\n|wYou see:|n " + ', '.join(thing_strings)
        if exits:
            string += "\n|wExits:|n " + ', '.join(exits)
        return string

    def at_look(self, target, **kwargs):

        description = target.return_appearance(self, **kwargs)

        target.at_desc(looker=self, **kwargs)

        return description

    pass


class AmbientRoom(Room):
    """
    Here's a first pass at making a weather room.
    """
    def __init__(self):
        self.ambient_strings = []

    def at_object_creation(self):
        super().at_object_creation()
        # subscribe ourselves to a ticker to repeatedly call the hook
        # "update_weather" on this object.
        self.db.interval = random.randint(50, 70)
        TICKER_HANDLER.add(
            interval=self.db.interval, callback=self.update_ambience
        )

    def update_ambience(self, *args, **kwargs):
        """
        Called by the tickerhandler at regular intervals. Even so, we
        only update 20% of the time, picking a random weather message
        when we do. The tickerhandler requires that this hook accepts
        any arguments and keyword arguments (hence the *args, **kwargs
        even though we don't actually use them in this example)
        """
        if random.random() < 0.005:
            self.msg_contents("|w%s|n" % random.choice(self.ambient_strings))


class DirgeIndoorAmbientRoom(AmbientRoom):

    def __init__(self):
        self.ambient_strings = DIRGE_INDOOR_AMBIENCE_STRINGS

