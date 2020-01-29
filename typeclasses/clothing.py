
from evennia import DefaultObject
from evennia.utils import list_to_string
from config.configlists import CLOTHING_MESSAGE_TYPES, NAKEDS_LIST


# HELPER FUNCTIONS START HERE

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
        if thing.db.worn:
            clothes_list.append(thing)
    return clothes_list


class Clothing(DefaultObject):

    def at_object_creation(self):
        self.db.messages = {message: "" for message in CLOTHING_MESSAGE_TYPES}
        self.db.coverage = []
        self.db.seethru = False
        self.db.color = ""

    def wear(self, wearer):
        """
        Sets clothes to 'worn' and echoes to the room.
        Args:
            wearer (obj): character object wearing this clothing object
        """
        # Set clothing as worn
        self.db.worn = True

        covered_list = [naked for naked in self.db.coverage]
        for covered in covered_list:
            wearer.db.worn[covered].append(self)

        # Echo a message to the room
        message = "%s %s" % (wearer, self.attributes.get(messages)['owear'])
        wearer.msg("%s" % self.db.messages['wear'])
        wearer.location.msg_contents(message + ".")

    def remove(self, wearer):
        """
        Removes worn clothes and optionally echoes to the room.
        Args:
            wearer (obj): character object wearing this clothing object
        """
        self.db.worn = False

        remove_message = "%s %s." % (wearer, self.attributes.get(message)['oremove'])
        wearer.msg("%s" % self.db.messages['remove'])
        wearer.location.msg_contents(remove_message)

    def at_get(self, getter):
        """
        Makes absolutely sure clothes aren't already set as 'worn'
        when they're picked up, in case they've somehow had their
        location changed without getting removed.
        """
        self.db.worn = False
