import tkinter as tk
from tkinter import messagebox, simpledialog
import serial
import json
import threading


class TicTacToeClient:
    def __init__(self, port='COM12', baudrate=9600):
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
        # Створення кнопок для поля
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                button = tk.Button(self.root, text=" ", font=("Arial", 24), width=5, height=2,
                                   command=lambda row=i, col=j: self.make_move(row, col))
                button.grid(row=i, column=j)
                self.buttons[i][j] = button

        # Кнопки керування
        new_game_button = tk.Button(self.root, text="Нова гра", command=self.new_game)
        new_game_button.grid(row=3, column=0, columnspan=3, sticky="we")

        save_game_button = tk.Button(self.root, text="Зберегти гру", command=self.save_game)
        save_game_button.grid(row=4, column=0, columnspan=3, sticky="we")

        load_game_button = tk.Button(self.root, text="Завантажити гру", command=self.load_game)
        load_game_button.grid(row=5, column=0, columnspan=3, sticky="we")

    def new_game(self):
        self.ser.write("new\n".encode())
        self.game_over = False
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.update_board()

    def save_game(self):
        self.ser.write("save\n".encode())
        messagebox.showinfo("Збереження", "Гру збережено у форматі INI.")

    def load_game(self):
        self.ser.write("load\n".encode())
        messagebox.showinfo("Завантаження", "Гру завантажено з INI файлу.")

    def make_move(self, row, col):
        if self.game_over:
            messagebox.showinfo("Гра закінчена", "Почніть нову гру.")
            return
        if self.board[row][col] != " ":
            messagebox.showwarning("Некоректний хід", "Ця клітинка вже зайнята.")
            return

        self.ser.write(f"move {row} {col}\n".encode())

    def listen(self):
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
        message = response.get('message', '')
        board = response.get('board', None)
        game_over = response.get('game_over', False)
        player_symbol = response.get('player_symbol', self.player_symbol)
        ai_symbol = response.get('ai_symbol', self.ai_symbol)

        # Оновлюємо символи гравця та AI, якщо вони змінилися
        self.player_symbol = player_symbol
        self.ai_symbol = ai_symbol

        if board:
            self.board = board
            self.update_board()
        if message:
            if "переміг" in message or "Нічия" in message:
                messagebox.showinfo("Результат гри", message)
                self.game_over = True
            elif "Клітинка зайнята" in message or "Некоректні координати" in message:
                messagebox.showwarning("Помилка", message)
            elif "Гра розпочата" in message or "Нова гра розпочата" in message or "Гру завантажено" in message:
                messagebox.showinfo("Хрестики-Нулики", message)
                self.game_over = game_over
            else:
                messagebox.showinfo("Інформація", message)
                self.game_over = game_over
        else:
            self.game_over = game_over

    def update_board(self):
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(text=self.board[i][j])
        self.root.update_idletasks()

    def close(self):
        self.running = False
        if self.ser.is_open:
            self.ser.close()
        self.listen_thread.join()
        self.root.quit()


if __name__ == "__main__":
    client = TicTacToeClient()
