import unittest
from unittest.mock import MagicMock, patch
from client import TicTacToeClient

class TestTicTacToeClient(unittest.TestCase):

    @patch('client.simpledialog.askstring')
    @patch('client.tk.Tk')
    @patch('serial.Serial')
    def setUp(self, mock_serial, mock_tk, mock_askstring):
        # Мокування серійного порту
        self.mock_serial_instance = mock_serial.return_value
        # Мокування Tkinter
        self.mock_root_instance = mock_tk.return_value
        # Мокування запиту символу
        mock_askstring.return_value = 'X'
        # Ініціалізація клієнта без запуску mainloop
        self.client = TicTacToeClient(start_mainloop=False)
        self.client.ser = self.mock_serial_instance
        self.client.root = self.mock_root_instance

    def test_init(self):
        # Перевірка ініціалізації клієнта
        self.assertIsNotNone(self.client.board)
        self.assertFalse(self.client.game_over)
        self.assertEqual(self.client.player_symbol, 'X')
        self.assertEqual(self.client.ai_symbol, 'O')

    def test_make_move(self):
        # Тест здійснення ходу
        self.client.game_over = False
        self.client.board = [
            [' ', ' ', ' '],
            [' ', 'X', ' '],
            [' ', ' ', ' ']
        ]
        self.client.make_move(0, 0)
        self.mock_serial_instance.write.assert_called_with(b'move 0 0\n')

    def test_make_move_invalid(self):
        # Тест некоректного ходу
        self.client.game_over = False
        self.client.board = [
            ['X', ' ', ' '],
            [' ', 'X', ' '],
            [' ', ' ', ' ']
        ]
        with patch('client.messagebox.showwarning') as mock_warning:
            self.client.make_move(0, 0)
            mock_warning.assert_called_with("Некоректний хід", "Ця клітинка вже зайнята.")

    def test_process_response_win(self):
        # Тест обробки відповіді про перемогу
        response = {
            'message': "Гравець 'X' переміг!",
            'board': [
                ['X', 'X', 'X'],
                ['O', 'O', ' '],
                [' ', ' ', ' ']
            ],
            'game_over': True,
            'player_symbol': 'X',
            'ai_symbol': 'O'
        }
        with patch('client.messagebox.showinfo') as mock_info:
            self.client.process_response(response)
            mock_info.assert_called_with("Результат гри", "Гравець 'X' переміг!")
            self.assertTrue(self.client.game_over)
            self.assertEqual(self.client.board, response['board'])

    def test_process_response_tie(self):
        # Тест обробки відповіді про нічию
        response = {
            'message': "Нічия!",
            'board': [
                ['X', 'O', 'X'],
                ['O', 'X', 'O'],
                ['O', 'X', 'O']
            ],
            'game_over': True,
            'player_symbol': 'X',
            'ai_symbol': 'O'
        }
        with patch('client.messagebox.showinfo') as mock_info:
            self.client.process_response(response)
            mock_info.assert_called_with("Результат гри", "Нічия!")
            self.assertTrue(self.client.game_over)

    def test_process_response_cell_taken(self):
        # Тест обробки повідомлення про зайняту клітинку
        response = {
            'message': "Клітинка зайнята. Спробуйте ще раз.",
            'board': self.client.board,
            'game_over': False
        }
        with patch('client.messagebox.showwarning') as mock_warning:
            self.client.process_response(response)
            mock_warning.assert_called_with("Помилка", "Клітинка зайнята. Спробуйте ще раз.")

    def test_process_response_invalid_coordinates(self):
        # Тест обробки повідомлення про некоректні координати
        response = {
            'message': "Некоректні координати. Використовуйте числа від 0 до 2.",
            'board': self.client.board,
            'game_over': False
        }
        with patch('client.messagebox.showwarning') as mock_warning:
            self.client.process_response(response)
            mock_warning.assert_called_with("Помилка", "Некоректні координати. Використовуйте числа від 0 до 2.")

    def test_new_game(self):
        # Тест методу new_game
        self.client.new_game()
        self.mock_serial_instance.write.assert_called_with(b'new\n')
        self.assertFalse(self.client.game_over)
        expected_board = [[" " for _ in range(3)] for _ in range(3)]
        self.assertEqual(self.client.board, expected_board)

    def test_save_game(self):
        # Тест методу save_game
        with patch('client.messagebox.showinfo') as mock_info:
            self.client.save_game()
            self.mock_serial_instance.write.assert_called_with(b'save\n')
            mock_info.assert_called_with("Збереження", "Гру збережено.")

    def test_load_game(self):
        # Тест методу load_game
        self.client.load_game()
        self.mock_serial_instance.write.assert_called_with(b'load\n')
        self.assertFalse(self.client.game_over)





if __name__ == '__main__':
    unittest.main()

