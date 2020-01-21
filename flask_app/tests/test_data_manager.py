import sqlite3
import unittest
import os


class TestDataManager(unittest.TestCase):
    def setUp(self) -> None:
        self.base_loc = self.get_base_loc("ControlTheGame")
        self.db_loc = ""
        self.init_test_db()

    def tearDown(self) -> None:
        self.init_test_db()

    # WARNING if sql execution script is moved, that's a big issue!
    def init_test_db(self):
        self.db_loc = os.path.join(self.base_loc, "flask_app/tests/test_resources/test_db.sqlite")
        sql_script_loc = os.path.join(self.base_loc, "flask_app/flaskr/schema.sql")

        if os.path.isfile(self.db_loc) is False:
            db_file = open(self.db_loc, "w")
            db_file.close()

        with open(sql_script_loc, "r") as script:
            db = self.get_db(self.db_loc)
            db.executescript(script.read().strip())

    def get_db(self, db_loc):
        db = sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        return db

    def get_base_loc(self, dir_name):
        cur_dir = os.getcwd().split("/")

        try:
            index = cur_dir.index(dir_name)
        except ValueError:
            return None

        return "/".join(cur_dir[0:index + 1])

    def test_db_creation(self):
        self.assertTrue(os.path.exists(self.db_loc))

    def test_store_game_obj(self):
        pass

if __name__ == '__main__':
    unittest.main()
