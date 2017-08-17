import neovim
import subprocess
from typing import List
import enum
import functools
import ast

from .py_ast import PrettyReader


COMPARISONS =\
    { " < "  : "less than"
    , " > "  : "greater than"
    , " >= " : "greater than or equal to"
    , " <= " : "less than or equal to"
    , " == " : "is equal to"
    , " && " : "and"
    , " || " : "or"
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
    , "?:": "elvis"
    }

HASKELL_BIN_OPS =\
    { "<$>": "effmap"
    , "<*>": "applic"
    , "<$": "const map"
    , "*>": "sequence right"
    , "<*": "sequence left"
    , ">>=": "and then"
    , "=<<": "bind"
    , "<=<": "kleisli compose"
    , ">>": "sequence right"
    , "<<": "sequence left"
    , "()": "unit"
    , "::": "of type"
    , ":": "appended to"
    , "&": "thread"
    , "$": "apply"
    , "<-": "bind"
    , "->": "yields"
    , ".": "compose"
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
        ENABLE_AT_STARTUP = ('enable_at_startup', True)
        INTERPRET_GENERIC_INFIX = ('interpet_generic_infix', True)
        INTERPRET_HASKELL_INFIX = ('interpret_haskell_infix', False)
        SPEAK_BRACKETS = ('speak_brackets', False)
        SPEAK_KEYPRESSES = ('speak_keypresses', False)
        SPEAK_WORDS = ('speak_words', True)
        SPEAK_MODE_TRANSITIONS = ('speak_mode_transitions', False)
        SPEAK_COMPLETIONS = ('speak_completions', False)
        AUTO_SPEAK_LINE = ('auto_speak_line', True)
        INDENT_STATUS = ('speak_indent', False)
        PITCH_MULTIPLIER = ('pitch_multiplier', 1)
        SPEED = ('speak_speed', 350)
        USE_ESPEAK = ('use_espeak', False)

    def __init__(self, vim):
        self.vim = vim
        self.last_spoken = ""
        self.current_process = None
        self.enabled = self.get_option(self.Options.ENABLE_AT_STARTUP)
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

    def call_say(self, txt: str, speed=None, pitch=None, literal=False):
        if self.get_option(self.Options.USE_ESPEAK):
            args = ["espeak"]
            if pitch:
                args += ["-p", str(pitch)]
            if speed:
                args += ["-s", str(speed)]
            if literal:
                txt = " ".join(txt)
            args.append(txt)
        else:
            args = ["say"]
            if pitch:
                txt = f"[[ pbas +{pitch}]] {txt}"
            if speed:
                args += ["-r", str(speed)]
            if literal:
                txt = f"[[ char LTRL ]] {txt}"
            args.append(txt)

        if self.enabled:
            subprocess.run(args)

    def speak(self, 
        txt: str,
        brackets=None,
        generic=None,
        haskell=None,
        standard=True,
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
            generic = self.get_option(self.Options.INTERPRET_GENERIC_INFIX)

        if speed is None:
            speed = self.get_option(self.Options.SPEED)

        if indent_status is None:
            indent_status = self.get_option(self.Options.INDENT_STATUS)

        indent_level = self.get_indent_level(txt) 
        pitch_mod = indent_level * self.get_option(self.Options.PITCH_MULTIPLIER)

        if literal:
            self.call_say(txt, speed=speed, literal=literal)
        else:
            if haskell:
                for (target, replacement) in HASKELL_BIN_OPS.items():
                    txt = txt.replace(target, f" {replacement} ")

            if generic:
                for (target, replacement) in GENERIC_BIN_OPS.items():
                    txt = txt.replace(target, f" {replacement} ")

            if standard:
                for (target, replacement) in { **STANDARD, **COMPARISONS }.items():
                    txt = txt.replace(target, f" {replacement} ")

            if brackets:
                for (target, replacement) in BRACKET_PAIRINGS.items():
                    txt = txt.replace(target, f" {replacement} ")

            if indent_status:
                txt = f"indent {index_level}, {txt}"
            if txt.strip():
                txt = f"{txt},"
            if newline:
                txt = f"{txt} newline"
            if stop:
                txt = f"{txt}, STOP."
            self.call_say(txt, speed=speed, pitch=pitch_mod)

    def explain(self, code: str, line=True) -> str:
        try:
            top_node = ast.parse(code)

            explained = PrettyReader().visit(top_node)
        except SyntaxError as e:
            explained = f"Syntax Error: '{e.msg}'"
            if line:
                explained += " on line {e.lineno},"
            explained += " column {e.offset}"

        return explained
        
    @neovim.command('SpeakLine')
    def cmd_speak_line(self):
        current = self.vim.current.line
        self.speak(current, newline=True)

    @neovim.command('SpeakLineDetail')
    def cmd_speak_line_detail(self):
        current = self.vim.current.line
        self.speak(current, brackets=True, generic=False, haskell=False, speed=self.get_option(self.Options.SPEED) - 100)

    @neovim.command('SpeakLineExplain')
    def cmd_speak_line_explain(self):
        current = self.vim.current.line.strip()

        explained = self.explain(current, line=False)
     
        self.speak(
            explained,
            stop=True,
            standard=False,
            brackets=False,
            haskell=False,
            indent_status=False,
            speed=200
        )

    @neovim.command('SpeakRange', range=True)
    def cmd_speak_range(self, line_range):
        for i in self.get_current_selection():
            self.speak(i)

    @neovim.command('SpeakRangeDetail', range=True)
    def cmd_speak_range_detail(self, line_range):
        for i in self.get_current_selection():
            self.speak(i, brackets=True, generic=False, haskell=False, speed=self.get_option(self.Options.SPEED) - 100)

    @neovim.command('SpeakRangeExplain', range=True)
    def cmd_explain_range(self, line_range):
        lines = self.get_current_selection()
        new_first_line = lines[0].lstrip()
        base_indent_level = len(lines[0]) - len(new_first_line)

        new_lines = [
            line[base_indent_level:]
            for line in lines
        ]

        code = "\n".join(new_lines)

        explained = self.explain(code, line=True)

        self.speak(
            explained,
            stop=True,
            standard=False,
            brackets=False,
            haskell=False,
            indent_status=False,
            speed=200
        )

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

    @neovim.autocmd('CompleteDone', eval='v:completed_item')
    @requires_option(Options.SPEAK_COMPLETIONS)
    def handle_complete_done(self, item):
        if not item:
            return

        if isinstance(item, dict):
            item = item['word']

        self.speak(item)
