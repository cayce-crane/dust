"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia import DefaultCharacter
from evennia.utils import list_to_string
from typeclasses.clothing import get_worn_clothes
from config.configlists import NAKEDS_LIST



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
        naked_dict = {naked: "" for naked in NAKEDS_LIST}
        self.attributes.add("nakeds", naked_dict)
        worn_dict = {naked: [] for naked in NAKEDS_LIST}
        self.attributes.add("worn", worn_dict)

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
        clothes_list = get_worn_clothes(self)
        # Append worn, uncovered clothing to the description
        #for garment in clothes_list:
        #    # If 'worn' is True, just append the name
        #    if garment.db.worn is True:
        #        worn_string_list.append(garment.name)
        #    # Otherwise, append the name and the string value of 'worn'
        #    elif garment.db.worn:
        #        worn_string_list.append("%s %s" % (garment.name, garment.db.worn))
        if desc:
            string += "%s" % desc

        worn = self.db.worn

        worn_set = set()

        for naked, clothing in worn.items():
            if len(clothing) != 0:
                worn_set.add(naked)

        naked_dict = self.db.nakeds
        for key, value in naked_dict.items():
            string += '\n' if (key == 'head' or key == 'left-shoulder' or key == 'groin') else ''
            string += worn[key][-1].db.messages['worn'] if key in worn_set else ('|W%s|n ' % value)
            # string += ('|W%s|n ' % value) if value else ''
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

