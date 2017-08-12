import neovim
import subprocess
from typing import List
import enum
import functools

COMPARISONS =\
    { " < ": "less than"
    , " > " : "greater than"
    , " >= ": "greater than or equal to"
    , " <= " : "less than or equal to"
    , " == " : "is equal to"
    }

STANDARD =\
    { ",": ", comma, "
    , ".": ", dot, "
    , ":": ", colon, "
    , "\n": ", newline, "
    }

BRACKET_PAIRINGS =\
    { "(": ". open paren,"
    , ")": ", close paren."
    , "[": ". open bracket,"
    , "]": ", close bracket."
    , "{": ". open curly,"
    , "}": ", close curly."
    , "<": ". open angle,"
    , ">": ", close angle."
    }

GENERIC_BIN_OPS =\
    { "->": "stab"
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

HASKELL_BIN_OPS =\
    { ".": "compose"
    , "&": "thread"
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
        SPEAK_BRACKETS = ('speak_brackets', False)
        SPEAK_KEYPRESSES = ('speak_keypresses', False)
        SPEAK_WORDS = ('speak_words', True)
        SPEAK_MODE_TRANSITIONS = ('speak_mode_transitions', False)
        AUTO_SPEAK_LINE = ('auto_speak_line', True)
        INDENT_STATUS = ('speak_indent', False)
        PITCH_FACTOR = ('pitch_factor', 1)
        SPEED = ('speak_speed', 350)

    def __init__(self, vim):
        self.vim = vim
        self.last_spoken = ""
        self.current_process = None
        self.literal_stack = []

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

        if len(lines) == 1:
            lines[0] = lines[0][col_start:col_end]
        else:
            lines[0] = lines[0][col_start:]
            lines[-1] = lines[-1][:col_end]

        return lines

    def speak(self, 
        txt: str,
        brackets=None,
        generic=None,
        haskell=None,
        speed=None,
        indent_status=None,
        newline=False,
        literal=False,
        stop=True
        ):

        if brackets is None:
            brackets = self.get_option(self.Options.SPEAK_BRACKETS)

        if haskell is None:
            haskell = self.get_option(self.Options.INTERPRET_HASKELL_INFIX)

        if generic is None:
            generic = self.get_option(self.Options.INTERPRET_GENERIC)

        if speed is None:
            speed = self.get_option(self.Options.SPEED)

        if indent_status is None:
            indent_status = self.get_option(self.Options.INDENT_STATUS)

        indent_level = self.get_indent_level(txt) 
        pitch_mod = indent_level // self.get_option(self.Options.PITCH_FACTOR)

        if literal:
            txt = f"[[ char LTRL ]] {txt} [[ char NORM ]]"
        else:
            if haskell:
                for (target, replacement) in HASKELL_BIN_OPS.items():
                    txt = txt.replace(target, f" {replacement} ")

            if generic:
                for (target, replacement) in GENERIC_BIN_OPS.items():
                    txt = txt.replace(target, f" {replacement} ")

            for (target, replacement) in { **STANDARD, **COMPARISONS }.items():
                txt = txt.replace(target, f" {replacement} ")

            if brackets:
                for (target, replacement) in BRACKET_PAIRINGS.items():
                    txt = txt.replace(target, f" {replacement} ")

            txt = f"[[ pbas +{pitch_mod}]]"\
                + (f" indent {indent_level}, " if indent_status else "")\
                + (f"{txt}," if txt.strip() else "")\
                + (" newline" if newline else "")\
                + (", STOP." if stop else "")

        subprocess.run(["say", "-r", str(speed), txt])
        
    @neovim.command('SpeakLine')
    def cmd_speak_line(self):
        current = self.vim.current.line
        self.speak(current, newline=True)

    @neovim.command('SpeakLineDetail')
    def cmd_speak_line_detail(self):
        current = self.vim.current.line
        self.speak(current, brackets=True, generic=False, haskell=False, speed=self.get_option(self.Options.SPEED) - 100)

    @neovim.command('SpeakRange', range=True)
    def cmd_speak_range(self, line_range):
        for i in self.get_current_selection():
            self.speak(i)

    @neovim.command('SpeakRangeDetail', range=True)
    def cmd_speak_range_detail(self, line_range):
        for i in self.get_current_selection():
            self.speak(i, brackets=True, generic=False, haskell=False, speed=self.get_option(self.Options.SPEED) - 100)

    @neovim.autocmd('CursorMoved')
    @requires_option(Options.AUTO_SPEAK_LINE)
    def handle_cursor_moved(self):
        current = self.vim.current.line
        if current == self.last_spoken:
            # FIXME: Dirty hack. Should rather figure out whether changing lines
            pass
        else:
            self.last_spoken = current
            self.speak(current, newline=True)

    @neovim.autocmd('InsertEnter')
    @requires_option(Options.SPEAK_MODE_TRANSITIONS)
    def handle_insert_enter(self):
        self.speak("INSERT ON", stop=True)

    @neovim.autocmd('InsertLeave')
    @requires_option(Options.SPEAK_MODE_TRANSITIONS)
    def handle_insert_leave(self): 
        self.speak("INSERT OFF", stop=True)

    def flush_stack(self):
        word = "".join(self.literal_stack)
        self.literal_stack = []
        if self.get_option(self.Options.SPEAK_KEYPRESSES):
            self.speak(word, literal=True, speed=700)


    @neovim.autocmd('InsertCharPre', eval='[v:char, getpos(".")]')
    def handle_insert_char(self, data):
        inserted, pos = data
        _, row, col, _ = pos
        #row, col = self.vim.api.win_get_cursor(self.vim.current.window)
        line = self.vim.current.line

        self.literal_stack.append(inserted)

        speak_words = self.get_option(self.Options.SPEAK_WORDS)

        if inserted == ' ':
            self.flush_stack()

            if speak_words: 
                # Inserted a space, say the last inserted word
                start_of_word = line.rfind(' ', 0, len(line) - 1)
                word = line[start_of_word + 1:col]
                self.speak(word, brackets=True, generic=False, haskell=False, stop=False)
        elif len(self.literal_stack) > 3:
            self.flush_stack()

