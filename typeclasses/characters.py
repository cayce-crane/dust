"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia import DefaultCharacter
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
        if not self.attributes.has("idlepose"):
            self.attributes.add("idlepose", "is standing here.")
        if not self.attributes.has("temp_idlepose"):
            self.attributes.add("temp_idlepose", "is standing here.")
        if not self.attributes.has("sleep_idlepose"):
            self.attributes.add("sleep_idlepose", "is sleeping here.")
        if not self.attributes.has("nakeds"):
            naked_dict = {naked: "" for naked in NAKEDS_LIST}
            self.attributes.add("nakeds", naked_dict)
        if not self.attributes.has("worn"):
            worn_dict = {naked: [] for naked in NAKEDS_LIST}
            self.attributes.add("worn", worn_dict)
        if not self.attributes.has('skintone'):
            self.attributes.add('skintone', '|n')

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
        if desc:
            string += "%s" % desc

        worn = self.db.worn

        worn_set = set()
        shown_set = set()

        # TODO DUST-58
        skintone = self.db.skintone if self.attributes.has("skintone") else "|W" #TODO DELETE THIS NEPHEW...

        for naked, clothing in worn.items():
            if len(clothing) != 0:
                worn_set.add(naked)
        naked_dict = self.db.nakeds
        for naked_name, naked_value in naked_dict.items():
            # Possible I'm breaking this with the expanded check for empty string
            string += '\n\n' if ((naked_name == 'head'
                                 or naked_name == 'left-shoulder'
                                 or naked_name == 'groin') and naked_value != '') else ''
            if naked_name in worn_set:
                # What in god's name was I doing with this
                # update: it appears the second index is to get the packed db object itself but there
                # absolutely has got to be a better way
                if worn[naked_name][-1].attributes.get("toggled"):
                    clothing_item_string = worn[naked_name][-1].attributes.get("messages")['worntoggled']
                else:
                    clothing_item_string = worn[naked_name][-1].attributes.get("messages")['worn']
                # I do not understand why we need this
                # in fact I'm almost certain we can axe this
                # like we never do anything but add these to it
                # I feel like it had/has to do with layering?
                if not worn[naked_name][-1] in shown_set:
                    string += ('%s ' % clothing_item_string)
                    shown_set.add(worn[naked_name][-1])
                if worn[naked_name][-1].attributes.get("seethru"):
                    string += ('%s%s|n ' % (skintone, naked_value))
            else:
                string += ('%s%s|n ' % (skintone, naked_value))
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

    def at_after_move(self, source_location):

        if self.attributes.has('temp_idlepose'):
            self.db.temp_idlepose = ""

        if self.location.access(self, "view"):
            self.msg(self.at_look(self.location))
