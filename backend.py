import string
import random
from datetime import datetime
from collections import OrderedDict
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Settings
RANDOM_LENGTH = 20
EMOJI_PEOPLE = u"\U0001f465"
SESSION_EXPIRY = 1  # In hours
POLL_EXPIRY = 720

# State types
NONE = "none"
TITLE = "title"
OPTION = "option"

PUBLISH = "publish"
DELETE = "delete"
BACK = "back"

creators = set()
all_sessions = dict()
all_polls = dict()


class Session(object):
    def __init__(self, uid: str) -> None:
        self.uid = uid
        self.state = TITLE
        self.poll = Poll(uid)
        self.start_date = datetime.now()
        self.expiry = SESSION_EXPIRY

    def get_state(self) -> str:
        return self.state

    def set_state(self, state: str) -> None:
        self.state = state

    def get_poll(self) -> Poll:
        return self.poll

    def get_start_date(self) -> datetime:
        return self.start_date

    def get_expiry(self) -> int:
        return self.expiry

    def set_expiry(self, expiry: int) -> None:
        self.expiry = expiry


class Poll(object):
    def __init__(self, uid: str, expiry=POLL_EXPIRY) -> None:
        self.creator_id = uid
        self.poll_id = uid + create_random_string(RANDOM_LENGTH)
        self.title = ""
        self.options = []
        self.created_date = datetime.now()
        self.expiry = expiry

    def get_title(self) -> str:
        return self.title

    def set_title(self, title: str) -> None:
        self.title = title

    def get_options(self) -> list:
        return self.options

    def add_option(self, option) -> void:
        self.options.append(option)

    def get_created_date(self) -> datetime:
        return self.created_date

    def get_expiry(self) -> int:
        return self.expiry

    def set_expiry(self, expiry: int) -> None:
        self.expiry = expiry

    @staticmethod
    def toggle(poll_id: str, opt_id: int, uid: str, user_profile: dict):
        poll = all_polls.get(poll_id, None)
        if not poll:
            return None, "Sorry, this pole has been deleted."
        if opt_id >= len(poll.get_options()):
            return None, "Sorry, invalid option."
        status = poll.get_options()[opt_id].toggle(uid, user_profile)
        return poll, status

    def build_option_buttons(self, is_admin=False) -> InlineKeyboardMarkup:
        buttons = []
        for i, option in enumerate(self.options):
            option_data = f"{self.poll_id} {i}"
            option_button = InlineKeyboardButton(option.title, callback_data=option_data)
            buttons.append([option_button])
        if is_admin:
            back_data = f"{self.poll_id} {BACK}"
            back_button = InlineKeyboardButton("Back", callback_data=back_data)
            buttons.append([back_button])
        return InlineKeyboardMarkup(buttons)


class Option(object):
    def __init__(self, title: str, is_comment_required: bool) -> None:
        self.title = title
        self.comment_required = is_comment_required
        self.respondents = OrderedDict()

    def comment_required(self) -> bool:
        return self.comment_required

    def toggle(self, uid: str, user_profile: dict) -> str:
        if uid in self.respondents:
            self.respondents.pop(uid, None)
            action = "removed from"
        else:
            self.respondents[uid] = user_profile.get("first_name", ""), user_profile.get("last_name", "")
            action = "added to"
        return f"You are {action} {self.title}!"

    def generate_namelist(self) -> str:
        return "\n".join(f"{first_name} {last_name}" for first_name, last_name in self.respondents.values())

    def render_text(self) -> str:
        title = make_html_bold(self.title)
        if self.respondents:
            title += f" ({len(self.respondents)}{EMOJI_PEOPLE})"
        namelist = strip_html_symbols(self.generate_namelist())
        return f"{title}\n{namelist}"


def to_id_string(uid: int) -> str:
    return str(uid).zfill(64)


def start_new_session(uid: int) -> None:
    uid = to_id_string(uid)
    all_sessions[uid] = Session(uid)


def create_random_string(n: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def strip_html_symbols(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_html_bold(text):
    return f"<b>{strip_html_symbols(text)}</b>"


def make_html_bold_first_line(text):
    text_split = text.split("\n", 1)
    output = make_html_bold(text_split[0])
    return output + "\n" + strip_html_symbols(text_split[1]) if len(text_split) > 1 else output
