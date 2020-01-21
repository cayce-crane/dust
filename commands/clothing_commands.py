
"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia import default_cmds
from evennia.commands.default.muxcommand import MuxCommand
from typeclasses.clothing import  get_worn_clothes
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
      wear <obj> [wear style]
    Examples:
      wear shirt
      wear scarf wrapped loosely about the shoulders
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
            self.caller.msg("Usage: wear <obj> [wear style]")
            return
        clothing = self.caller.search(self.arglist[0], candidates=self.caller.contents)
        wearstyle = True
        if not clothing:
            self.caller.msg("Thing to wear must be in your inventory.")
            return
        if not clothing.is_typeclass("evennia.contrib.clothing.Clothing", exact=False):
            self.caller.msg("That's not clothes!")
            return

        # Enforce overall clothing limit.
        if CLOTHING_OVERALL_LIMIT and len(get_worn_clothes(self.caller)) >= CLOTHING_OVERALL_LIMIT:
            self.caller.msg("You can't wear any more clothes.")
            return

        # Apply individual clothing type limits.
        if clothing.db.clothing_type and not clothing.db.worn:
            type_count = single_type_count(get_worn_clothes(self.caller), clothing.db.clothing_type)
            if clothing.db.clothing_type in list(CLOTHING_TYPE_LIMIT.keys()):
                if type_count >= CLOTHING_TYPE_LIMIT[clothing.db.clothing_type]:
                    self.caller.msg(
                        "You can't wear any more clothes of the type '%s'."
                        % clothing.db.clothing_type
                    )
                    return

        if clothing.db.worn and len(self.arglist) == 1:
            self.caller.msg("You're already wearing %s!" % clothing.name)
            return
        if len(self.arglist) > 1:  # If wearstyle arguments given
            wearstyle_list = self.arglist  # Split arguments into a list of words
            del wearstyle_list[0]  # Leave first argument (the clothing item) out of the wearstyle
            wearstring = " ".join(
                str(e) for e in wearstyle_list
            )  # Join list of args back into one string
            if (
                    WEARSTYLE_MAXLENGTH and len(wearstring) > WEARSTYLE_MAXLENGTH
            ):  # If length of wearstyle exceeds limit
                self.caller.msg(
                    "Please keep your wear style message to less than %i characters."
                    % WEARSTYLE_MAXLENGTH
                )
            else:
                wearstyle = wearstring
        clothing.wear(self.caller, wearstyle)


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
        if clothing.db.covered_by:
            self.caller.msg("You have to take off %s first." % clothing.db.covered_by.name)
            return
        clothing.remove(self.caller)


class CmdCover(MuxCommand):
    """
    Covers a worn item of clothing with another you're holding or wearing.
    Usage:
        cover <obj> [with] <obj>
    When you cover a clothing item, it is hidden and no longer appears in
    your description until it's uncovered or the item covering it is removed.
    You can't remove an item of clothing if it's covered.
    """

    key = "cover"
    help_category = "clothing"

    def func(self):
        """
        This performs the actual command.
        """

        if len(self.arglist) < 2:
            self.caller.msg("Usage: cover <worn clothing> [with] <clothing object>")
            return
        # Get rid of optional 'with' syntax
        if self.arglist[1].lower() == "with" and len(self.arglist) > 2:
            del self.arglist[1]
        to_cover = self.caller.search(self.arglist[0], candidates=self.caller.contents)
        cover_with = self.caller.search(self.arglist[1], candidates=self.caller.contents)
        if not to_cover or not cover_with:
            return
        if not to_cover.is_typeclass("evennia.contrib.clothing.Clothing", exact=False):
            self.caller.msg("%s isn't clothes!" % to_cover.name)
            return
        if not cover_with.is_typeclass("evennia.contrib.clothing.Clothing", exact=False):
            self.caller.msg("%s isn't clothes!" % cover_with.name)
            return
        if cover_with.db.clothing_type:
            if cover_with.db.clothing_type in CLOTHING_TYPE_CANT_COVER_WITH:
                self.caller.msg("You can't cover anything with that!")
                return
        if not to_cover.db.worn:
            self.caller.msg("You're not wearing %s!" % to_cover.name)
            return
        if to_cover == cover_with:
            self.caller.msg("You can't cover an item with itself!")
            return
        if cover_with.db.covered_by:
            self.caller.msg("%s is covered by something else!" % cover_with.name)
            return
        if to_cover.db.covered_by:
            self.caller.msg(
                "%s is already covered by %s." % (cover_with.name, to_cover.db.covered_by.name)
            )
            return
        if not cover_with.db.worn:
            cover_with.wear(
                self.caller, True
            )  # Put on the item to cover with if it's not on already
        self.caller.location.msg_contents(
            "%s covers %s with %s." % (self.caller, to_cover.name, cover_with.name)
        )
        to_cover.db.covered_by = cover_with


class CmdUncover(MuxCommand):
    """
    Reveals a worn item of clothing that's currently covered up.
    Usage:
        uncover <obj>
    When you uncover an item of clothing, you allow it to appear in your
    description without having to take off the garment that's currently
    covering it. You can't uncover an item of clothing if the item covering
    it is also covered by something else.
    """

    key = "uncover"
    help_category = "clothing"

    def func(self):
        """
        This performs the actual command.
        """

        if not self.args:
            self.caller.msg("Usage: uncover <worn clothing object>")
            return

        to_uncover = self.caller.search(self.args, candidates=self.caller.contents)
        if not to_uncover:
            return
        if not to_uncover.db.worn:
            self.caller.msg("You're not wearing %s!" % to_uncover.name)
            return
        if not to_uncover.db.covered_by:
            self.caller.msg("%s isn't covered by anything!" % to_uncover.name)
            return
        covered_by = to_uncover.db.covered_by
        if covered_by.db.covered_by:
            self.caller.msg("%s is under too many layers to uncover." % to_uncover.name)
            return
        self.caller.location.msg_contents("%s uncovers %s." % (self.caller, to_uncover.name))
        to_uncover.db.covered_by = None


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

        # This part is new!
        # You can't drop clothing items that are covered.
        if obj.db.covered_by:
            caller.msg("You can't drop that because it's covered by %s." % obj.db.covered_by)
            return
        # Remove clothes if they're dropped.
        if obj.db.worn:
            obj.remove(caller, quiet=True)

        obj.move_to(caller.location, quiet=True)
        caller.msg("You drop %s." % (obj.name,))
        caller.location.msg_contents("%s drops %s." % (caller.name, obj.name), exclude=caller)
        # Call the object script's at_drop() method.
        obj.at_drop(caller)


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
        # This is new! Can't give away something that's worn.
        if to_give.db.covered_by:
            caller.msg(
                "You can't give that away because it's covered by %s." % to_give.db.covered_by
            )
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
        self.add(CmdCover())
        self.add(CmdUncover())
        self.add(CmdGive())
        self.add(CmdDrop())
        self.add(CmdInventory())

    pass

