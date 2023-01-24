import unittest

from src.sshc import mjdb


class Test_DataRead(unittest.TestCase):
    def test_read_pyproject_toml(self):
        with self.assertRaises(SystemExit) as cm:
            mjdb().read_all_data()
        self.assertEqual(cm.exception.code, "DB file doesn't exists. Please initiate first.")


if __name__ == '__main__':
    unittest.main()
