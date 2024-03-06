from telebot.handler_backends import State, StatesGroup


class HighPriceStates(StatesGroup):
    # Just name variables differently
    city = State() # creating instances of State class is enough from now
    hotels = State()
    upper_limit = State()
    lower_limit = State()
    check_in_date = State()
    check_out_date = State()

class LowPriceStates(StatesGroup):
    # Just name variables differently
    city = State() # creating instances of State class is enough from now
    hotels = State()
    upper_limit = State()
    lower_limit = State()
    check_in_date = State()
    check_out_date = State()


class CustomPriceStates(StatesGroup):
    # Just name variables differently
    city = State() # creating instances of State class is enough from now
    hotels = State()
    upper_limit = State()
    lower_limit = State()
    check_in_date = State()
    check_out_date = State()