from telebot import types
from io import BytesIO
import re
from html import escape
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from loader import  bot
from storage import user_data, WhatsApp, COMPETITIONS
from registration import end_registration, performance_time, city, number_of_participants, exit_registration, music_file
from keyboards import competition_menu, contact_menu, competition_1_menu,back_to_info_menu, back_to_competition_menu, bid_menu, back_to_competition1_menu, apply_menu, request_navigation, contact_menu1, contact_menu2, faq_menu, faq_page_menu
from database import get_user_requests, get_participants, get_all_requests, get_all_users_requests, all_count, all_participants, requests_status, request_time, get_connection, search_requests, search_request_by_participant, get_request_by_id, delete_request, update_request_status, get_all_faq, get_faq_by_id, add_faq, update_faq, delete_faq, get_all_telegram_ids, get_all_admins, is_admin, add_admin, delete_admin, search_request_by_id, search_request_by_email, search_request_by_whatsapp, search_request_by_participant,get_admin_name
from admin_keyboards import admin_requests_menu_menu, admin_request_navigation, admin_requests_menu, admin_stats_menu, admin_status_menu, admin_faq_menu, admin_competitions_menu, admin_search_menu, admins_func_menu


