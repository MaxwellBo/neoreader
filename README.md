# neoreader

neoreader is a screenreader for Neovim. It supports:

- generalised syntax rewrites, such as infix substitutions 
  + `->` is read as "stab" if `interpret_generic` is enabled
- language specific syntax rewrites
  + `->` is read as "yields" if `interpret_haskell_infix` is enabled
- Python 3 specific semantic analysis for more intelligible reading

```python
x = [i for i in range(1, 100) if 10 < i < 20]
```
is read as

> L-value x assigned a list comprehension of i, from a generator using i as an iterator, looping through range called with 1 and 100, with a guard of 10 is less than i is less than 20

## Requirements

neoreader requires [Neovim](https://github.com/neovim/neovim) with `if\_python3`.
If `:echo has("python3")` returns `1`, then you're fine; otherwise, see below.

You can enable the Python 3 interface with `pip`:

    pip3 install neovim

You must be using Python 3.6

You may use macOS's Speech Synthesis API _OR_ [eSpeak](https://github.com/rhdunn/espeak)


## Installation

For [vim-plug](https://github.com/junegunn/vim-plug)

```
Plug 'MaxwellBo/neoreader'
```

## Configuration

```vimscript
nnoremap <Leader>q :SpeakLine<cr>
nnoremap <Leader>w :SpeakLineDetail<cr>
nnoremap <Leader>e :SpeakLineExplain<cr>
vnoremap <Leader>a :SpeakRange<cr>
vnoremap <Leader>s :SpeakRangeDetail<cr>
vnoremap <Leader>d :SpeakRangeExplain<cr>

" defaults
let g:interpret_generic = 1
let g:interpret_haskell_infix = 0
let g:speak_brackets = 0
let g:speak_keypresses = 0
let g:speak_words = 1
let g:speak_mode_transitions = 0
let g:speak_completions = 0
let g:auto_speak_line = 1
let g:speak_indent = 0
let g:pitch_multiplier = 1
let g:speak_speed = 350
let g:use_espeak = 0
```

