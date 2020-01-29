
from evennia import DefaultObject
from config.configlists import CLOTHING_MESSAGE_TYPES, NAKEDS_LIST


class Clothing(DefaultObject):

    def at_object_creation(self):
        if not self.db.messages:
            self.db.messages = {message: "" for message in CLOTHING_MESSAGE_TYPES}
        if not self.db.coverage:
            self.db.coverage = []
        if not self.db.seethru:
            self.db.seethru = False
        if not self.db.color:
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
        message = "%s %s " % (wearer, self.db.messages['owear'])
        wearer.msg("%s %s " % ("You", self.db.messages['wear']))
        wearer.location.msg_contents(message, exclude=wearer)

    def remove(self, wearer):
        """
        Removes worn clothes and optionally echoes to the room.
        Args:
            wearer (obj): character object wearing this clothing object
        """
        self.db.worn = False

        remove_message = "%s %s " % (wearer, self.db.messages['oremove'])
        wearer.msg("%s %s " % ("You", self.db.messages['remove']))
        wearer.location.msg_contents(remove_message, exclude=wearer)

    def at_get(self, getter):
        """
        Makes absolutely sure clothes aren't already set as 'worn'
        when they're picked up, in case they've somehow had their
        location changed without getting removed.
        """
        self.db.worn = False
