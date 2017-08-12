import neovim
import subprocess
from typing import List


def var(name: str, default=''):
    """
    Helper function to create a property for a NeoVim variable with default.
    """
    @property
    def inner(self):
        val = self.vim.vars.get(name)
        if val is None:
            return default
        return val

    @inner.setter
    def inner(self, new):
        return self.vim.api.set_var(name, new)

    return inner


@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim
        self.last_spoken = ""
        self.current_process = None

    # Configuration
    interpret_generic = var('interpret_generic', True)
    interpret_haskell_infix = var('interpret_haskell_infix', False)
    speak_punctuation = var('speak_punctuation', False)
    speak_keypresses = var('speak_keypresses', False)
    speak_mode_transitions = var('speak_mode_transitions', False)
    auto_speak_line = var('auto_speak_line', True)
    pitch_factor = var('pitch_factor', 1)
    speed = var('speak_speed', 350)

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
        # if self.current_process:
        #     self.current_process.kill()
        subprocess.run(["say", "-r", str(self.speed), self.mutate_speech(txt)])

    @neovim.command('SpeakLine')
    def speak_line(self):
        current = self.vim.current.line
        if current == self.last_spoken:
        # FIXME: Dirty hack. Should rather figure out whether changing lines
            pass
        else:
            self.last_spoken = current
            self.speak(current)

    @neovim.command('SpeakRange', range=True)
    def speak_range(self, line_range):
        for i in self.get_current_selection():
            self.speak(i)

    def make_sign(_, x: int) -> str:
        if x >= 0:
            return "+"
        else:
            return "-"

    def mutate_speech(self, txt):
        punctuation = { ".": "dot"
                      , ":": "colon"
                      , "(": "open paren"
                      , ")": "close paren"
                      , "[": "open bracket"
                      , "]": "close bracket"
                      , "{": "open curly"
                      , "}": "close curly"
                      }
        
        generic = { "->": "stab"
                  , ">=>": "fish"
                  , "<=>": "spaceship"
                  , "=>": "fat arrow"
                  , "===": "triple equals"
                  , "++": "increment"
                  , "--": "decrement"
                  , "+=": "add with"
                  , "-=": "subtract with"
                  , "/=": "divide with"
                  , "*=": "multiply with"
                  }

        haskell = { "." : "compose"
                  , "&" : "thread"
                  , "$": "apply"
                  , "->": "yields"
                  , "<-": "bind"
                  , "<$>": "effmap"
                  , "<$": "const map"
                  , "<*>": "applic"
                  , "*>": "sequence right"
                  , "<*": "sequence left"
                  , ">>=": "and then"
                  , "=<<": "bind"
                  , "<=<": "kleisli compose"
                  , ">>": "sequence right"
                  , "<<": "sequence left"
                  }
    
        pitch_mod = self.get_indent_level(txt) // self.pitch_factor  # TODO - multiline support

        if self.interpret_haskell_infix:
            for (target, replacement) in haskell.items():
                txt = txt.replace(target, f" {replacement} ")

        if self.interpret_generic:
            for (target, replacement) in generic.items():
                txt = txt.replace(target, f" {replacement} ")

        if self.speak_punctuation:
            for (target, replacement) in punctuation.items():
                txt = txt.replace(target, f" {replacement} ")

        return f"[[ pbas +{pitch_mod}]]" + txt
        
    @neovim.autocmd('CursorMoved')
    def handle_cursor_moved(self):
        if self.auto_speak_line:
            self.speak_line()

    @neovim.autocmd('InsertEnter')
    def handle_insert_enter(self):
        if self.speak_mode_transitions:
            self.speak("INSERT ON") # FIXME: Make this a sound - see timeyyy/orchestra.nvim

    @neovim.autocmd('InsertLeave')
    def handle_insert_leave(self): 
        if self.speak_mode_transitions:
            self.speak("INSERT OFF") # FIXME: Make this a sound

    # FIXME - Remove this? (As we now have  let g:speak_speed = 400)
    @neovim.command("SpeakSpeed", count=1)
    def set_speed(self, speed):
        self.speed = int(speed)

    @neovim.autocmd('InsertCharPre')
    def handle_insert_char(self):
        if self.speak_keypresses:
            row, col = self.vim.api.win_get_cursor(self.vim.current.window)
            line = self.vim.current.line

            inserted = line[col - 1]

            self.speak(inserted)
