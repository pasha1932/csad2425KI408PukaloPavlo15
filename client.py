"""
@file client.py
@brief Клієнт гри "Хрестики-Нулики" на основі COM-порту
@details Цей модуль реалізує клієнтську частину гри "Хрестики-Нулики" з графічним інтерфейсом на основі Tkinter.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import serial
import json
import threading


class TicTacToeClient:
    """
    @class TicTacToeClient
    @brief Клієнт гри "Хрестики-Нулики"
    @details Відповідає за взаємодію з сервером гри через COM-порт, а також за графічний інтерфейс користувача.
    """

    def __init__(self, port='COM12', baudrate=9600):
        """
        @brief Конструктор класу TicTacToeClient
        @param port COM-порт, який буде використовуватись для взаємодії.
        @param baudrate Швидкість передачі даних через COM-порт.
        """
        self.root = tk.Tk()
        self.root.title("Хрестики-Нулики Клієнт")
        self.ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Клієнт 'Хрестики-Нулики' запущено на {port}")
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.player_symbol = None
        self.ai_symbol = None
        self.game_over = False
        self.running = True  # Прапорець для контролю потоку
        self.create_widgets()
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.ask_player_symbol()
        self.root.mainloop()

    def ask_player_symbol(self):
        """
        @brief Запитує символ гравця у користувача.
        @details Відображає діалог для вибору символу ('X' або 'O') і передає вибір на сервер.
        """
        symbol = None
        while symbol not in ['X', 'O']:
            symbol = simpledialog.askstring("Вибір символу", "Виберіть ваш символ (X або O):", parent=self.root)
            if symbol is None:
                self.close()
                return
            symbol = symbol.upper()
            if symbol not in ['X', 'O']:
                messagebox.showwarning("Невірний вибір", "Будь ласка, введіть 'X' або 'O'.")
        self.player_symbol = symbol
        self.ai_symbol = 'O' if self.player_symbol == 'X' else 'X'
        self.ser.write(f"start {self.player_symbol}\n".encode())

    def create_widgets(self):
        """
        @brief Створює графічний інтерфейс користувача.
        @details Додає кнопки для ігрової дошки, а також елементи керування для нової гри, збереження та завантаження.
        """
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                button = tk.Button(self.root, text=" ", font=("Arial", 24), width=5, height=2,
                                   command=lambda row=i, col=j: self.make_move(row, col))
                button.grid(row=i, column=j)
                self.buttons[i][j] = button

        new_game_button = tk.Button(self.root, text="Нова гра", command=self.new_game)
        new_game_button.grid(row=3, column=0, columnspan=3, sticky="we")

        save_game_button = tk.Button(self.root, text="Зберегти гру", command=self.save_game)
        save_game_button.grid(row=4, column=0, columnspan=3, sticky="we")

        load_game_button = tk.Button(self.root, text="Завантажити гру", command=self.load_game)
        load_game_button.grid(row=5, column=0, columnspan=3, sticky="we")

    def new_game(self):
        """
        @brief Починає нову гру.
        @details Очищає ігрову дошку та повідомляє сервер про початок нової гри.
        """
        self.ser.write("new\n".encode())
        self.game_over = False
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.update_board()

    def save_game(self):
        """
        @brief Зберігає поточний стан гри.
        @details Надсилає серверу команду збереження гри.
        """
        self.ser.write("save\n".encode())
        messagebox.showinfo("Збереження", "Гру збережено у форматі INI.")

    def load_game(self):
        """
        @brief Завантажує стан гри.
        @details Надсилає серверу команду завантаження гри.
        """
        self.ser.write("load\n".encode())
        messagebox.showinfo("Завантаження", "Гру завантажено з INI файлу.")

    def make_move(self, row, col):
        """
        @brief Робить хід гравця.
        @param row Рядок, у якому гравець хоче зробити хід.
        @param col Стовпець, у якому гравець хоче зробити хід.
        """
        if self.game_over:
            messagebox.showinfo("Гра закінчена", "Почніть нову гру.")
            return
        if self.board[row][col] != " ":
            messagebox.showwarning("Некоректний хід", "Ця клітинка вже зайнята.")
            return

        self.ser.write(f"move {row} {col}\n".encode())

    def listen(self):
        """
        @brief Прослуховує відповіді від сервера.
        @details У окремому потоці отримує відповіді від сервера та обробляє їх.
        """
        try:
            while self.running:
                if self.ser.in_waiting > 0:
                    try:
                        response_str = self.ser.readline().decode().strip()
                        if response_str:
                            try:
                                response = json.loads(response_str)
                                print(f"Отримано відповідь: {response}")
                                self.process_response(response)
                            except json.JSONDecodeError as e:
                                messagebox.showerror("Помилка", f"Невірний формат відповіді від сервера: {e}")
                    except serial.SerialException as e:
                        print(f"Помилка в потоці прослуховування клієнта: {e}")
                        break
        except Exception as e:
            print(f"Помилка в потоці прослуховування клієнта: {e}")

    def process_response(self, response):
        """
        @brief Обробляє відповідь від сервера.
        @param response JSON-об'єкт з відповіддю від сервера.
        """
        message = response.get('message', '')
        board = response.get('board', None)
        game_over = response.get('game_over', False)
        player_symbol = response.get('player_symbol', self.player_symbol)
        ai_symbol = response.get('ai_symbol', self.ai_symbol)

        self.player_symbol = player_symbol
        self.ai_symbol = ai_symbol

        if board:
            self.board = board
            self.update_board()
        if message:
            if "переміг" in message or "Нічия" in message:
                messagebox.showinfo("Результат гри", message)
                self.game_over = True
            else:
                messagebox.showinfo("Інформація", message)
                self.game_over = game_over
        else:
            self.game_over = game_over

    def update_board(self):
        """
        @brief Оновлює графічне представлення ігрової дошки.
        """
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(text=self.board[i][j])
        self.root.update_idletasks()

    def close(self):
        """
        @brief Закриває клієнтську програму.
        @details Закриває з'єднання з сервером і завершує потік.
        """
        self.running = False
        if self.ser.is_open:
            self.ser.close()
        self.listen_thread.join()
        self.root.quit()


if __name__ == "__main__":
    client = TicTacToeClient()

