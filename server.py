"""
@file server.py
@brief Сервер гри "Хрестики-Нулики" на основі COM-порту
@details Цей модуль реалізує серверну логіку гри "Хрестики-Нулики", використовуючи бібліотеки `serial`, `json`, та `threading`.
"""

import configparser
import serial
import json
import threading


class TicTacToeServer:
    """
    @class TicTacToeServer
    @brief Сервер гри "Хрестики-Нулики"
    @details Відповідає за логіку гри, збереження/завантаження стану гри, обробку команд та взаємодію через COM-порт.
    """

    def __init__(self, port='COM11', baudrate=9600):
        """
        @brief Конструктор класу TicTacToeServer
        @param port COM-порт, який буде використовуватись для взаємодії.
        @param baudrate Швидкість передачі даних через COM-порт.
        """
        self.ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Сервер 'Хрестики-Нулики' запущено на {port}")
        self.board = self.init_board()
        self.game_over = False
        self.lock = threading.Lock()
        self.player_symbol = None
        self.ai_symbol = None
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def init_board(self):
        """
        @brief Ініціалізує порожню ігрову дошку 3x3.
        @return Список списків, що представляє ігрову дошку.
        """
        return [[" " for _ in range(3)] for _ in range(3)]

    def save_game(self, filename='savegame.ini'):
        """
        @brief Зберігає стан гри у файл.
        @param filename Ім'я файлу для збереження.
        """
        config = configparser.ConfigParser()
        config['GAME'] = {
            'player_symbol': self.player_symbol if self.player_symbol else "",
            'ai_symbol': self.ai_symbol if self.ai_symbol else "",
            'game_over': str(self.game_over)
        }
        for i in range(3):
            config[f'ROW_{i}'] = {str(j): self.board[i][j] for j in range(3)}
        with open(filename, 'w') as configfile:
            config.write(configfile)
        print(f"Гра збережена у файл {filename}")

    def load_game(self, filename='savegame.ini'):
        """
        @brief Завантажує стан гри з файлу.
        @param filename Ім'я файлу для завантаження.
        """
        config = configparser.ConfigParser()
        try:
            config.read(filename)
            self.player_symbol = config['GAME'].get('player_symbol', None)
            self.ai_symbol = config['GAME'].get('ai_symbol', None)
            self.game_over = config['GAME'].getboolean('game_over', False)
            self.board = [
                [config[f'ROW_{i}'].get(str(j), " ").strip() or " " for j in range(3)]
                for i in range(3)
            ]
            print(f"Гра завантажена з файлу {filename}")
        except (KeyError, configparser.Error) as e:
            print(f"Помилка завантаження гри: {e}")
            self.board = self.init_board()
            self.player_symbol = None
            self.ai_symbol = None
            self.game_over = False

    def check_winner(self, board, symbol):
        """
        @brief Перевіряє, чи є перемога на дошці для заданого символу.
        @param board Ігрова дошка.
        @param symbol Символ для перевірки ('X' або 'O').
        @return True, якщо символ виграв; інакше False.
        """
        lines = (
            board[0], board[1], board[2],
            [board[0][0], board[1][0], board[2][0]],
            [board[0][1], board[1][1], board[2][1]],
            [board[0][2], board[1][2], board[2][2]],
            [board[0][0], board[1][1], board[2][2]],
            [board[0][2], board[1][1], board[2][0]]
        )
        for line in lines:
            if all(cell == symbol for cell in line):
                return True
        return False

    def check_tie(self, board):
        """
        @brief Перевіряє, чи є нічия на дошці.
        @param board Ігрова дошка.
        @return True, якщо нічия; інакше False.
        """
        return all(cell != " " for row in board for cell in row)

    def minimax(self, board, depth, is_maximizing):
        """
        @brief Алгоритм мінімакс для вибору найкращого ходу AI.
        @param board Ігрова дошка.
        @param depth Глибина рекурсії.
        @param is_maximizing Прапорець, що вказує, чи AI максимізує оцінку.
        @return Оцінка ходу.
        """
        if self.check_winner(board, self.ai_symbol):
            return 1
        if self.check_winner(board, self.player_symbol):
            return -1
        if self.check_tie(board):
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == " ":
                        board[i][j] = self.ai_symbol
                        score = self.minimax(board, depth + 1, False)
                        board[i][j] = " "
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == " ":
                        board[i][j] = self.player_symbol
                        score = self.minimax(board, depth + 1, True)
                        board[i][j] = " "
                        best_score = min(score, best_score)
            return best_score

    def make_ai_move(self):
        """
        @brief Робить хід AI, використовуючи алгоритм мінімакс.
        @return Координати зробленого ходу або None, якщо хід неможливий.
        """
        best_score = -float('inf')
        move = None
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == " ":
                    self.board[i][j] = self.ai_symbol
                    score = self.minimax(self.board, 0, False)
                    self.board[i][j] = " "
                    if score > best_score:
                        best_score = score
                        move = (i, j)
        if move:
            self.board[move[0]][move[1]] = self.ai_symbol
            return move
        return None
    def process_command(self, command):
        """
                @brief Обробляє отриману команду від клієнта.
                @param command Рядок команди.
                @return JSON-рядок з результатом обробки.
        """
        response = {}
        if command.startswith("start"):
            parts = command.split()
            if len(parts) == 2 and parts[1] in ['X', 'O']:
                self.player_symbol = parts[1]
                self.ai_symbol = 'O' if self.player_symbol == 'X' else 'X'
                self.board = self.init_board()
                self.game_over = False
                response['message'] = f"Гра розпочата. Ви граєте за '{self.player_symbol}'."
            else:
                response['message'] = "Некоректна команда старту. Використовуйте 'start X' або 'start O'."
        elif command == "new":
            if self.player_symbol is None:
                response['message'] = "Спочатку виберіть символ гравця за допомогою команди 'start X' або 'start O'."
            else:
                self.board = self.init_board()
                self.game_over = False
                response['message'] = "Нова гра розпочата."
        elif command == "save":
            self.save_game()
            response['message'] = "Гру збережено."
        elif command == "load":
            self.load_game()
            response['message'] = "Гру завантажено."
        elif command.startswith("move"):
            if self.game_over:
                response['message'] = "Гра вже закінчена. Розпочніть нову гру."
            elif self.player_symbol is None:
                response['message'] = "Спочатку виберіть символ гравця за допомогою команди 'start X' або 'start O'."
            else:
                parts = command.split()
                if len(parts) == 3:
                    _, row, col = parts
                    try:
                        row, col = int(row), int(col)
                        if 0 <= row <= 2 and 0 <= col <= 2:
                            if self.board[row][col] == " ":
                                self.board[row][col] = self.player_symbol
                                if self.check_winner(self.board, self.player_symbol):
                                    response['message'] = f"Гравець '{self.player_symbol}' переміг!"
                                    self.game_over = True
                                elif self.check_tie(self.board):
                                    response['message'] = "Нічия!"
                                    self.game_over = True
                                else:
                                    ai_move = self.make_ai_move()
                                    if self.check_winner(self.board, self.ai_symbol):
                                        response['message'] = f"Гравець '{self.ai_symbol}' переміг!"
                                        self.game_over = True
                                    elif self.check_tie(self.board):
                                        response['message'] = "Нічия!"
                                        self.game_over = True
                                    else:
                                        response['message'] = f"Ваш хід на ({row}, {col}). Хід AI на ({ai_move[0]}, {ai_move[1]})."
                            else:
                                response['message'] = "Клітинка зайнята. Спробуйте ще раз."
                        else:
                            response['message'] = "Некоректні координати. Використовуйте числа від 0 до 2."
                    except ValueError:
                        response['message'] = "Некоректний формат команди."
                else:
                    response['message'] = "Некоректний формат команди."
        else:
            response['message'] = "Невідома команда."
        # Завжди додаємо дошку та стан гри до відповіді
        response['board'] = self.board
        response['game_over'] = self.game_over
        response['player_symbol'] = self.player_symbol
        response['ai_symbol'] = self.ai_symbol
        response_str = json.dumps(response) + '\n'
        return response_str

    def listen(self):
        """
        @brief Основний цикл прослуховування комунікації через COM-порт.
        """
        try:
            while True:
                if self.ser.in_waiting > 0:
                    command = self.ser.readline().decode().strip()
                    if command:
                        print(f"Отримано команду: {command}")
                        with self.lock:
                            response = self.process_command(command)
                            self.ser.write(response.encode())
        except Exception as e:
            print(f"Помилка в потоці прослуховування сервера: {e}")
        finally:
            self.ser.close()
            # Видалено автоматичне збереження конфігурації


if __name__ == "__main__":
    server = TicTacToeServer()
