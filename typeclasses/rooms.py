"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
import random
from evennia import TICKER_HANDLER
from collections import defaultdict
from typeclasses.characters import Character


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
                users.append("|c%s|n" % key)
            else:
                things[key].append(con)
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        if desc:
            string += "%s" % desc
        if exits:
            string += "\n|wExits:|n " + list_to_string(exits)
        # this doesn't quite work yet
        if users:
            string += "\n|wStanding here is |n" + list_to_string(users)
        if things:
            thing_strings = []
            for key, itemlist in sorted(things.items()):
                nitem = len(itemlist)
                if nitem == 1:
                    key, _ = itemlist[0].get_numbered_name(nitem, looker, key=key)
                else:
                    key = [item.get_numbered_name(nitem, looker, key=key)[1] for item in itemlist][0]
                thing_strings.append(key)
            string += "\n|wYou see:|n " + list_to_string(thing_strings)
        return string

    def at_look(self, target, **kwargs):

        description = target.return_appearance(self, **kwargs)

        target.at_desc(looker=self, **kwargs)

        return description

    pass

# These are ambiance strings
AMBIENCE_STRINGS = (
    "Off in the distance, the sirens of a private police-force wail, rising and fading.",
    "The whine of an electric tool sounds from somewhere nearby, then the crunch of cutting metal.",
    "For a moment, you catch the smell of distant street-grils, thick and oily.",
    "The loud revs of aftermarket engines fill the air, echoed down concrete streets.",
    "An electric hum picks up, reaching a distinctly noticable level before fading back to nothing.",
    "You catch the acrid whiff of burning electronics, filtered in from somewhere else.",
    "Gunshots sound off in the distance. Just a few, then relative silence.",
    "Nearby, muffled shouting marks the start of a fight only a wall or two away.",
    "The sound of crunching, gurgling pipes interrupt the background noise here, but only for a few moments.",
)


class AmbientRoom(Room):
    """
    Here's a first pass at making a weather room.
    """

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
        if random.random() < 0.2:
            # only update 20 % of the time
            self.msg_contents("|w%s|n" % random.choice(AMBIENCE_STRINGS))
