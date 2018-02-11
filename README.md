# neoreader

neoreader is a screenreader for Neovim. It supports:

- general infix operator identification:
  + `->` is read as "stab" if `interpet_generic_infix` is enabled
- language specific syntax infix operator identification:
  + `->` is read as "yields" if `interpret_haskell_infix` is enabled
- Python 3 specific AST analysis for more intelligible reading

```python
x = [i for i in range(1, 100) if 10 < i < 20]
```
is read as

> L-value "x" assigned a list comprehension of "i", from a generator using "i" as an iterator, looping through "range" called with 2 arguments: 1 and 100, guarded by 10 is less than "i" is less than 20

## Requirements

neoreader requires [Neovim](https://github.com/neovim/neovim) with `if_python3`.
If `:echo has("python3")` returns `1`, then you're fine; otherwise, see below.

You can enable the Python 3 interface with `pip`:

    pip3 install neovim

You must be using Python 3.6.

You may use macOS's Speech Synthesis API _OR_ [eSpeak](https://github.com/rhdunn/espeak).


## Installation

For [vim-plug](https://github.com/junegunn/vim-plug), add 

```vim
Plug 'MaxwellBo/neoreader'
```

to your configuration, and execute `:PlugInstall`.

Execute `:UpdateRemotePlugins` and restart Neovim.

## Configuration

```vim
nnoremap <Leader>q :SpeakLine<cr>
nnoremap <Leader>w :SpeakLineDetail<cr>
nnoremap <Leader>e :SpeakLineExplain<cr>
vnoremap <Leader>a :SpeakRange<cr>
vnoremap <Leader>s :SpeakRangeDetail<cr>
vnoremap <Leader>d :SpeakRangeExplain<cr>

" defaults
let g:enable_at_startup = 1
let g:interpet_generic_infix = 1
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

## Contributors

- [Lewis Bobbermen](https://github.com/lewisjb)
- [Max Bo](https://github.com/MaxwellBo)
