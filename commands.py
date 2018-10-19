"""
Run this command line interpret to explore this P.o.C.
SYNOPSIS
ADD <doc> or MADD <glob>
SEARCH <terms>
"""

from cmd import Cmd
from docbase import DocumentBase

import os.path
import glob


class CmdUI(Cmd):
    prompt = 'DOC> '
    env = {'CD': None, 'LANG': None}

    def __init__(self, service):
        self.service = service
        super().__init__()

    @staticmethod
    def _parse_assign(args):
        return tuple(map(lambda s: s.strip(), args.split('=')))

    def __setitem__(self, key, value):
        if key.upper() in CmdUI.env:
            validator = getattr(self, '_validate_{0}'.format(key.lower()), lambda x: x)
            CmdUI.env[key.upper()] = validator(value)
        elif key.upper() == 'PROMPT':
            CmdUI.prompt = f'{value} '

    @staticmethod
    def _pprint(*objects):
        for o in objects:
            if isinstance(o, dict):
                for key, val in sorted(o.items(), key=lambda t: t[0]):
                    if val is None:
                        val = 'NONE'
                    print(f'{key}={val}')
            elif isinstance(o, list):
                for e in o:
                    print(e)

    @staticmethod
    def _validate_lang(val):
        return val

    @staticmethod
    def _validate_cd(val):
        if os.path.exists(val):
            return val
        else:
            raise FileNotFoundError(val)

    @staticmethod
    def _make_filename(arg):
        path = arg
        if os.path.isfile(path):
            return path

        base = CmdUI.env['CD'] or os.curdir

        if base is not None:
            assert os.path.exists(base)

            path = os.path.join(base, path)

        return path

    @staticmethod
    def _list_files():
        base = CmdUI.env['CD']
        if base is None:
            base = os.curdir

        return list(glob.iglob(os.path.join(base, '*.pdf'), recursive=False)), base

    def _exit(self):
        pass

    """ COMMAND INTERFACE"""

    def do_exit(self, args):
        """Syntax: EXIT [message]"""
        if args:
            print(args)
        self._exit()
        return True

    def do_set(self, args):
        """Syntax: SET var=value
Description: Set a global variable in the command interpreter
Variables are CD (current directory), PROMPT and LANG
        """
        key, val = self._parse_assign(args)
        self[key] = val

    def do_show(self, args):
        """Syntax: SHOW [item]
Description: display values of some items of the program.
Items may be: ENV, PROMPT, ANALYTICS or FILES"""
        if len(args) == 0 or args.upper() == 'ENV':
            self._pprint(self.env, {'PROMPT': self.prompt})
        elif args.upper() == 'ANALYTICS':
            self._pprint(self.service.full_report)
        elif args.upper() == 'FILES':
            files, path = self._list_files()
            if len(files):
                self._pprint(files)
            else:
                print(f'No file found at {path}')

    def do_analyze(self, args):
        """Syntax: ANALYZE filename
Description: Provide NLP analytics and characterization of the document in <filename>
filename can be provided as a relative path if CD is set"""
        filename, report = None, None
        try:
            filename = self._make_filename(args)
            filename, report = self.service.analyze_document(filename)
        except FileNotFoundError as e:
            print(f'File not found: {str(e)}')
        finally:
            if filename is not None and report is not None:
                print(f'Analysis report for {filename}')
                self._pprint(report)

    def do_add(self, args):
        """Syntax: ADD filename [LANG=lang]
Description: add a document to the index. The document must be a PDF file
If LANG is provided in the command line or set as a global variable, its value is used by default
otherwise language detection is performed"""
        doc_id, report = None, None
        try:
            filename = self._make_filename(args)
            doc_id, report = self.service.add_document(filename)
        except FileNotFoundError:
            print(f'File not found: {filename}')
        finally:
            if doc_id is not None and report is not None:
                print(f'Completed processing for {filename}')
                print(f'Document added with ID={doc_id}')
                self._pprint(report)

    def do_madd(self, args):
        """Syntax: MADD fileglob [LANG=lang]
Description: add multiple documents to the index by resolving the fileglob
If the environment variable CD is set, the glob may simply be *.pdf"""

        nb_files, nb_errors = 0, 0
        nb_tries = 0
        path = args
        while nb_files == 0 and nb_tries < 2:
            for filename in glob.iglob(path, recursive=False):
                try:
                    print(f'processing file {filename}')
                    filename = self._make_filename(filename)
                    self.service.add_document(filename)
                except FileNotFoundError:
                    nb_errors += 1
                finally:
                    nb_files += 1

            path = self._make_filename(path)
            nb_tries += 1

        print(f'{nb_files} files processed with {nb_errors} errors')

    def do_search(self, args):
        """Syntax: SEARCH terms [LANG=lang]
Description: search the document base for approximate matching of <terms>.
If LANG is provided in the command line or set as a global variable, its value is used by default
otherwise language detection is performed on <terms>."""
        for result in self.service.search(args):
            print(f'file {result[1]} with relevancy of {result[0]}')


if __name__ == '__main__':
    cmd = CmdUI(service=DocumentBase())
    cmd.cmdloop()
