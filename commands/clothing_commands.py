
"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia import default_cmds
from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.clothing import get_worn_clothes
from evennia.utils import evtable


# Maximum character length of 'wear style' strings, or None for unlimited.
WEARSTYLE_MAXLENGTH = 50
# The maximum number of each type of clothes that can be worn. Unlimited if untyped or not specified.
CLOTHING_TYPE_LIMIT = {"hat": 1, "gloves": 1, "socks": 1, "shoes": 1}
# The maximum number of clothing items that can be worn, or None for unlimited.
CLOTHING_OVERALL_LIMIT = 20
# Types of clothes that can't be used to cover other clothes.
CLOTHING_TYPE_CANT_COVER_WITH = ["jewelry"]


class CmdWear(MuxCommand):
    """
    Puts on an item of clothing you are holding.
    Usage:
      wear <obj>
    Examples:
      wear shirt
    All the clothes you are wearing are appended to your description.
    If you provide a 'wear style' after the command, the message you
    provide will be displayed after the clothing's name.
    """

    key = "wear"
    help_category = "clothing"

    def func(self):
        """
        This performs the actual command.
        """
        if not self.args:
            self.caller.msg("Usage: wear <obj>")
            return
        clothing = self.caller.search(self.arglist[0], candidates=self.caller.contents)
        if not clothing:
            self.caller.msg("Thing to wear must be in your inventory.")
            return
        if not clothing.is_typeclass("typeclasses.clothing.Clothing", exact=False):
            self.caller.msg("That's not clothes!")
            return
        if clothing.db.worn and len(self.arglist) == 1:
            self.caller.msg("You're already wearing %s!" % clothing.name)
            return
        clothing.wear(self.caller)


class CmdRemove(MuxCommand):
    """
    Takes off an item of clothing.
    Usage:
       remove <obj>
    Removes an item of clothing you are wearing. You can't remove
    clothes that are covered up by something else - you must take
    off the covering item first.
    """

    key = "remove"
    help_category = "clothing"

    def func(self):
        """
        This performs the actual command.
        """
        clothing = self.caller.search(self.args, candidates=self.caller.contents)
        if not clothing:
            self.caller.msg("Thing to remove must be carried or worn.")
            return
        if not clothing.db.worn:
            self.caller.msg("You're not wearing that!")
            return
        for covered in clothing.db.coverage:
            worn = self.caller.db.worn
            if worn[covered] and worn[covered][-1] != clothing:
                self.caller.msg("You need to remove %s first." % worn[covered][-1].name)
                return
        for covered in clothing.db.coverage:
            worn = self.caller.db.worn
            worn[covered].pop()
        clothing.remove(self.caller)


class CmdDrop(MuxCommand):
    """
    drop something
    Usage:
      drop <obj>
    Lets you drop an object from your inventory into the
    location you are currently in.
    """

    key = "drop"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """Implement command"""

        caller = self.caller
        if not self.args:
            caller.msg("Drop what?")
            return

        # Because the DROP command by definition looks for items
        # in inventory, call the search function using location = caller
        obj = caller.search(
            self.args,
            location=caller,
            nofound_string="You aren't carrying %s." % self.args,
            multimatch_string="You carry more than one %s:" % self.args,
        )
        if not obj:
            return

        # Remove clothes if they're dropped.
        if obj.db.worn:
            obj.remove(caller, quiet=True)

        obj.move_to(caller.location, quiet=True)
        caller.msg("You drop %s." % (obj.name,))
        caller.location.msg_contents("%s drops %s." % (caller.name, obj.name), exclude=caller)
        # Call the object script's at_drop() method.
        obj.at_drop(caller)


class CmdSetWorn(MuxCommand):

    key = '@worn'

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("Need to provide item and message.")
            return

        if self.lhs:
            clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not clothing:
                self.caller.msg("Thing to set message for must be carried or worn.")
                return
            if self.rhs:
                clothing.db.messages['worn'] = self.rhs
                caller.msg("Worn message for %s set." % clothing.name)


class CmdSetWear(MuxCommand):

    key = '@wear'

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("Need to provide item and message.")
            return

        if self.lhs:
            clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not clothing:
                self.caller.msg("Thing to set message for must be carried or worn.")
                return
            if self.rhs:
                clothing.db.messages['wear'] = self.rhs
                caller.msg("Wear message for %s set." % clothing.name)


class CmdSetOwear(MuxCommand):

    key = '@owear'

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("Need to provide item and message.")
            return

        if self.lhs:
            clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not clothing:
                self.caller.msg("Thing to set message for must be carried or worn.")
                return
            if self.rhs:
                clothing.db.messages['owear'] = self.rhs
                caller.msg("owear message for %s set." % clothing.name)


class CmdSetRemove(MuxCommand):

    key = '@remove'

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("Need to provide item and message.")
            return

        if self.lhs:
            clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not clothing:
                self.caller.msg("Thing to set message for must be carried or worn.")
                return
            if self.rhs:
                clothing.db.messages['remove'] = self.rhs
                caller.msg("Remove message for %s set." % clothing.name)


class CmdSetOremove(MuxCommand):

    key = '@oremove'

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("Need to provide item and message.")
            return

        if self.lhs:
            clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not clothing:
                self.caller.msg("Thing to set message for must be carried or worn.")
                return
            if self.rhs:
                clothing.db.messages['oremove'] = self.rhs
                caller.msg("oremove message for %s set." % clothing.name)


class CmdCoveragePlus(MuxCommand):

    key = "@coverage+"

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("need to provide item and coverage")
            return
        if self.lhs:
            clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not clothing:
                self.caller.msg("thing to add coverage to must be carried")
                return
            if self.rhs:
                clothing.db.coverage.append(self.rhs.strip().lower())
                caller.msg("Added coverage %s for %s" % (self.rhs, clothing.name))


class CmdCoverageMinus(MuxCommand):

    key = "@coverage-"

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("need to provide item and coverage")
            return
        if self.lhs:
            clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
            if not clothing:
                self.caller.msg("thing to remove coverage to must be carried")
                return
            if self.rhs:
                clothing.db.coverage.remove(self.rhs.strip().lower())
                caller.msg("Remove coverage %s for %s" % (self.rhs, clothing.name))




class CmdGive(MuxCommand):
    """
    give away something to someone
    Usage:
      give <inventory obj> = <target>
    Gives an items from your inventory to another character,
    placing it in their inventory.
    """

    key = "give"
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """Implement give"""

        caller = self.caller
        if not self.args or not self.rhs:
            caller.msg("Usage: give <inventory object> = <target>")
            return
        to_give = caller.search(
            self.lhs,
            location=caller,
            nofound_string="You aren't carrying %s." % self.lhs,
            multimatch_string="You carry more than one %s:" % self.lhs,
        )
        target = caller.search(self.rhs)
        if not (to_give and target):
            return
        if target == caller:
            caller.msg("You keep %s to yourself." % to_give.key)
            return
        if not to_give.location == caller:
            caller.msg("You are not holding %s." % to_give.key)
            return
        # Remove clothes if they're given.
        if to_give.db.worn:
            to_give.remove(caller)
        to_give.move_to(caller.location, quiet=True)
        # give object
        caller.msg("You give %s to %s." % (to_give.key, target.key))
        to_give.move_to(target, quiet=True)
        target.msg("%s gives you %s." % (caller.key, to_give.key))
        # Call the object script's at_give() method.
        to_give.at_give(caller, target)


class CmdInventory(MuxCommand):
    """
    view inventory
    Usage:
      inventory
      inv
    Shows your inventory.
    """

    # Alternate version of the inventory command which separates
    # worn and carried items.

    key = "inventory"
    aliases = ["inv", "i"]
    locks = "cmd:all()"
    arg_regex = r"$"

    def func(self):
        """check inventory"""
        if not self.caller.contents:
            self.caller.msg("You are not carrying or wearing anything.")
            return

        items = self.caller.contents

        carry_table = evtable.EvTable(border="header")
        wear_table = evtable.EvTable(border="header")
        for item in items:
            if not item.db.worn:
                carry_table.add_row("|C%s|n" % item.name, item.db.desc or "")
        if carry_table.nrows == 0:
            carry_table.add_row("|CNothing.|n", "")
        string = "|wYou are carrying:\n%s" % carry_table
        for item in items:
            if item.db.worn:
                wear_table.add_row("|C%s|n" % item.name, item.db.desc or "")
        if wear_table.nrows == 0:
            wear_table.add_row("|CNothing.|n", "")
        string += "|/|wYou are wearing:\n%s" % wear_table
        self.caller.msg(string)


class ClothedCharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    Command set for clothing, including new versions of 'give' and 'drop'
    that take worn and covered clothing into account, as well as a new
    version of 'inventory' that differentiates between carried and worn
    items.
    """

    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super().at_cmdset_creation()
        #
        # any commands you add below will overload the default ones.
        #
        self.add(CmdWear())
        self.add(CmdRemove())
        self.add(CmdGive())
        self.add(CmdDrop())
        self.add(CmdInventory())
        self.add(CmdSetWorn())
        self.add(CmdSetWear())
        self.add(CmdSetOwear())
        self.add(CmdSetRemove())
        self.add(CmdSetOremove())
        self.add(CmdCoveragePlus())

    pass

