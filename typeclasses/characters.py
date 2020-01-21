"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia import DefaultCharacter
from evennia import default_cmds
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import list_to_string
from evennia.utils import evtable

# Options start here.
# Maximum character length of 'wear style' strings, or None for unlimited.
WEARSTYLE_MAXLENGTH = 50

# The rest of these options have to do with clothing types. Clothing types are optional,
# but can be used to give better control over how different items of clothing behave. You
# can freely add, remove, or change clothing types to suit the needs of your game and use
# the options below to affect their behavior.

# The order in which clothing types appear on the description. Untyped clothing or clothing
# with a type not given in this list goes last.
CLOTHING_TYPE_ORDER = [
    "hat",
    "jewelry",
    "top",
    "undershirt",
    "gloves",
    "fullbody",
    "bottom",
    "underpants",
    "socks",
    "shoes",
    "accessory",
]
# The maximum number of each type of clothes that can be worn. Unlimited if untyped or not specified.
CLOTHING_TYPE_LIMIT = {"hat": 1, "gloves": 1, "socks": 1, "shoes": 1}
# The maximum number of clothing items that can be worn, or None for unlimited.
CLOTHING_OVERALL_LIMIT = 20
# What types of clothes will automatically cover what other types of clothes when worn.
# Note that clothing only gets auto-covered if it's already worn when you put something
# on that auto-covers it - for example, it's perfectly possible to have your underpants
# showing if you put them on after your pants!
CLOTHING_TYPE_AUTOCOVER = {
    "top": ["undershirt"],
    "bottom": ["underpants"],
    "fullbody": ["undershirt", "underpants"],
    "shoes": ["socks"],
}
# Types of clothes that can't be used to cover other clothes.
CLOTHING_TYPE_CANT_COVER_WITH = ["jewelry"]


# HELPER FUNCTIONS START HERE


def order_clothes_list(clothes_list):
    """
    Orders a given clothes list by the order specified in CLOTHING_TYPE_ORDER.
    Args:
        clothes_list (list): List of clothing items to put in order
    Returns:
        ordered_clothes_list (list): The same list as passed, but re-ordered
                                     according to the hierarchy of clothing types
                                     specified in CLOTHING_TYPE_ORDER.
    """
    ordered_clothes_list = clothes_list
    # For each type of clothing that exists...
    for current_type in reversed(CLOTHING_TYPE_ORDER):
        # Check each item in the given clothes list.
        for clothes in clothes_list:
            # If the item has a clothing type...
            if clothes.db.clothing_type:
                item_type = clothes.db.clothing_type
                # And the clothing type matches the current type...
                if item_type == current_type:
                    # Move it to the front of the list!
                    ordered_clothes_list.remove(clothes)
                    ordered_clothes_list.insert(0, clothes)
    return ordered_clothes_list


def get_worn_clothes(character, exclude_covered=False):
    """
    Get a list of clothes worn by a given character.
    Args:
        character (obj): The character to get a list of worn clothes from.
    Kwargs:
        exclude_covered (bool): If True, excludes clothes covered by other
                                clothing from the returned list.
    Returns:
        ordered_clothes_list (list): A list of clothing items worn by the
                                     given character, ordered according to
                                     the CLOTHING_TYPE_ORDER option specified
                                     in this module.
    """
    clothes_list = []
    for thing in character.contents:
        # If uncovered or not excluding covered items
        if not thing.db.covered_by or exclude_covered is False:
            # If 'worn' is True, add to the list
            if thing.db.worn:
                clothes_list.append(thing)
    # Might as well put them in order here too.
    ordered_clothes_list = order_clothes_list(clothes_list)
    return ordered_clothes_list


def clothing_type_count(clothes_list):
    """
    Returns a dictionary of the number of each clothing type
    in a given list of clothing objects.
    Args:
        clothes_list (list): A list of clothing items from which
                             to count the number of clothing types
                             represented among them.
    Returns:
        types_count (dict): A dictionary of clothing types represented
                            in the given list and the number of each
                            clothing type represented.
    """
    types_count = {}
    for garment in clothes_list:
        if garment.db.clothing_type:
            type = garment.db.clothing_type
            if type not in list(types_count.keys()):
                types_count[type] = 1
            else:
                types_count[type] += 1
    return types_count


def single_type_count(clothes_list, type):
    """
    Returns an integer value of the number of a given type of clothing in a list.
    Args:
        clothes_list (list): List of clothing objects to count from
        type (str): Clothing type to count
    Returns:
        type_count (int): Number of garments of the specified type in the given
                          list of clothing objects
    """
    type_count = 0
    for garment in clothes_list:
        if garment.db.clothing_type:
            if garment.db.clothing_type == type:
                type_count += 1
    return type_count


class Clothing(DefaultObject):
    def wear(self, wearer, wearstyle, quiet=False):
        """
        Sets clothes to 'worn' and optionally echoes to the room.
        Args:
            wearer (obj): character object wearing this clothing object
            wearstyle (True or str): string describing the style of wear or True for none
        Kwargs:
            quiet (bool): If false, does not message the room
        Notes:
            Optionally sets db.worn with a 'wearstyle' that appends a short passage to
            the end of the name  of the clothing to describe how it's worn that shows
            up in the wearer's desc - I.E. 'around his neck' or 'tied loosely around
            her waist'. If db.worn is set to 'True' then just the name will be shown.
        """
        # Set clothing as worn
        self.db.worn = wearstyle
        # Auto-cover appropirate clothing types, as specified above
        to_cover = []
        if self.db.clothing_type and self.db.clothing_type in CLOTHING_TYPE_AUTOCOVER:
            for garment in get_worn_clothes(wearer):
                if (
                        garment.db.clothing_type
                        and garment.db.clothing_type in CLOTHING_TYPE_AUTOCOVER[self.db.clothing_type]
                ):
                    to_cover.append(garment)
                    garment.db.covered_by = self
        # Return if quiet
        if quiet:
            return
        # Echo a message to the room
        message = "%s puts on %s" % (wearer, self.name)
        if wearstyle is not True:
            message = "%s wears %s %s" % (wearer, self.name, wearstyle)
        if to_cover:
            message = message + ", covering %s" % list_to_string(to_cover)
        wearer.location.msg_contents(message + ".")

    def remove(self, wearer, quiet=False):
        """
        Removes worn clothes and optionally echoes to the room.
        Args:
            wearer (obj): character object wearing this clothing object
        Kwargs:
            quiet (bool): If false, does not message the room
        """
        self.db.worn = False
        remove_message = "%s removes %s." % (wearer, self.name)
        uncovered_list = []

        # Check to see if any other clothes are covered by this object.
        for thing in wearer.contents:
            # If anything is covered by
            if thing.db.covered_by == self:
                thing.db.covered_by = False
                uncovered_list.append(thing.name)
        if len(uncovered_list) > 0:
            remove_message = "%s removes %s, revealing %s." % (
                wearer,
                self.name,
                list_to_string(uncovered_list),
            )
        # Echo a message to the room
        if not quiet:
            wearer.location.msg_contents(remove_message)

    def at_get(self, getter):
        """
        Makes absolutely sure clothes aren't already set as 'worn'
        when they're picked up, in case they've somehow had their
        location changed without getting removed.
        """
        self.db.worn = False


class Character(DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """
    def at_object_creation(self):
        self.attributes.add("idlepose", "is standing here.")
        naked_dict = {"head":"", "left-eye":"", "right-eye":"", "face":"", "neck":"", "left-shoulder":"",
                      "right-shoulder":"", "chest":"", "back":"", "left-upperarm":"", "right-upperarm":"",
                      "left-forearm":"", "right-forearm":"", "left-hand":"", "right-hand":"", "abdomen":"", "groin":"",
                      "butt":"", "left-thigh":"", "right-thigh":"", "left-calf":"", "right-calf":"",
                      "left-foot":"", "right-foot":""}
        self.attributes.add("nakeds", naked_dict)

    def return_appearance(self, looker):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        Args:
            looker (Object): Object doing the looking.
        Notes:
            The name of every clothing item carried and worn by the character
            is appended to their description. If the clothing's db.worn value
            is set to True, only the name is appended, but if the value is a
            string, the string is appended to the end of the name, to allow
            characters to specify how clothing is worn.
        """
        if not looker:
            return ""
        # get description, build string
        string = "|c%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        worn_string_list = []
        clothes_list = get_worn_clothes(self, exclude_covered=True)
        # Append worn, uncovered clothing to the description
        for garment in clothes_list:
            # If 'worn' is True, just append the name
            if garment.db.worn is True:
                worn_string_list.append(garment.name)
            # Otherwise, append the name and the string value of 'worn'
            elif garment.db.worn:
                worn_string_list.append("%s %s" % (garment.name, garment.db.worn))
        if desc:
            string += "%s\n" % desc
        # Append nakeds
        # TODO cover if clothes worn
        if self.db.nakeds:
            naked_dict = self.db.nakeds
            for key, value in naked_dict.items():
                string += '\n\n' if key == 'groin' else ''
                string += value if value else ''
        # Append worn clothes.
        if worn_string_list:
            string += "|/|/%s is wearing %s." % (self, list_to_string(worn_string_list))
        else:
            string += "|/|/%s is not wearing anything." % self
        return string

    def at_post_puppet(self, **kwargs):
        self.msg("\nYou become |c%s|n.\n" % self.name)
        self.msg(self.at_look(self.location))

        def message(obj, from_obj):
            obj.msg("%s blinks their eyes." % self.get_display_name(obj), from_obj=from_obj)
        self.location.for_contents(message, exclude=[self], from_obj=self)

    def at_post_unpuppet(self, account, session=None, **kwargs):

        if not self.sessions.count():
            if self.location:
                def message(obj, from_obj):
                    obj.msg("%s falls to the ground, unconscious." % self.get_display_name(obj), from_obj=from_obj)
                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location

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
            self.caller.msg("%s is under too many layers to uncover." % (to_uncover.name))
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
