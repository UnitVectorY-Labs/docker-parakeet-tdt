"""Unit checks for the E2E assertion logic, not a substitute for inference."""
import copy
import unittest

from transcribe import validate


class TimestampValidation(unittest.TestCase):
    def setUp(self):
        self.result = {'text': 'Hello world.', 'task': 'transcribe', 'duration': 2.0,
                       'words': [{'word': 'Hello', 'start': 0.1, 'end': 0.5},
                                 {'word': 'world.', 'start': 0.6, 'end': 1.2}]}

    def test_valid(self):
        validate(self.result)

    def test_missing_or_empty(self):
        for key, value in [('text', ''), ('words', []), ('duration', 0)]:
            result = copy.deepcopy(self.result)
            result[key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError):
                validate(result)

    def test_invalid_timestamps(self):
        for start, end in [(-1, 0), (1, 0), (0, 10), (float('nan'), 1), (0, float('inf'))]:
            result = copy.deepcopy(self.result)
            result['words'][0].update(start=start, end=end)
            with self.subTest(start=start, end=end), self.assertRaises(AssertionError):
                validate(result)

    def test_out_of_order(self):
        self.result['words'].reverse()
        with self.assertRaises(AssertionError):
            validate(self.result)


if __name__ == '__main__':
    unittest.main()
