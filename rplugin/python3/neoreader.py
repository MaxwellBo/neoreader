import neovim
import subprocess
from typing import List
import enum
import functools


def requires_option(option):
    def decorator(fn):
        @functools.wraps(fn)
        def inner(self, *args, **kwargs):
            if self.get_option(option):
                return fn(self, *args, **kwargs)

        return inner

    return decorator


@neovim.plugin
class Main(object):
    class Options(enum.Enum):
        INTERPRET_GENERIC = ('interpret_generic', True)
        INTERPRET_HASKELL_INFIX = ('interpret_haskell_infix', False)
        SPEAK_PUNCTUATION = ('speak_punctuation', False)
        SPEAK_KEYPRESSES = ('speak_keypresses', False)
        SPEAK_MODE_TRANSITIONS = ('speak_mode_transitions', False)
        AUTO_SPEAK_LINE = ('auto_speak_line', True)
        PITCH_FACTOR = ('pitch_factor', 1)
        SPEED = ('speak_speed', 350)

    def __init__(self, vim):
        self.vim = vim
        self.last_spoken = ""
        self.current_process = None

    def get_option(self, option):
        name, default = option.value
        val = self.vim.vars.get(name)
        if val is None:
            return default
        return val

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
        subprocess.run(["say", "-r", str(self.get_option(self.Options.SPEED)), self.mutate_speech(txt)])

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
    
        pitch_mod = self.get_indent_level(txt) // self.get_option(self.Options.PITCH_FACTOR)

        if self.get_option(self.Options.INTERPRET_HASKELL_INFIX):
            for (target, replacement) in haskell.items():
                txt = txt.replace(target, f" {replacement} ")

        if self.get_option(self.Options.INTERPRET_GENERIC):
            for (target, replacement) in generic.items():
                txt = txt.replace(target, f" {replacement} ")

        if self.get_option(self.Options.SPEAK_PUNCTUATION):
            for (target, replacement) in punctuation.items():
                txt = txt.replace(target, f" {replacement} ")

        return f"[[ pbas +{pitch_mod}]]" + txt
        
    @neovim.autocmd('CursorMoved')
    @requires_option(Options.AUTO_SPEAK_LINE)
    def handle_cursor_moved(self):
        self.speak_line()

    @neovim.autocmd('InsertEnter')
    @requires_option(Options.SPEAK_MODE_TRANSITIONS)
    def handle_insert_enter(self):
        self.speak("INSERT ON") # FIXME: Make this a sound - see timeyyy/orchestra.nvim

    @neovim.autocmd('InsertLeave')
    @requires_option(Options.SPEAK_MODE_TRANSITIONS)
    def handle_insert_leave(self): 
        self.speak("INSERT OFF") # FIXME: Make this a sound

    @neovim.autocmd('InsertCharPre', eval="v:char")
    @requires_option(Options.SPEAK_KEYPRESSES)
    def handle_insert_char(self, inserted):
        row, col = self.vim.api.win_get_cursor(self.vim.current.window)
        line = self.vim.current.line

        self.speak(inserted)

        if inserted == ' ':
            # Inserted a space, say the last inserted word
            start_of_word = line.rfind(' ', 0, len(line) - 1)
            word = line[start_of_word + 1:col]
            self.speak(word)
