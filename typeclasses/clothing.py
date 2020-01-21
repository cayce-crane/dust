


# Options start here.


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
