import os
import re
import threading

import telebot
from telebot import types

import schedule
import time
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

from UserDatabase import UserDatabase
from UserLocations import UserLocations
from UserQueries import UserQueries
from NewsApiClient import NewsApiClient
from UserSubscriptions import UserSubscriptions

personal_cabinet_message_id = None

class NewsBot:
    def __init__(self, token, news_api_key):
        self.bot = telebot.TeleBot(token)
        self.news_api_client = NewsApiClient(news_api_key)
        self.user_db = UserDatabase()
        self.user_queries = UserQueries()
        self.user_subs = UserSubscriptions()
        self.user_locations = UserLocations()
        self.cache = {}
        self.user_states = {}
        self.scheduled_jobs_recommendation = {}
        self.scheduled_jobs_notification = {}
        self.language_codes = {
            'Arabic': 'ar',
            'German': 'de',
            'English': 'en',
            'Spanish': 'es',
            'French': 'fr',
            'Hebrew': 'he',
            'Italian': 'it',
            'Dutch': 'nl',
            'Norwegian': 'no',
            'Portuguese': 'pt',
            'Swedish': 'sv',
            'Urdu': 'ud',
            'Chinese': 'zh',
            "Don't choose": "dont!"
        }
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=['author'])
        def send_welcome(message):
            self.bot.reply_to(message, "Contact in telegram: https://t.me/muzyka_viktor")
        @self.bot.message_handler(commands=['help'])
        def send_help_message(message):
            help_text = (
                "Hello! This is a guide to using the bot.\n"
                "To get news:\n"
                "1. First, use the /start command to sign up.\n"
                "2. Select the news settings from the menu.\n"
                "3. Wait for the bot response and follow the instructions.\n"
                "To get recommendation:\n"
                "1. Select im main menu recommendation.\n"
                "2. Select include for get recommendation\n"
                "2.1 Select exclude for stop receive recommendation\n"
                "News subscriptions:\n"
                "- Add or unsubscribe to news topics through the 'News subscriptions' in menu.\n"
                "Setting up recommendations and subscriptions:\n"
                "- Set the time and period for receiving recommendations and news through the 'Settings' menu.\n"
                "- Available periods: daily, weekly, monthly.\n"
                "Additional commands:\n"
                "/help - display this help message.\n"
                "/author - display about author.\n"
            )
            self.bot.reply_to(message, help_text)
        @self.bot.message_handler(commands=['start'])
        def start(message):
            user_id = message.chat.id
            first_name = message.chat.first_name
            last_name = message.chat.last_name
            user_name = message.chat.username
            self.user_db.add_user(user_id, first_name, last_name, user_name)

            print("START!")

            global personal_cabinet_message_id

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("Personal Cabinet", callback_data="personal_cabinet"))
            markup.row(types.InlineKeyboardButton("News", callback_data="news"))
            markup.row(types.InlineKeyboardButton("Subscription", callback_data="subscription"))
            markup.row(types.InlineKeyboardButton("Personalized  recommendations", callback_data="personal_recommendation"))

            is_edited = False
            if personal_cabinet_message_id:
                try:
                    self.bot.edit_message_text(chat_id=message.chat.id, text="Choose an option:", message_id=personal_cabinet_message_id, reply_markup=markup)
                    is_edited = True
                except Exception as e:
                    print(e)

            if not is_edited:
                sent_message = self.bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id

        @self.bot.callback_query_handler(func=lambda call: call.data == "start")
        def start_callback(call):
            start(call.message)
            try:
                self.user_states.pop(call.from_user.id)
            except Exception as e:
                print(e)

        @self.bot.callback_query_handler(func=lambda call: call.data == "start_new")
        def start_callback(call):
            global personal_cabinet_message_id
            personal_cabinet_message_id = None
            start(call.message)
            try:
                self.user_states.pop(call.from_user.id)
            except Exception as e:
                print(e)

        @self.bot.callback_query_handler(func=lambda call: call.data == "personal_cabinet")
        def personal_cabinet_callback(call):
            print("personal_cabinet!")
            global personal_cabinet_message_id

            try:
                # get LANGUAGE
                user_id = call.from_user.id
                language_code = self.user_db.get_language_code(user_id)
                if language_code and language_code != "dont!":
                    language_name = {v: k for k, v in self.language_codes.items()}[language_code]
                    message_text = f"Your selected language for news headlines is: {language_name}.\n"
                else:
                    message_text = "You haven't selected any language yet.\n"
                # get NOTIFICATIONS TIME
                notify_time = self.user_db.get_notification_time(user_id)
                if notify_time != '':
                    message_text += f"Your Subscription Time is: {notify_time}.\n"
                else:
                    message_text += "You haven't selected Subscription Time yet.\n"
                # get NOTIFICATIONS PERIOD
                notify_period = self.user_db.get_notification_frequency(user_id)
                if notify_period != '':
                    message_text += f"Your Subscription Period is: {notify_period}.\n"
                else:
                    message_text += "You haven't selected Subscription Period yet.\n"
                # get RECOMENDATION TIME
                recommend_time = self.user_db.get_recommendation_time(user_id)
                if recommend_time != '':
                    message_text += f"Your Recommendation Time is: {recommend_time}."
                else:
                    message_text += "You haven't selected Recommendation Time yet."
            except Exception as e:
                print(e)
                self.bot.send_message("An error occurred while processing your request. Please try again.")

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("Change Language", callback_data="change_language"))
            markup.row(types.InlineKeyboardButton("Change Subscription Time", callback_data="change_notification_time"))
            markup.row(types.InlineKeyboardButton("Change Subscription Frequency", callback_data="change_notification_frequency"))
            markup.row(types.InlineKeyboardButton("Change Recommendation Time", callback_data="change_recommendation_time"))
            markup.row(types.InlineKeyboardButton("Back", callback_data="start"))

            is_edited = False
            if personal_cabinet_message_id:
                try:
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=personal_cabinet_message_id, text=message_text, reply_markup=markup)
                    is_edited = True
                except Exception as e:
                    print(e)

            if not is_edited:
                sent_message = self.bot.send_message(call.message.chat.id, text=message_text, reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id

        @self.bot.callback_query_handler(func=lambda call: call.data == "personal_cabinet_new")
        def start_callback(call):
            global personal_cabinet_message_id
            personal_cabinet_message_id = None
            personal_cabinet_callback(call)
            try:
                self.user_states.pop(call.from_user.id)
            except Exception as e:
                print(e)

        @self.bot.callback_query_handler(func=lambda call: call.data == "change_language")
        def change_language_callback(call):
            print("change_language!")
            global personal_cabinet_message_id
            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            for language_name in self.language_codes.keys():
                markup.add(types.InlineKeyboardButton(language_name, callback_data=f"select_language_{language_name}"))
            markup.add(types.InlineKeyboardButton("Back", callback_data="personal_cabinet"))
            message_text = "Choose a language to set for news headlines:"

            is_edited = False
            if personal_cabinet_message_id:
                try:
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=personal_cabinet_message_id, text=message_text, reply_markup=markup)
                    is_edited = True
                except Exception as e:
                    print(e)

            if not is_edited:
                sent_message = self.bot.send_message(call.message.chat.id, message_text, reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("select_language_"))
        def select_language_callback(call):
            print("select_language_!")
            user_id = call.from_user.id
            print(user_id)
            selected_language = call.data.split("_")[2]
            language_code = self.language_codes[selected_language]
            self.user_db.set_language_code(user_id, language_code)
            personal_cabinet_callback(call)

        @self.bot.callback_query_handler(func=lambda call: call.data == "change_notification_frequency")
        def change_notification_frequency_callback(call):
            global personal_cabinet_message_id

            user_id = call.from_user.id
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("Once a day", callback_data="notification_frequency_daily"))
            markup.row(types.InlineKeyboardButton("Once a week", callback_data="notification_frequency_weekly"))
            markup.row(types.InlineKeyboardButton("Once a month", callback_data="notification_frequency_monthly"))
            markup.row(types.InlineKeyboardButton("Back", callback_data="personal_cabinet"))

            is_edited = False
            if personal_cabinet_message_id:
                try:
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=personal_cabinet_message_id, text="Choose notification frequency:", reply_markup=markup)
                    is_edited = True
                except Exception as e:
                    print(e)

            if not is_edited:
                sent_message = self.bot.send_message(call.message.chat.id, text="Choose notification frequency:", reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("notification_frequency_"))
        def notification_frequency_callback(call):
            user_id = call.from_user.id
            try:
                frequency = call.data.split("_")[2]
                self.user_db.set_notification_frequency(user_id, frequency)
                self.bot.answer_callback_query(call.id, f"Subscription frequency set to {frequency}.")
            except Exception as e:
                print(e)
                self.bot.send_message(user_id, "An error occurred while processing your request. Please try again.")

        @self.bot.callback_query_handler(func=lambda call: call.data == "change_notification_time")
        def change_notification_time_callback(call):
            user_id = call.from_user.id
            try:
                self.user_states[user_id] = "waiting_for_subscription_time"
                self.bot.send_message(user_id, "Please enter the new subscription time in 24-hour format (e.g., 23:59):")
            except Exception as e:
                print(e)
                self.bot.send_message(user_id, "An error occurred while processing your request. Please try again.")

        @self.bot.callback_query_handler(func=lambda call: call.data == "change_recommendation_time")
        def change_recommendation_time_callback(call):
            user_id = call.from_user.id
            try:
                self.user_states[user_id] = "waiting_for_recommendation_time"
                self.bot.send_message(user_id, "Please enter the new recommendation time in 24-hour format (e.g., 23:59):")
            except Exception as e:
                print(e)
                self.bot.send_message(user_id, "An error occurred while processing your request. Please try again.")

        @self.bot.callback_query_handler(func=lambda call: call.data == "subscription")
        def subscription_callback(call):
            print("subscription!")
            global personal_cabinet_message_id
            user_id = call.from_user.id

            try:
                print("subscription!1")
                user_subscriptions = self.user_subs.get_user_subscriptions_with_id(user_id)
                num_subscriptions = len(user_subscriptions)
                message_text = f"You have {num_subscriptions}/5 subscriptions"
                print("subscription!2")
                markup = types.InlineKeyboardMarkup()
                for sub_id, topic in user_subscriptions:
                    markup.row(types.InlineKeyboardButton(f"{topic} ❌", callback_data=f"unsubscribe_{sub_id}_{topic}"))
                print("subscription!3")
                if num_subscriptions > 1:
                    markup.row(types.InlineKeyboardButton("Unsubscribe All ❌", callback_data="unsubscribe_all"))
                markup.row(types.InlineKeyboardButton("Add Topic", callback_data="add_topic"))
                markup.row(types.InlineKeyboardButton("Back", callback_data="start"))

                print("subscription!4")
                is_edited = False
                if personal_cabinet_message_id:
                    try:
                        self.bot.edit_message_text(chat_id=user_id, text=message_text, message_id=personal_cabinet_message_id, reply_markup=markup)
                        is_edited = True
                    except Exception as e:
                        print(e)

                if not is_edited:
                    sent_message = self.bot.send_message(user_id, "Choose an option:", reply_markup=markup)
                    personal_cabinet_message_id = sent_message.message_id

            except Exception as e:
                print(e)
                self.bot.send_message(user_id, "An error occurred while processing your request. Please try again.")

        @self.bot.callback_query_handler(func=lambda call: call.data == "add_topic")
        def add_topic_callback(call):
            user_id = call.from_user.id

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("Back", callback_data="subscription"))

            self.bot.send_message(user_id, "Enter the topic you want to subscribe:", reply_markup=markup)
            self.user_states[user_id] = "waiting_for_subs"

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("unsubscribe_"))
        def unsubscribe_callback(call):
            global personal_cabinet_message_id
            user_id = call.from_user.id
            try:
                parts = call.data.split("_")
                sub_id = parts[1]
                topic = "_".join(parts[2:])

                print(sub_id, topic)

                confirmation_message = f"Are you sure you want to unsubscribe from the topic '{topic}'? " \
                                       f"Click 'Yes' to confirm or 'No' to cancel."

                if sub_id == "all":
                    confirmation_message = f"Are you sure you want to unsubscribe from all topics? " \
                                           f"Click 'Yes' to confirm or 'No' to cancel."

                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("Yes", callback_data=f"confirm_unsubscribe_{sub_id}"))
                markup.row(types.InlineKeyboardButton("No", callback_data="cancel_unsubscribe"))
                markup.row(types.InlineKeyboardButton("Back", callback_data="subscription"))

                sent_message = self.bot.send_message(user_id, confirmation_message, reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id
            except Exception as e:
                print(e)
                self.bot.send_message(call.message.chat.id, "An error occurred while unsubscribing from the topic. Please try again.")

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_unsubscribe_"))
        def confirm_unsubscribe_callback(call):
            print("confirm_unsubscribe_callback")
            global personal_cabinet_message_id
            user_id = call.from_user.id
            try:
                sub_id = call.data.split("_", 2)[2]
                if sub_id == "all":
                    user_subscriptions = self.user_subs.get_user_subscriptions_with_id(user_id)
                    for sub_id, topic in user_subscriptions:
                        self.user_subs.unsubscribe_from_topic(sub_id)
                else:
                    self.user_subs.unsubscribe_from_topic(sub_id)
                self.bot.answer_callback_query(call.id, "Unsubscribe confirmed!")
            except Exception as e:
                print(e)
                self.bot.send_message(user_id, "An error occurred while processing your request. Please try again.")
            else:
                subscription_callback(call)

        @self.bot.callback_query_handler(func=lambda call: call.data == "cancel_unsubscribe")
        def cancel_unsubscribe_callback(call):
            global personal_cabinet_message_id
            user_id = call.from_user.id
            self.bot.answer_callback_query(call.id, "Unsubscription cancelled.")
            subscription_callback(call)

        @self.bot.callback_query_handler(func=lambda call: call.data == "personal_recommendation")
        def personal_recommendation_callback(call):
            print("personal_recommendation!")
            global personal_cabinet_message_id

            try:
                user_id = call.from_user.id
                recommendation = self.user_db.get_recommendation(user_id)
                print(recommendation)
                if recommendation == 1:
                    message_text = "Personalized recommendations included"
                else:
                    message_text = "Personal recommendations are not included"
            except Exception as e:
                print(e)
                self.bot.send_message("An error occurred while processing your request. Please try again.")

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("Include", callback_data="include_recommendations"))
            markup.row(types.InlineKeyboardButton("Exclude", callback_data="exclude_recommendations"))
            markup.row(types.InlineKeyboardButton("Back", callback_data="start"))

            is_edited = False
            if personal_cabinet_message_id:
                try:
                    self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=personal_cabinet_message_id, text=message_text, reply_markup=markup)
                    is_edited = True
                except Exception as e:
                    print(e)

            if not is_edited:
                sent_message = self.bot.send_message(call.message.chat.id, text=message_text, reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id

        @self.bot.callback_query_handler(func=lambda call: call.data == "include_recommendations")
        def include_recommendations_callback(call):
            print("include_recommendations!")
            user_id = call.from_user.id
            self.user_db.set_recommendation(user_id, 1)
            self.bot.answer_callback_query(call.id, "Personalized recommendations included")
            start(call.message)

        @self.bot.callback_query_handler(func=lambda call: call.data == "exclude_recommendations")
        def exclude_recommendations_callback(call):
            print("exclude_recommendations!")
            user_id = call.from_user.id
            self.user_db.set_recommendation(user_id, 0)
            self.bot.answer_callback_query(call.id, "Personalized recommendations excluded")
            start(call.message)

        @self.bot.callback_query_handler(func=lambda call: call.data == "news")
        def news_callback(call):
            global personal_cabinet_message_id

            user_id = call.from_user.id
            topic_message = "Enter topic or location to get local news:"

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("Back", callback_data="start"))

            is_edited = False
            if personal_cabinet_message_id:
                try:
                    sent_message = self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=personal_cabinet_message_id, text=topic_message, reply_markup=markup)
                    is_edited = True
                    self.user_states[user_id] = "waiting_for_news"
                except Exception as e:
                    print(e)

            if not is_edited:
                sent_message = self.bot.send_message(call.message.chat.id, topic_message, reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id
                self.user_states[user_id] = "waiting_for_news"

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('reaction_'))
        def handle_reaction_callback(call):
            user_id = call.from_user.id
            reaction, topic = call.data.split("|")

            message = self.user_queries.increase_reaction(user_id, topic, reaction)

            if message:
                self.bot.answer_callback_query(call.id, message)

            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

            new_markup = types.InlineKeyboardMarkup()
            new_markup.add(types.InlineKeyboardButton(text=f"Another news about {topic}", callback_data=f"more_news_{topic}"))
            new_markup.row(types.InlineKeyboardButton(text="Back to menu", callback_data="start_new"))
            self.bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=new_markup)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            try:
                if call.message:
                    user_id = call.from_user.id
                    topic = call.data.split('_')[2]  # Get theme from callback
                    self.process_news_results(user_id, topic, call.message, edit_message_id=call.message.message_id)
            except Exception as e:
                print(e)

        @self.bot.message_handler(func=lambda message: True, content_types=['text'])
        def handle_text_message(message):
            global personal_cabinet_message_id

            user_id = message.chat.id
            user_state = self.user_states.get(user_id)
            topic = message.text

            if topic == "News":
                news_callback(message)
            elif user_state == "waiting_for_subs":
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("Back", callback_data="subscription"))

                num_subscriptions = len(self.user_subs.get_user_subscriptions(user_id))
                if num_subscriptions >= 5:
                    sent_message = self.bot.send_message(user_id, "You have reached the maximum limit of subscriptions (5). You cannot subscribe to more topics.", reply_markup=markup)
                    personal_cabinet_message_id = sent_message.message_id
                    return

                subscription_result = self.user_subs.subscribe_to_topic(user_id, topic)
                sent_message = self.bot.send_message(user_id, subscription_result, reply_markup=markup)
                personal_cabinet_message_id = sent_message.message_id
            elif user_state == "waiting_for_news":
                print(message.text)
                topic = message.text
                if topic == "News":
                    news_callback(message)
                else:
                    self.process_news_results(user_id, topic, message)
            elif user_state == "waiting_for_recommendation_time":
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("Back", callback_data="personal_cabinet_new"))
                try:
                    recommendation_time = message.text.strip()
                    print(recommendation_time)

                    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', recommendation_time):
                        raise ValueError("Invalid time format. Please enter time in the format 'HH:MM'.")

                    self.user_db.set_recommendation_time(user_id, recommendation_time)
                    self.bot.send_message(user_id, "Recommendation time updated successfully.", reply_markup=markup)
                except Exception as e:
                    self.bot.send_message(user_id, f"Error: {str(e)}")
            elif user_state == "waiting_for_subscription_time":
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("Back", callback_data="personal_cabinet_new"))
                try:
                    notification_time = message.text.strip()
                    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', notification_time):
                        raise ValueError("Invalid time format. Please enter time in the format 'HH:MM'.")

                    self.user_db.set_notification_time(user_id, notification_time)
                    self.bot.send_message(user_id, "Subscription time updated successfully.", reply_markup=markup)
                except Exception as e:
                    self.bot.send_message(user_id, f"Error: {str(e)}")

        @self.bot.message_handler(func=lambda message: True, content_types=['location'])
        def handle_location(message):
            user_id = message.chat.id
            location_names = self.get_location_name(message.location.latitude, message.location.longitude)

            self.user_locations.add_location(user_id, round(message.location.latitude, 2), round(message.location.longitude, 2), location_names)

            location_parts = location_names.split(',')
            print(location_parts)
            for location_part in location_parts:
                print(location_part, len(location_part))
                if len(location_part) < 3:
                    continue
                if self.process_news_results(user_id, location_part, message, True):
                    return

    def get_location_name(self, latitude, longitude):
        geolocator = Nominatim(user_agent="my_geocoder")
        location = geolocator.reverse((latitude, longitude), language="en")
        address = location.address
        return address

    def process_news_results(self, user_id, topic, message, from_geo=False, edit_message_id=None):
        try:
            is_find_news = False
            lang_code = self.user_db.get_language_code(user_id)
            cache_key = (user_id, lang_code, topic)
            if cache_key in self.cache:
                news_results = self.cache[cache_key]
            else:
                news_results = self.news_api_client.get_news_by_topic(topic, self.user_db.get_language_code(user_id))
                self.cache[cache_key] = news_results
            # add search theme to db, for personalized recommendation
            self.user_queries.add_query(user_id, topic)

            message_text = "Not found, please try another topic."
            if len(news_results) > 1:
                message_text = f"{news_results[0]['title']}\n[{news_results[0]['url']}](news_results[0]['url'])"
                self.cache[cache_key] = news_results[1:]
            elif cache_key in self.cache:
                del self.cache[cache_key]

            markup = types.InlineKeyboardMarkup()

            if message_text != "Not found, please try another topic.":
                is_find_news = True
                markup.add(types.InlineKeyboardButton(text=f"Another news about {topic}", callback_data=f"more_news_{topic}"))

                heart_button = types.InlineKeyboardButton(text="❤", callback_data=f"reaction_heart|{topic}")
                like_button = types.InlineKeyboardButton(text="👍", callback_data=f"reaction_like|{topic}")
                dislike_button = types.InlineKeyboardButton(text="👎", callback_data=f"reaction_dislike|{topic}")
                markup.row(heart_button, like_button, dislike_button)

            markup.row(types.InlineKeyboardButton(text="Back to menu", callback_data="start_new"))

            if not is_find_news and from_geo:
                return False

            if edit_message_id:
                self.bot.edit_message_text(chat_id=message.chat.id, message_id=edit_message_id, text=message_text, reply_markup=markup, parse_mode='Markdown')
            else:
                self.bot.send_message(message.chat.id, message_text, reply_markup=markup, parse_mode='Markdown')

            return is_find_news
        except Exception as e:
            print(e)
            self.bot.send_message(message.chat.id, "An error occurred while processing your request. Please try changing the search topic or your news language.")
            return False


    def schedule_check_recommendation_and_subs(self):
        schedule.every().minute.do(self.check_recommendation_times)
        schedule.every().minute.do(self.check_subscription_times)

        while True:
            schedule.run_pending()
            time.sleep(1)
    ###### RECOMMENDATION FUNC
    def check_recommendation_times(self):
        user_recommendation_times = self.user_db.get_users_for_recommendation()

        for user_id, recommendation_time in user_recommendation_times:
            if user_id not in self.scheduled_jobs_recommendation or self.scheduled_jobs_recommendation[user_id] != recommendation_time:
                self.cancel_previous_job_recommendation(user_id)
                self.schedule_new_job_recommendation(user_id, recommendation_time)
    def cancel_previous_job_recommendation(self, user_id):
        if user_id in self.scheduled_jobs_recommendation:
            schedule.cancel_job(self.scheduled_jobs_recommendation[user_id])
    def schedule_new_job_recommendation(self, user_id, recommendation_time):
        job = schedule.every().day.at(recommendation_time).do(self.send_recommendations_for_user, user_id=user_id)
        self.scheduled_jobs_recommendation[user_id] = job

    def send_recommendations_for_user(self, user_id):
        current_date = datetime.now()
        previous_date = current_date - timedelta(days=1)
        formatted_date = previous_date.strftime("%Y-%m-%d")

        popular_queries = self.user_queries.get_popular_queries(user_id)
        message = ""

        for idx, query in enumerate(popular_queries, start=1):
            topic = query["theme"]
            news_results = self.news_api_client.get_news_by_topic(topic, self.user_db.get_language_code(user_id), formatted_date, 1)
            if news_results:
                recommended_news = news_results[0]
                message += f"{idx}. {recommended_news['title']}\n{recommended_news['url']}\n"

        if message != "":
            message = "Here are today's top recommendations based on your interests:\n" + message
            self.bot.send_message(user_id, text=message)
    ###### RECOMMENDATION FUNC

    ###### SUBSCRIPTION NEWS
    def check_subscription_times(self):
        user_notification_times = self.user_db.get_user_for_subscriptions()

        print(user_notification_times)

        for user_id, subscription_time, frequency in user_notification_times:
            if user_id not in self.scheduled_jobs_notification or self.scheduled_jobs_notification[user_id] != subscription_time or self.scheduled_jobs_notification[user_id] != frequency:
                self.cancel_previous_job_notification(user_id)
                self.schedule_new_job_notification(user_id, subscription_time, frequency)

    def cancel_previous_job_notification(self, user_id):
        if user_id in self.scheduled_jobs_notification:
            schedule.cancel_job(self.scheduled_jobs_notification[user_id])

    def schedule_new_job_notification(self, user_id, subscription_time, frequency):
        if frequency == "daily":
            job = schedule.every().day.at(subscription_time).do(self.send_notification_for_user, user_id=user_id)
        elif frequency == "weekly":
            job = schedule.every().week.at(subscription_time).do(self.send_notification_for_user, user_id=user_id)
        else:
            job = schedule.every().day.at(subscription_time).do(self.send_notification_for_user, user_id=user_id)
            job.interval = 30

        print(user_id, subscription_time, frequency)

        self.scheduled_jobs_notification[user_id] = job

    def send_notification_for_user(self, user_id):
        topics = self.user_subs.get_user_subscriptions(user_id)
        print("send_notification_for_user", topics, )
        current_date = datetime.now()

        news_date = current_date - timedelta(days=1)

        for topic in topics:
            news_results = self.news_api_client.get_news_by_topic(topic, self.user_db.get_language_code(user_id), news_date.strftime("%Y-%m-%d"), 3)

            if news_results:
                message = f"Here are the latest news updates{topic}:\n"
                for idx, news in enumerate(news_results, start=1):
                    message += f"{idx}. {news['title']}\n{news['url']}\n"

            self.bot.send_message(user_id, text=message)

    ###### SUBSCRIPTION NEWS
    def start_bot(self):
        schedule_thread_recomm = threading.Thread(target=self.schedule_check_recommendation_and_subs)
        schedule_thread_recomm.start()

        self.bot.infinity_polling()

    def run(self):
        self.start_bot()

if __name__ == "__main__":
    bot = NewsBot(os.getenv("TELEGRAM_API"), os.getenv("NEWS_API"))
    bot.run()