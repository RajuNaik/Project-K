import unittest

from data_engineering_etl import process_csv_text


class TestDataEngineeringETL(unittest.TestCase):
    def test_happy_path_summary_and_defaults(self) -> None:
        csv_text = (
            "event_id,user_id,event_ts,event_type,amount\n"
            "1,u1,2026-02-10T10:00:00Z,Click,10.50\n"
            "2,u1,2026-02-10T11:00:00+00:00,purchase,5\n"
            "3,u2,2026-02-11,,\n"
        )
        result = process_csv_text(csv_text)

        self.assertEqual(result.summary["total_rows"], 3)
        self.assertEqual(result.summary["valid_rows"], 3)
        self.assertEqual(result.summary["invalid_rows"], 0)
        self.assertEqual(result.summary["deduped_rows"], 3)
        self.assertEqual(result.summary["duplicates_dropped"], 0)
        self.assertEqual(result.summary["total_amount"], "15.50")
        self.assertEqual(result.summary["event_type_counts"]["click"], 1)
        self.assertEqual(result.summary["event_type_counts"]["purchase"], 1)
        self.assertEqual(result.summary["event_type_counts"]["unknown"], 1)
        self.assertEqual(result.summary["null_or_blank_counts"]["event_type"], 1)
        self.assertEqual(result.summary["null_or_blank_counts"]["amount"], 1)

        first = result.records[0]
        self.assertEqual(first["event_ts"], "2026-02-10T10:00:00Z")

    def test_dedupe_keep_latest_event(self) -> None:
        csv_text = (
            "event_id,user_id,event_ts,event_type,amount\n"
            "a,u1,2026-02-10T10:00:00Z,click,1\n"
            "a,u1,2026-02-10T12:00:00Z,click,2\n"
        )
        result = process_csv_text(csv_text)

        self.assertEqual(result.summary["deduped_rows"], 1)
        self.assertEqual(result.summary["duplicates_dropped"], 1)
        self.assertEqual(result.summary["total_amount"], "2")
        self.assertEqual(result.records[0]["event_ts"], "2026-02-10T12:00:00Z")

    def test_invalid_amount_skipped(self) -> None:
        csv_text = (
            "event_id,user_id,event_ts,event_type,amount\n"
            "1,u1,2026-02-10T10:00:00Z,click,not-a-number\n"
            "2,u1,2026-02-10T11:00:00Z,click,3\n"
        )
        result = process_csv_text(csv_text)

        self.assertEqual(result.summary["total_rows"], 2)
        self.assertEqual(result.summary["valid_rows"], 1)
        self.assertEqual(result.summary["invalid_rows"], 1)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.summary["total_amount"], "3")

    def test_invalid_date_raises_when_configured(self) -> None:
        csv_text = (
            "event_id,user_id,event_ts,event_type,amount\n"
            "1,u1,not-a-date,click,3\n"
        )
        with self.assertRaises(ValueError):
            process_csv_text(csv_text, on_error="raise")

    def test_missing_required_columns(self) -> None:
        csv_text = "event_id,user_id,amount\n1,u1,3\n"
        with self.assertRaises(ValueError):
            process_csv_text(csv_text)

    def test_empty_input(self) -> None:
        csv_text = "event_id,user_id,event_ts,event_type,amount\n"
        result = process_csv_text(csv_text)

        self.assertEqual(result.summary["total_rows"], 0)
        self.assertEqual(result.summary["valid_rows"], 0)
        self.assertEqual(result.summary["invalid_rows"], 0)
        self.assertEqual(result.summary["deduped_rows"], 0)

    def test_header_normalization_and_whitespace(self) -> None:
        csv_text = (
            "\ufeff EVENT_ID , USER_ID , EVENT_TS , EVENT_TYPE , AMOUNT \n"
            " 1 , u1 , 2026-02-10T10:00:00Z , CLICK , 3 \n"
        )
        result = process_csv_text(csv_text)

        self.assertEqual(result.summary["total_rows"], 1)
        self.assertEqual(result.summary["total_amount"], "3")
        self.assertEqual(result.records[0]["event_type"], "click")

    def test_timezone_normalization(self) -> None:
        csv_text = (
            "event_id,user_id,event_ts,event_type,amount\n"
            "1,u1,2026-02-10T10:00:00-05:00,click,1\n"
        )
        result = process_csv_text(csv_text)

        self.assertEqual(result.records[0]["event_ts"], "2026-02-10T15:00:00Z")


if __name__ == "__main__":
    unittest.main()
