
"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia import default_cmds
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import evtable
from config.configlists import CLOTHING_MESSAGE_TYPES, NAKEDS_LIST


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
            if len(worn[covered]) == 1:
                worn[covered] = []
            elif worn[covered]:
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


class CmdToggle(MuxCommand):
    """
    Toggle between a piece of clothing's two states.
    Usage:
        toggle <item>
    """

    key = "toggle"
    help_category = "clothing"

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("Need to provide an item to toggle")
            return

        clothing = self.caller.search(self.lhs, candidates=self.caller.contents)
        if not clothing:
            self.caller.msg("Item must be clothing")
            return
        if clothing.db.toggled:
            clothing.db.toggled = False
            caller.msg("%s %s " % ("You", clothing.db.messages['toggle2']))
            caller.location.msg_contents("%s %s" % (caller.name, clothing.db.messages['otoggle2']), exclude=caller)
        else:
            togglecoverage = clothing.db.togglecoverage
            oldcoverage = clothing.db.coverage
            for oldcovered in oldcoverage:
                if oldcovered in togglecoverage:
                    continue
                else: # old coverage is now no longer covered
                    caller.db.worn[oldcovered].remove(clothing)
            for newcovered in togglecoverage:
                if newcovered not in clothing.db.coverage:
                    caller.db.worn[newcovered].append(clothing)
            clothing.db.toggled = True
            caller.msg("%s %s" % ("You", clothing.db.messages['toggle1']))
            caller.location.msg_contents("%s %s" % (caller.name, clothing.db.messages['otoggle1']), exclude=caller)


class CmdSetWorn(MuxCommand):
    """
    Set the 'worn' message for an article of clothing
    Usage:
        @worn <clothing item> = <message>
    """

    key = '@worn'
    help_category = "tailoring"

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
                caller.msg("Worn message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetWear(MuxCommand):
    """
    Set the 'wear' message for an article of clothing
    Usage:
        @wear <clothing item> = <message>
    """

    key = '@wear'
    help_category = "tailoring"

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
                caller.msg("Wear message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetOwear(MuxCommand):
    """
    Set the 'owear' message for an article of clothing
    Usage:
        @owear <clothing item> = <message>
    """

    key = '@owear'
    help_category = "tailoring"

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
                caller.msg("owear message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetRemove(MuxCommand):
    """
    Set the 'remove' message for an article of clothing
    Usage:
        @remove <clothing item> = <message>
    """

    key = '@remove'
    help_category = "tailoring"

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
                caller.msg("Remove message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetOremove(MuxCommand):
    """
    Set the 'oremove' message for an article of clothing
    Usage:
        @oremove <clothing item> = <message>
    """

    key = '@oremove'
    help_category = "tailoring"

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
                caller.msg("oremove message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetTease(MuxCommand):
    """
    Set the 'tease' message for an article of clothing
    Usage:
        @tease <clothing item> = <message>
    """

    key = '@tease'
    help_category = "tailoring"

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
                clothing.db.messages['tease'] = self.rhs
                caller.msg("tease message for %s set." % clothing.name)


class CmdSetOtease(MuxCommand):
    """
    Set the 'otease' message for an article of clothing
    Usage:
        @otease <clothing item> = <message>
    """

    key = '@otease'
    help_category = "tailoring"

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
                clothing.db.messages['otease'] = self.rhs
                caller.msg("otease message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetToggle1(MuxCommand):
    """
    Set the 'toggle1' message for an article of clothing
    Usage:
        @toggle1 <clothing item> = <message>
    """

    key = '@toggle1'
    help_category = "tailoring"

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
                clothing.db.messages['toggle1'] = self.rhs
                caller.msg("toggle1 message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetToggle2(MuxCommand):
    """
    Set the 'toggle2' message for an article of clothing
    Usage:
        @toggle2 <clothing item> = <message>
    """

    key = '@toggle2'
    help_category = "tailoring"

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
                clothing.db.messages['toggle2'] = self.rhs
                caller.msg("toggle2 message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetOtoggle1(MuxCommand):
    """
    Set the 'otoggle1' message for an article of clothing
    Usage:
        @otoggle1 <clothing item> = <message>
    """

    key = '@otoggle1'
    help_category = "tailoring"

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
                clothing.db.messages['otoggle1'] = self.rhs
                caller.msg("otoggle1 message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetOtoggle2(MuxCommand):
    """
    Set the 'otoggle2' message for an article of clothing
    Usage:
        @otoggle2 <clothing item> = <message>
    """

    key = '@otoggle2'
    help_category = "tailoring"

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
                clothing.db.messages['otoggle2'] = self.rhs
                caller.msg("otoggle2 message for %s set as: %s" % (clothing.name, self.rhs))


class CmdSetWornToggled(MuxCommand):
    """
    Set the 'worntoggled' message for an article of clothing
    Usage:
        @worntoggled <clothing item> = <message>
    """

    key = '@worntoggled'
    help_category = "tailoring"

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
                clothing.db.messages['worntoggled'] = self.rhs
                caller.msg("worntoggled message for %s set as: %s" % (clothing.name, self.rhs))


class CmdCoveragePlus(MuxCommand):
    """
    Add a naked covered by a piece of clothing.
    Usage:
        @coverage+ <clothing item> = <naked>
    """

    key = "@coverage+"
    help_category = "tailoring"

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
                if self.rhs not in NAKEDS_LIST:
                    self.caller.msg("%s is not a naked area. " % self.rhs)
                    return
                clothing.db.coverage.append(self.rhs.strip().lower())
                caller.msg("Added coverage %s for %s" % (self.rhs, clothing.name))


class CmdCoverageMinus(MuxCommand):
    """
    Remove a naked covered by a piece of clothing.
    Usage:
        @coverage- <clothing item> = <naked>
    """

    key = "@coverage-"
    help_category = "tailoring"

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
                if self.rhs not in NAKEDS_LIST:
                    self.caller.msg("%s is not a naked area. " % self.rhs)
                    return
                clothing.db.coverage.remove(self.rhs.strip().lower())
                caller.msg("Remove coverage %s for %s" % (self.rhs, clothing.name))



class CmdToggleCoveragePlus(MuxCommand):
    """
    Add a naked covered by a piece of clothing when it's otggled.
    Usage:
        @togglecov+ <clothing item> = <naked>
    """

    key = "@togglecov+"
    help_category = "tailoring"

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
                if self.rhs not in NAKEDS_LIST:
                    self.caller.msg("%s is not a naked area. " % self.rhs)
                    return
                clothing.db.togglecoverage.append(self.rhs.strip().lower())
                caller.msg("Added toggle coverage %s for %s" % (self.rhs, clothing.name))


class CmdToggleCoverageMinus(MuxCommand):
    """
    Remove a naked covered by a piece of clothing when it's toggled.
    Usage:
        @togglecov- <clothing item> = <naked>
    """

    key = "@togglecov-"
    help_category = "tailoring"

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
                if self.rhs not in NAKEDS_LIST:
                    self.caller.msg("%s is not a naked area. " % self.rhs)
                    return
                clothing.db.togglecoverage.remove(self.rhs.strip().lower())
                caller.msg("Remove toggled coverage %s for %s" % (self.rhs, clothing.name))


class CmdMessages(MuxCommand):
    """
    Show the existing messages for an article of clothing.
    Usage:
        @messages <clothing item>
    """

    key = "@messages"
    help_category = "tailoring"

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("Need to provide the article of clothing to view messages for.")
            return
        clothing = self.caller.search(self.args, candidates=self.caller.contents)
        if not clothing:
            self.caller.msg("Thing to view messages for must be clothing.")
            return
        message_string = ""
        for message_name, message in clothing.db.messages.items():
            message_string += "%s: %s\n" % (message_name, message)
        caller.msg("Messages for %s:\n%s" % (clothing.name, message_string))


class CmdGive(MuxCommand):
    """
    Give away something to someone
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
        self.add(CmdSetToggle1())
        self.add(CmdSetToggle2())
        self.add(CmdSetOtoggle1())
        self.add(CmdSetOtoggle2())
        self.add(CmdSetWornToggled())
        self.add(CmdCoveragePlus())
        self.add(CmdCoverageMinus())
        self.add(CmdToggleCoveragePlus())
        self.add(CmdToggleCoverageMinus())
        self.add(CmdSetTease())
        self.add(CmdSetOtease())
        self.add(CmdMessages())
        self.add(CmdToggle())

    pass

