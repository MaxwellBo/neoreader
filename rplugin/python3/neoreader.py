import neovim
import subprocess
from typing import List


@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim
        self.speed = 350
        self.last_spoken = ""

    def get_indent_level(self, line: str) -> int:
        """
        Given a line, return the indentation level
        """
        whitespaces = 1
        if self.vim.api.get_option("expandtab"):
            whitespaces = self.vim.api.get_option("shiftwidth")

        leading_spaces = len(line) - len(line.lstrip())

        return leading_spaces // whitespaces
        
    def get_current_selection(self) -> List[str]:
        """
        Returns the current highlighted selection
        """
        buf = self.vim.current.buffer
        line_start, col_start = buf.mark('<')
        line_end, col_end = buf.mark('>')

        lines = self.vim.api.buf_get_lines(buf, line_start - 1, line_end, True)

        lines[0] = lines[0][col_start:]
        lines[-1] = lines[-1][:col_end]

        return lines

    def speak(self, txt: str) -> None:
        """
        Runs TTS on the supplied string
        """
        speed = self.speed
        speed += 100 * self.get_indent_level(txt)  # TODO - multiline support
        subprocess.run(["say", "-r", str(speed), self.mutate_speech(txt)])

    @neovim.command('SpeakLine')
    def speak_line(self):
        current = self.vim.current.line
        if current == self.last_spoken:
        # FIXME: Dirty hack. Should rather figure out whether changing lines
            pass
        else:
            self.speak(current)
            self.last_spoken = current

    @neovim.command('SpeakRange', range=True)
    def speak_range(self, line_range):
        current = self.get_current_selection()
        current = ' newline '.join(current)

        self.speak(current)

    def make_sign(_, x: int) -> str:
        if x >= 0:
            return "+"
        else:
            return "-"

    def mutate_speech(self, txt):
        # FIXME: Might be a hack, couldn't get it to read the punctuation

        conversions = { ".": " fullstop ",
                  ":": " colon ",
                  "(": " open paren ",
                  ")": " close paren ",
                  "[": " open bracket ",
                  "]": " close bracket ",
                  "{": " open curly ",
                  "}": " close curly "
                  }
        
        for (target, replacement) in conversions.items():
            txt = txt.replace(target, replacement)

        return txt
        
    @neovim.autocmd('CursorMoved')
    def handle_cursor_moved(self):
        self.speak_line()

    @neovim.autocmd('InsertEnter')
    def handle_insert_enter(self):
        self.speak("INSERT ON")

    @neovim.autocmd('InsertLeave')
    def handle_insert_leave(self): 
        self.speak("INSERT OFF")

    @neovim.command("SpeakSpeed", count=1)
    def set_speed(self, speed):
        self.speed = int(speed)

    @neovim.autocmd('InsertCharPre')
    def handle_insert_char(self):
        row, col = self.vim.api.win_get_cursor(self.vim.current.window)
        line = self.vim.current.line

        inserted = line[col - 1]

        self.speak(inserted)
