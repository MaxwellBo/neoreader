import neovim
import subprocess

@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim

    @neovim.command('DoItPython')
    def doItPython(self):
        current = self.vim.current.line
        self.vim.command(f'echo "{current}"')
        subprocess.run(["say", current])
        

