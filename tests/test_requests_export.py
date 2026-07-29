import importlib
import os
import re
import sys
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from openpyxl import load_workbook


os.environ.setdefault("TOKEN", "123456:TEST")
sys.modules.setdefault("psycopg2", SimpleNamespace(connect=Mock()))
requests_callbacks = importlib.import_module("callbacks.requests_callbacks")
database = importlib.import_module("database")


def callback(data):
    return SimpleNamespace(
        id="callback-id",
        data=data,
        message=SimpleNamespace(
            chat=SimpleNamespace(id=100),
            message_id=55,
            text=""
        )
    )


def export_request(**overrides):
    data = {
        "id": 10,
        "telegram_id": 777,
        "city": "Москва",
        "name_team": "Команда",
        "number_name": "Номер",
        "number_genre": "Вокал",
        "number_of_participants": 2,
        "age": "10-14",
        "performance_time": 3,
        "SFP_supervisor": "Руководитель",
        "WhatsApp_number": "+79990000000",
        "email": "team@example.com",
        "status": "На рассмотрении",
        "create_at": "2026-07-29 12:00",
        "music_file_id": "file-id",
        "music_file_name": "music.mp3",
        "competition_id": 7,
        "competition_name": "ArtFlow",
        "participants": ["Анна", "Иван"],
    }
    data.update(overrides)
    return data


def competitions(count):
    return [
        {"id": index, "name": f"Конкурс {index}", "requests_count": index % 3}
        for index in range(1, count + 1)
    ]


def button_list(markup):
    return [button for row in markup.keyboard for button in row]


def button_map(markup):
    return {button.callback_data: button.text for button in button_list(markup)}


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.execute_calls = []
        self.closed = False

    def execute(self, sql, params=()):
        self.execute_calls.append((sql, params))

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


class RequestsExportTest(unittest.TestCase):
    def test_admin_choice_request_shows_competition_picker_without_creating_file(self):
        items = competitions(2)

        with patch.object(requests_callbacks.bot, "answer_callback_query"):
            with patch.object(requests_callbacks, "admin_check", return_value=True):
                with patch.object(requests_callbacks, "get_competitions_for_requests_export", return_value=items) as get_competitions:
                    with patch.object(requests_callbacks, "create_requests_excel") as create_excel:
                        with patch.object(requests_callbacks.bot, "edit_message_text") as edit_message:
                            requests_callbacks.requests_callback_message(callback("admin_choice_request"))

        get_competitions.assert_called_once_with()
        create_excel.assert_not_called()
        self.assertIn("Выберите конкурс", edit_message.call_args.args[0])
        buttons = button_map(edit_message.call_args.kwargs["reply_markup"])
        self.assertIn("admin_export_competition_1", buttons)
        self.assertIn("admin_export_competition_2", buttons)
        self.assertIn("admin_export_all", buttons)
        self.assertIn("back_to_admin_info", buttons)

    def test_export_menu_has_maximum_eight_competitions_per_page(self):
        markup = requests_callbacks.admin_export_competitions_menu(competitions(10), 1)
        competition_buttons = [button for button in button_list(markup) if button.callback_data.startswith("admin_export_competition_")]

        self.assertEqual(len(competition_buttons), 8)
        self.assertEqual(competition_buttons[0].callback_data, "admin_export_competition_1")
        self.assertEqual(competition_buttons[-1].callback_data, "admin_export_competition_8")

    def test_export_menu_has_all_and_back_buttons(self):
        buttons = button_map(requests_callbacks.admin_export_competitions_menu(competitions(3), 1))

        self.assertEqual(buttons["admin_export_all"], "📚 Все конкурсы")
        self.assertEqual(buttons["back_to_admin_info"], "🔙 Назад")

    def test_export_menu_has_page_navigation(self):
        buttons = button_list(requests_callbacks.admin_export_competitions_menu(competitions(10), 1))
        callbacks = [button.callback_data for button in buttons]
        page_labels = [button.text for button in buttons if button.text.startswith("Страница")]

        self.assertIn("admin_export_page_2", callbacks)
        self.assertEqual(page_labels, ["Страница 1/2"])

    def test_last_export_page_works(self):
        buttons = button_list(requests_callbacks.admin_export_competitions_menu(competitions(10), 2))
        callbacks = [button.callback_data for button in buttons]
        page_labels = [button.text for button in buttons if button.text.startswith("Страница")]

        self.assertIn("admin_export_competition_9", callbacks)
        self.assertIn("admin_export_competition_10", callbacks)
        self.assertIn("admin_export_page_1", callbacks)
        self.assertEqual(page_labels, ["Страница 2/2"])

    def test_invalid_export_page_is_handled_safely(self):
        items = competitions(10)

        with patch.object(requests_callbacks.bot, "answer_callback_query"):
            with patch.object(requests_callbacks, "admin_check", return_value=True):
                with patch.object(requests_callbacks, "get_competitions_for_requests_export", return_value=items):
                    with patch.object(requests_callbacks.bot, "edit_message_text") as edit_message:
                        requests_callbacks.requests_callback_message(callback("admin_export_page_bad"))

        self.assertIn("Страница 1/2", edit_message.call_args.args[0])

    def test_competition_callback_contains_only_id(self):
        item = {"id": 7, "name": "ArtFlow dangerous name", "requests_count": 1}
        buttons = button_list(requests_callbacks.admin_export_competitions_menu([item], 1))
        callbacks = [button.callback_data for button in buttons if button.callback_data.startswith("admin_export_competition_")]

        self.assertEqual(callbacks, ["admin_export_competition_7"])
        self.assertTrue(re.match(r"^admin_export_competition_\d+$", callbacks[0]))

    def test_export_all_gets_competition_id_none(self):
        rows = [export_request(), export_request(id=11, competition_id=8, competition_name="Other")]
        excel_file = BytesIO(b"fake")
        excel_file.name = "artflow_requests_all.xlsx"

        with patch.object(requests_callbacks.bot, "answer_callback_query"):
            with patch.object(requests_callbacks, "admin_check", return_value=True):
                with patch.object(requests_callbacks, "get_requests_for_excel", return_value=rows) as get_export:
                    with patch.object(requests_callbacks, "create_requests_excel", return_value=excel_file) as create_excel:
                        with patch.object(requests_callbacks.bot, "send_document") as send_document:
                            requests_callbacks.requests_callback_message(callback("admin_export_all"))

        get_export.assert_called_once_with(None)
        create_excel.assert_called_once_with(rows, None)
        self.assertEqual(send_document.call_args.args[1].name, "artflow_requests_all.xlsx")
        self.assertIn("Количество заявок: 2", send_document.call_args.kwargs["caption"])

    def test_export_all_workbook_contains_requests_from_different_competitions(self):
        excel_file = requests_callbacks.create_requests_excel([
            export_request(id=1, competition_id=7, competition_name="ArtFlow"),
            export_request(id=2, competition_id=8, competition_name="Other"),
        ])

        workbook = load_workbook(excel_file)
        sheet = workbook.active
        self.assertEqual(excel_file.name, "artflow_requests_all.xlsx")
        self.assertEqual(sheet["B2"].value, 7)
        self.assertEqual(sheet["C2"].value, "ArtFlow")
        self.assertEqual(sheet["B3"].value, 8)
        self.assertEqual(sheet["C3"].value, "Other")

    def test_selected_export_gets_selected_competition_id(self):
        rows = [export_request(competition_id=7, competition_name="ArtFlow")]
        excel_file = BytesIO(b"fake")
        excel_file.name = "artflow_requests_competition_7.xlsx"

        with patch.object(requests_callbacks.bot, "answer_callback_query"):
            with patch.object(requests_callbacks, "admin_check", return_value=True):
                with patch.object(requests_callbacks, "get_competition_by_id", return_value={"title": "ArtFlow"}) as get_competition:
                    with patch.object(requests_callbacks, "get_requests_for_excel", return_value=rows) as get_export:
                        with patch.object(requests_callbacks, "create_requests_excel", return_value=excel_file) as create_excel:
                            with patch.object(requests_callbacks.bot, "send_document") as send_document:
                                requests_callbacks.requests_callback_message(callback("admin_export_competition_7"))

        get_competition.assert_called_once_with("competition_7")
        get_export.assert_called_once_with(7)
        create_excel.assert_called_once_with(rows, 7)
        self.assertEqual(send_document.call_args.args[1].name, "artflow_requests_competition_7.xlsx")
        self.assertIn("ArtFlow", send_document.call_args.kwargs["caption"])

    def test_selected_export_workbook_contains_provided_selected_requests(self):
        excel_file = requests_callbacks.create_requests_excel([export_request(competition_id=7)], 7)

        workbook = load_workbook(excel_file)
        sheet = workbook.active
        self.assertEqual(excel_file.name, "artflow_requests_competition_7.xlsx")
        self.assertEqual(sheet["B2"].value, 7)
        self.assertEqual(sheet["R2"].value, "Анна\nИван")

    def test_competition_without_requests_does_not_create_file(self):
        with patch.object(requests_callbacks, "get_competition_by_id", return_value={"title": "Empty"}):
            with patch.object(requests_callbacks, "get_requests_for_excel", return_value=[]):
                with patch.object(requests_callbacks, "create_requests_excel") as create_excel:
                    with patch.object(requests_callbacks.bot, "send_message") as send_message:
                        requests_callbacks.send_requests_excel(callback("admin_export_competition_7"), 7)

        create_excel.assert_not_called()
        self.assertIn("пока нет заявок", send_message.call_args.args[1])

    def test_all_empty_export_does_not_create_file(self):
        with patch.object(requests_callbacks, "get_requests_for_excel", return_value=[]):
            with patch.object(requests_callbacks, "create_requests_excel") as create_excel:
                with patch.object(requests_callbacks.bot, "send_message") as send_message:
                    requests_callbacks.send_requests_excel(callback("admin_export_all"))

        create_excel.assert_not_called()
        self.assertIn("Заявок пока нет", send_message.call_args.args[1])

    def test_excel_layer_does_not_call_database(self):
        with patch.object(requests_callbacks, "get_requests_for_excel") as get_export:
            excel_file = requests_callbacks.create_requests_excel([export_request()], 7)

        get_export.assert_not_called()
        self.assertEqual(excel_file.name, "artflow_requests_competition_7.xlsx")

    def test_database_layer_executes_one_query(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with patch.object(database, "get_connection", return_value=connection):
            result = database.get_requests_for_excel(7)

        self.assertEqual(result, [])
        self.assertEqual(len(cursor.execute_calls), 1)
        self.assertTrue(cursor.closed)
        self.assertTrue(connection.closed)
        self.assertEqual(cursor.execute_calls[0][1], (7,))

    def test_database_layer_uses_bulk_participants(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with patch.object(database, "get_connection", return_value=connection):
            database.get_requests_for_excel()

        sql = cursor.execute_calls[0][0]
        self.assertIn("LEFT JOIN participants", sql)
        self.assertIn("array_agg", sql)
        self.assertNotIn("get_participants", sql)

    def test_database_layer_keeps_stable_sorting(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with patch.object(database, "get_connection", return_value=connection):
            database.get_requests_for_excel()

        self.assertIn("ORDER BY b.create_at ASC, b.id ASC", cursor.execute_calls[0][0])

    def test_formula_like_strings_are_sanitized(self):
        self.assertEqual(requests_callbacks.sanitize_excel_cell("=HYPERLINK(\"x\")"), "'=HYPERLINK(\"x\")")
        self.assertEqual(requests_callbacks.sanitize_excel_cell("+SUM(1,2)"), "'+SUM(1,2)")
        self.assertEqual(requests_callbacks.sanitize_excel_cell("-1+1"), "'-1+1")
        self.assertEqual(requests_callbacks.sanitize_excel_cell("@SUM(1,2)"), "'@SUM(1,2)")
        self.assertEqual(requests_callbacks.sanitize_excel_cell("   =SUM(1,2)"), "'   =SUM(1,2)")
        self.assertEqual(requests_callbacks.sanitize_excel_cell("\t=SUM(1,2)"), "'\t=SUM(1,2)")

    def test_safe_string_and_negative_number_are_not_changed(self):
        self.assertEqual(requests_callbacks.sanitize_excel_cell("обычный дефис - внутри"), "обычный дефис - внутри")
        self.assertEqual(requests_callbacks.sanitize_excel_cell(-1), -1)

    def test_excel_cells_are_sanitized(self):
        excel_file = requests_callbacks.create_requests_excel([
            export_request(
                competition_name="=HYPERLINK(\"x\")",
                city=" +SUM(1,2)",
                name_team="@SUM(1,2)",
                number_name="-1+1",
                participants=["=BAD()"],
                performance_time=-1,
            )
        ])

        workbook = load_workbook(excel_file)
        sheet = workbook.active
        self.assertEqual(sheet["C2"].value, "'=HYPERLINK(\"x\")")
        self.assertEqual(sheet["E2"].value, "' +SUM(1,2)")
        self.assertEqual(sheet["F2"].value, "'@SUM(1,2)")
        self.assertEqual(sheet["G2"].value, "'-1+1")
        self.assertEqual(sheet["K2"].value, -1)
        self.assertEqual(sheet["R2"].value, "'=BAD()")

    def test_filenames_are_stable(self):
        self.assertEqual(requests_callbacks.requests_excel_filename(7), "artflow_requests_competition_7.xlsx")
        self.assertEqual(requests_callbacks.requests_excel_filename(), "artflow_requests_all.xlsx")

    def test_caption_contains_count_and_cleans_competition_name(self):
        caption = requests_callbacks.build_export_caption(3, {"title": "Art\r\nFlow"})

        self.assertIn("Количество заявок: 3", caption)
        self.assertIn("Art Flow", caption)
        self.assertNotIn("\r", caption)
        self.assertNotIn("\nFlow", caption)

    def test_caption_escapes_html_tags_in_competition_name(self):
        caption = requests_callbacks.build_export_caption(1, {"title": "<b>Конкурс</b>"})

        self.assertIn("&lt;b&gt;Конкурс&lt;/b&gt;", caption)
        self.assertNotIn("<b>Конкурс</b>", caption)

    def test_empty_export_message_escapes_html_tags_in_competition_name(self):
        message = requests_callbacks.empty_export_message({"title": "</script><b>test</b>"})

        self.assertIn("&lt;/script&gt;&lt;b&gt;test&lt;/b&gt;", message)
        self.assertNotIn("</script><b>test</b>", message)

    def test_competition_name_with_ampersand_is_escaped(self):
        caption = requests_callbacks.build_export_caption(2, {"title": "Вокал & танец"})
        message = requests_callbacks.empty_export_message({"title": "Вокал & танец"})

        self.assertIn("Вокал &amp; танец", caption)
        self.assertIn("Вокал &amp; танец", message)

    def test_competition_name_with_angle_brackets_does_not_break_caption(self):
        caption = requests_callbacks.build_export_caption(2, {"title": "A < B > C"})

        self.assertIn("A &lt; B &gt; C", caption)
        self.assertNotIn("A < B > C", caption)
    def test_competition_name_with_quote_is_escaped(self):
        caption = requests_callbacks.build_export_caption(2, {"title": "Конкурс \"Весна\""})

        self.assertIn("Конкурс &quot;Весна&quot;", caption)
        self.assertNotIn("Конкурс \"Весна\"", caption)

    def test_plain_competition_name_stays_readable_in_caption(self):
        caption = requests_callbacks.build_export_caption(2, {"title": "ArtFlow"})

        self.assertIn("🏆 ArtFlow", caption)

    def test_filename_still_does_not_use_competition_name(self):
        excel_file = requests_callbacks.create_requests_excel([
            export_request(competition_name="<b>Конкурс</b>")
        ], 7)

        self.assertEqual(excel_file.name, "artflow_requests_competition_7.xlsx")
        self.assertNotIn("Конкурс", excel_file.name)

    def test_excel_file_closes_after_successful_send(self):
        excel_file = BytesIO(b"fake")
        excel_file.name = "artflow_requests_all.xlsx"

        def send_document(chat_id, document, caption=None):
            self.assertFalse(document.closed)

        with patch.object(requests_callbacks, "get_requests_for_excel", return_value=[export_request()]):
            with patch.object(requests_callbacks, "create_requests_excel", return_value=excel_file):
                with patch.object(requests_callbacks.bot, "send_document", side_effect=send_document) as send_document_mock:
                    requests_callbacks.send_requests_excel(callback("admin_export_all"))

        send_document_mock.assert_called_once()
        self.assertTrue(excel_file.closed)

    def test_excel_file_closes_when_send_document_fails_and_error_message_stays(self):
        excel_file = BytesIO(b"fake")
        excel_file.name = "artflow_requests_all.xlsx"

        def send_document(chat_id, document, caption=None):
            self.assertFalse(document.closed)
            raise RuntimeError("telegram failed")

        with patch.object(requests_callbacks, "get_requests_for_excel", return_value=[export_request()]):
            with patch.object(requests_callbacks, "create_requests_excel", return_value=excel_file):
                with patch.object(requests_callbacks.bot, "send_document", side_effect=send_document) as send_document_mock:
                    with patch.object(requests_callbacks.bot, "send_message") as send_message:
                        with self.assertLogs(requests_callbacks.logger, level="ERROR"):
                            requests_callbacks.send_requests_excel(callback("admin_export_all"))

        send_document_mock.assert_called_once()
        self.assertTrue(excel_file.closed)
        self.assertIn("Не удалось создать Excel-файл", send_message.call_args.args[1])
    def test_workbook_error_is_handled(self):
        with patch.object(requests_callbacks, "get_requests_for_excel", return_value=[export_request()]):
            with patch.object(requests_callbacks, "create_requests_excel", side_effect=RuntimeError("workbook failed")):
                with patch.object(requests_callbacks.bot, "send_message") as send_message:
                    with self.assertLogs(requests_callbacks.logger, level="ERROR"):
                        requests_callbacks.send_requests_excel(callback("admin_export_all"))

        self.assertIn("Не удалось создать Excel-файл", send_message.call_args.args[1])

    def test_send_document_error_is_handled(self):
        excel_file = BytesIO(b"fake")
        excel_file.name = "artflow_requests_all.xlsx"

        with patch.object(requests_callbacks, "get_requests_for_excel", return_value=[export_request()]):
            with patch.object(requests_callbacks, "create_requests_excel", return_value=excel_file):
                with patch.object(requests_callbacks.bot, "send_document", side_effect=RuntimeError("telegram failed")):
                    with patch.object(requests_callbacks.bot, "send_message") as send_message:
                        with self.assertLogs(requests_callbacks.logger, level="ERROR"):
                            requests_callbacks.send_requests_excel(callback("admin_export_all"))

        self.assertIn("Не удалось создать Excel-файл", send_message.call_args.args[1])

    def test_regular_user_cannot_export(self):
        with patch.object(requests_callbacks.bot, "answer_callback_query"):
            with patch.object(requests_callbacks, "admin_check", return_value=False):
                with patch.object(requests_callbacks, "get_requests_for_excel") as get_export:
                    requests_callbacks.requests_callback_message(callback("admin_export_all"))

        get_export.assert_not_called()


if __name__ == "__main__":
    unittest.main()
