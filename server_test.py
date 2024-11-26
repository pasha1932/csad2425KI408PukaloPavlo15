import unittest
from unittest.mock import MagicMock, patch
from server import TicTacToeServer
import json

class TestTicTacToeServer(unittest.TestCase):

    @patch('serial.Serial')
    def setUp(self, mock_serial):
        # Мокування серійного порту
        self.mock_serial_instance = mock_serial.return_value
        self.server = TicTacToeServer()
        self.server.ser = self.mock_serial_instance

    def test_init_board(self):
        # Перевірка ініціалізації дошки
        expected_board = [[" " for _ in range(3)] for _ in range(3)]
        self.assertEqual(self.server.board, expected_board)

    def test_process_command_start(self):
        # Тест команди старту гри
        response = self.server.process_command('start X')
        response_data = json.loads(response)
        self.assertEqual(response_data['player_symbol'], 'X')
        self.assertEqual(response_data['ai_symbol'], 'O')
        self.assertIn('Гра розпочата', response_data['message'])

    def test_process_command_new(self):
        # Тест команди нової гри
        self.server.player_symbol = 'X'
        response = self.server.process_command('new')
        response_data = json.loads(response)
        expected_board = [[" " for _ in range(3)] for _ in range(3)]
        self.assertEqual(self.server.board, expected_board)
        self.assertIn('Нова гра розпочата', response_data['message'])

    def test_process_command_invalid(self):
        # Тест некоректної команди
        response = self.server.process_command('invalid command')
        response_data = json.loads(response)
        self.assertIn('Невідома команда', response_data['message'])

    def test_make_ai_move(self):
        # Тест ходу AI
        self.server.player_symbol = 'X'
        self.server.ai_symbol = 'O'
        self.server.board = [
            ['X', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' ']
        ]
        ai_move = self.server.make_ai_move()
        self.assertIsNotNone(ai_move)
        self.assertEqual(self.server.board[ai_move[0]][ai_move[1]], 'O')

    def test_check_winner_row(self):
        # Перевірка перемоги по рядку
        self.server.board = [
            ['X', 'X', 'X'],
            [' ', 'O', ' '],
            ['O', ' ', ' ']
        ]
        self.assertTrue(self.server.check_winner(self.server.board, 'X'))

    def test_check_winner_column(self):
        # Перевірка перемоги по стовпцю
        self.server.board = [
            ['O', 'X', ' '],
            ['O', 'X', ' '],
            ['O', ' ', 'X']
        ]
        self.assertTrue(self.server.check_winner(self.server.board, 'O'))

    def test_check_winner_diagonal(self):
        # Перевірка перемоги по діагоналі
        self.server.board = [
            ['X', 'O', ' '],
            ['O', 'X', ' '],
            [' ', ' ', 'X']
        ]
        self.assertTrue(self.server.check_winner(self.server.board, 'X'))

    def test_check_tie(self):
        # Тест перевірки нічиєї
        self.server.board = [
            ['X', 'O', 'X'],
            ['O', 'X', 'O'],
            ['O', 'X', 'O']
        ]
        self.assertTrue(self.server.check_tie(self.server.board))

    def test_process_command_invalid_start(self):
        # Тест команди старту з некоректним символом
        response = self.server.process_command('start Z')
        response_data = json.loads(response)
        self.assertIn('Некоректна команда старту', response_data['message'])

    def test_process_command_move_without_start(self):
        # Тест команди move без вибору символу гравця
        response = self.server.process_command('move 0 0')
        response_data = json.loads(response)
        self.assertIn('Спочатку виберіть символ гравця', response_data['message'])

    def test_process_command_move_after_game_over(self):
        # Тест команди move після завершення гри
        self.server.player_symbol = 'X'
        self.server.game_over = True
        response = self.server.process_command('move 0 0')
        response_data = json.loads(response)
        self.assertIn('Гра вже закінчена', response_data['message'])

    def test_process_command_move_cell_taken(self):
        # Тест команди move на зайняту клітинку
        self.server.player_symbol = 'X'
        self.server.ai_symbol = 'O'
        self.server.board[0][0] = 'X'
        response = self.server.process_command('move 0 0')
        response_data = json.loads(response)
        self.assertIn('Клітинка зайнята', response_data['message'])

    def test_process_command_move_invalid_coordinates(self):
        # Тест команди move з некоректними координатами
        self.server.player_symbol = 'X'
        response = self.server.process_command('move 3 3')
        response_data = json.loads(response)
        self.assertIn('Некоректні координати', response_data['message'])

    def test_process_command_save(self):
        # Тест команди save
        with patch('builtins.print') as mock_print:
            response = self.server.process_command('save')
            response_data = json.loads(response)
            self.assertIn('Гру збережено', response_data['message'])
            mock_print.assert_called()

    def test_process_command_load(self):
        # Тест команди load
        with patch('builtins.print') as mock_print:
            response = self.server.process_command('load')
            response_data = json.loads(response)
            self.assertIn('Гру завантажено', response_data['message'])
            mock_print.assert_called()

    def test_minimax_tie(self):
        # Тестування minimax при нічиї
        self.server.player_symbol = 'X'
        self.server.ai_symbol = 'O'
        board = [
            ['X', 'O', 'X'],
            ['O', 'X', 'O'],
            ['O', 'X', ' ']
        ]
        score = self.server.minimax(board, 0, True)
        self.assertEqual(score, 0)



if __name__ == '__main__':
    unittest.main()

