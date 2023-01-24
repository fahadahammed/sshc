import unittest

from src.sshc import mjdb, read_pyproject_toml


class Test_Basic_Function(unittest.TestCase):
    def test_read_all_data(self):
        with self.assertRaises(SystemExit) as cm:
            mjdb().read_all_data()
        self.assertEqual(cm.exception.code, "DB file doesn't exists. Please initiate first.")

    def test_read_pyproject_toml(self):
        self.assertEqual(read_pyproject_toml(), '0.3.0')


if __name__ == '__main__':
    unittest.main()
