import unittest

from parser import Parser


class ParserTests(unittest.TestCase):
    def test_parse_easy_linear(self) -> None:
        p = Parser("maps/easy/01_linear_path.txt")
        p.parse()
        self.assertEqual(p.nb_drones, 2)
        self.assertEqual(p.start_hub, "start")
        self.assertEqual(p.end_hub, "goal")
        self.assertEqual(len(p.hubs), 4)
        self.assertEqual(len(p.connection_declarations), 3)


if __name__ == "__main__":
    unittest.main()
