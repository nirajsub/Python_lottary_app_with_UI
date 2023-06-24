import sys
import random
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QEasingCurve, QRect, QPropertyAnimation, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLineEdit, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox

MAX_LINES = 5
MAX_BET = 100
MIN_BET = 1

ROWS = 5
COLS = 3

symbol_count = {
    "A": 3,
    "B": 4,
    "C": 6,
    "D": 8,
    "E": 12,
}
symbol_value = {
    "A": 5,
    "B": 4.5,
    "C": 3,
    "D": 2.5,
    "E": 2
}


class AnimatedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(500)

    def set_target_position(self, target_position):
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(target_position)
        self.animation.start()


class DepositPage(AnimatedWidget):
    deposit_completed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)

        deposit_label = QLabel("Deposit Amount:")
        self.deposit_input = QLineEdit()
        self.deposit_input.setPlaceholderText("Enter deposit amount")
        deposit_button = QPushButton("Deposit")
        deposit_button.clicked.connect(self.deposit)

        layout.addWidget(deposit_label)
        layout.addWidget(self.deposit_input)
        layout.addWidget(deposit_button)

    def deposit(self):
        deposit_amount = self.deposit_input.text()
        if deposit_amount.isdigit():
            deposit_amount = int(deposit_amount)
            if deposit_amount > 0:
                self.deposit_completed.emit(deposit_amount)
            else:
                QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than 0.")
        else:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid number.")

class BetPage(AnimatedWidget):
    bet_completed = pyqtSignal(list)

    def __init__(self, current_balance):
        super().__init__()
        self.current_balance = current_balance
        self.selected_lines = []
        self.bet_inputs = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Bet Page")

        balance_label = QLabel(f"Total Balance: ${self.current_balance}")
        lines_label = QLabel("Select Lines to Bet On:")
        self.line_buttons = []
        for line in range(1, MAX_LINES + 1):
            line_button = QPushButton(str(line))
            line_button.setCheckable(True)
            line_button.clicked.connect(self.line_button_clicked)
            self.line_buttons.append(line_button)

        bet_label = QLabel("Enter Betting Amounts:")
        self.bet_input_layout = QVBoxLayout()

        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_button_clicked)

        layout = QVBoxLayout()
        layout.addWidget(balance_label)
        layout.addWidget(lines_label)
        for line_button in self.line_buttons:
            layout.addWidget(line_button)
        layout.addWidget(bet_label)
        layout.addLayout(self.bet_input_layout)
        layout.addWidget(submit_button)
        self.setLayout(layout)

    def line_button_clicked(self):
        sender = self.sender()
        line = int(sender.text())

        if sender.isChecked():
            self.selected_lines.append(line)
            bet_input = QLineEdit()
            self.bet_inputs.append(bet_input)
            label = QLabel(f"Line {line}:")
            layout = QHBoxLayout()
            layout.addWidget(label)
            layout.addWidget(bet_input)
            self.bet_input_layout.addLayout(layout)
        else:
            index = self.selected_lines.index(line)
            self.selected_lines.pop(index)
            bet_input = self.bet_inputs.pop(index)
            bet_input.deleteLater()

    def submit_button_clicked(self):
        if not self.selected_lines:
            QMessageBox.warning(self, "No Lines Selected", "Please select at least one line to bet on.")
            return

        bet_amounts = []
        for bet_input in self.bet_inputs:
            bet_text = bet_input.text().strip()
            if not bet_text:
                QMessageBox.warning(self, "Missing Betting Amount", "Please enter a betting amount for all selected lines.")
                return
            if not bet_text.isdigit():
                QMessageBox.warning(self, "Invalid Betting Amount", "Please enter a valid number for the betting amount.")
                return
            bet_amounts.append(int(bet_text))

        self.bet_completed.emit(bet_amounts)


class LotterySpinnerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lottery Spinner Application")
        self.setFixedSize(600, 400)

        self.deposit_page = DepositPage()
        self.deposit_page.deposit_completed.connect(self.show_bet_page)
        self.setCentralWidget(self.deposit_page)

        self.bet_page = None

        self.current_balance = 0

    def show_bet_page(self, deposit_amount):
        self.current_balance += deposit_amount
        self.bet_page = BetPage(self.current_balance)
        self.bet_page.bet_completed.connect(self.spin)
        self.setCentralWidget(self.bet_page)
        self.bet_page.set_target_position(QRect(0, 0, self.width(), self.height()))

    def spin(self, bet_amounts):
        total_betting_amount = sum(bet_amounts)

        if total_betting_amount > self.current_balance:
            QMessageBox.warning(self, "Insufficient Balance", f"You do not have enough balance. Your current balance is ${self.current_balance}")
            return

        self.current_balance -= total_betting_amount
        self.bet_page.set_target_position(QRect(-self.width(), 0, self.width(), self.height()))
        self.centralWidget().update()

        slot = self.get_machine_spin(ROWS, COLS, symbol_count)
        self.print_machine_spin(slot)

        winnings, winning_lines = self.check_winnings(slot, self.bet_page.selected_lines, bet_amounts, symbol_value)
        self.show_result(winnings, winning_lines, slot)

    def get_machine_spin(self, rows, cols, symbols):
        all_symbols = []
        for symbol, symbol_count in symbols.items():
            for _ in range(symbol_count):
                all_symbols.append(symbol)
        columns = []
        for _ in range(cols):
            column = []
            current_symbols = all_symbols[:]
            for _ in range(rows):
                value = random.choice(current_symbols)
                current_symbols.remove(value)
                column.append(value)
            columns.append(column)
        return columns

    def print_machine_spin(self, columns):
        for row in range(len(columns[0])):
            row_text = ""
            for i, column in enumerate(columns):
                if i != len(columns) - 1:
                    row_text += f"{column[row]} | "
                else:
                    row_text += column[row]
            print(row_text)

    def check_winnings(self, slot, selected_lines, bet_amounts, symbol_value):
        winnings = 0
        winning_lines = []

        for line in selected_lines:
            line_values = set(slot[i][line - 1] for i in range(len(slot)))
            line_value = line_values.pop() if len(line_values) == 1 else None
            if line_value:
                winnings += bet_amounts[line - 1 - 1] * symbol_value[line_value]  # Adjusted indexing
                winning_lines.append(line)

        return winnings, winning_lines

    def show_result(self, winnings, winning_lines, columns):
        result_message = f"Result:\n"
        slot = self.get_machine_spin(ROWS, COLS, symbol_count)

        for row in range(len(columns[0])):
            row_text = ""
            for i, column in enumerate(columns):
                if i != len(columns) - 1:
                    row_text += f"{column[row]} | "
                else:
                    row_text += column[row]
            result_message += row_text + "\n"

        result_message += f"\nWinnings: ${winnings}\n"
        if winning_lines:
            result_message += f"Winning Lines: {', '.join(str(line) for line in winning_lines)}"
        else:
            result_message += "No winning lines."

        QMessageBox.information(self, "Result", result_message)

        self.current_balance += winnings

        # Create a new instance of BetPage with the updated balance
        self.bet_page = BetPage(self.current_balance)
        self.bet_page.bet_completed.connect(self.spin)

        self.setCentralWidget(self.bet_page)
        self.bet_page.set_target_position(QRect(0, 0, self.width(), self.height()))


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(0, 0, 0, 100))
        pen.setWidth(3)
        painter.setPen(pen)

        brush = QBrush(QColor(255, 255, 255, 100))
        painter.setBrush(brush)

        rect = self.rect()
        rect.setWidth(rect.width() - 1)
        rect.setHeight(rect.height() - 1)
        painter.drawRoundedRect(rect, 10, 10)

        super().paintEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LotterySpinnerApp()
    window.show()
    sys.exit(app.exec_())
