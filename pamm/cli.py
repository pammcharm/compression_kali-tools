from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archive import create_archive, extract_archive, list_archive
from . import __version__


def _default_archive_path(input_path: str, fast: bool) -> str:
    p = Path(input_path)
    ext = ".pa" if fast else ".pamm"
    if p.is_dir():
        return str(p.with_suffix(ext))
    return str(p.with_suffix(p.suffix + ext if p.suffix else ext))


def _default_extract_dest(archive: str) -> str:
    p = Path(archive)
    name = p.name
    if name.endswith(".pamm"):
        name = name[: -len(".pamm")]
    elif name.endswith(".pa"):
        name = name[: -len(".pa")]
    else:
        name = p.stem
    return str(Path.cwd() / f"{name}_extracted")


def _completion_script(shell: str) -> str:
    if shell == "bash":
        return """# bash completion for pamm
_pamm_completions()
{
    local cur prev words cword
    _init_completion || return

    local commands="compress extract list doctor completion"
    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
        return
    fi

    case "${words[1]}" in
        compress)
            COMPREPLY=( $(compgen -W "-o --output --fast --password --json -h --help" -- "${cur}") )
            ;;
        extract)
            COMPREPLY=( $(compgen -W "-d --dest --password --json -h --help" -- "${cur}") )
            ;;
        list)
            COMPREPLY=( $(compgen -W "--json -h --help" -- "${cur}") )
            ;;
        doctor)
            COMPREPLY=( $(compgen -W "--json -h --help" -- "${cur}") )
            ;;
        completion)
            COMPREPLY=( $(compgen -W "--shell bash zsh -h --help" -- "${cur}") )
            ;;
    esac
}
complete -F _pamm_completions pamm
"""

    return """#compdef pamm

_pamm() {
  local -a commands
  commands=(
    'compress:Compress file/folder into .pamm or .pa'
    'extract:Extract archive'
    'list:Show archive metadata'
    'doctor:Check runtime and native backend status'
    'completion:Print shell completion script'
  )

  if (( CURRENT == 2 )); then
    _describe 'command' commands
    return
  fi

  case $words[2] in
    compress)
      _arguments \
        '-o[output archive path]:file:_files' \
        '--output[output archive path]:file:_files' \
        '--fast[use fast mode]' \
        '--password[encryption password]' \
        '--json[json output]'
      ;;
    extract)
      _arguments \
        '-d[destination directory]:dir:_files -/' \
        '--dest[destination directory]:dir:_files -/' \
        '--password[archive password]' \
        '--json[json output]'
      ;;
    list)
      _arguments '--json[json output]'
      ;;
    doctor)
      _arguments '--json[json output]'
      ;;
    completion)
      _arguments '--shell[shell type]:shell:(bash zsh)'
      ;;
  esac
}

_pamm "$@"
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pamm",
        description="PAMM adaptive compressor",
        epilog=(
            "Examples:\n"
            "  pamm compress my_folder\n"
            "  pamm compress video.mkv --fast\n"
            "  pamm compress src -o backup.pamm --password \"secret\"\n"
            "  pamm extract backup.pamm\n"
            "  pamm list backup.pamm\n"
            "  pamm doctor"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=f"pamm {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("compress", help="Compress file/folder into .pamm or .pa")
    c.add_argument("input", help="Input file or directory")
    c.add_argument("-o", "--output", help="Output archive path (default: inferred)")
    c.add_argument("--fast", action="store_true", help="Use .pa fast mode")
    c.add_argument("--password", help="Encrypt with password (full mode only)")
    c.add_argument("--json", action="store_true", help="Print JSON output")

    e = sub.add_parser("extract", help="Extract archive")
    e.add_argument("archive", help="Archive path")
    e.add_argument("-d", "--dest", help="Destination directory (default: inferred)")
    e.add_argument("--password", help="Password for encrypted archives")
    e.add_argument("--json", action="store_true", help="Print JSON output")

    l = sub.add_parser("list", help="Show archive metadata")
    l.add_argument("archive", help="Archive path")
    l.add_argument("--json", action="store_true", help="Print JSON output")

    d = sub.add_parser("doctor", help="Check PAMM runtime and native backend status")
    d.add_argument("--json", action="store_true", help="Print JSON output")

    comp = sub.add_parser("completion", help="Print shell completion script")
    comp.add_argument("--shell", choices=["bash", "zsh"], required=True, help="Target shell")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "compress":
            output = args.output or _default_archive_path(args.input, args.fast)
            result = create_archive(
                input_path=args.input,
                output_path=output,
                fast_mode=args.fast,
                password=args.password,
            )
            result["output"] = output
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(
                    f"Compressed {result['files']} file(s) -> {output}\n"
                    f"Raw: {result['raw_size']} bytes, Archive: {result['archive_size']} bytes, Ratio: {result['ratio']:.4f}"
                )
            return 0

        if args.command == "extract":
            dest = args.dest or _default_extract_dest(args.archive)
            result = extract_archive(
                archive_path=args.archive,
                output_dir=dest,
                password=args.password,
            )
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Extracted {result['files_restored']} file(s) -> {result['output_dir']}")
            return 0

        if args.command == "list":
            result = list_archive(args.archive)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                mode = result["mode"]
                enc = "yes" if result["encrypted"] else "no"
                print(f"Mode: {mode} | Encrypted: {enc} | Files: {len(result['files'])}")
                for entry in result["files"]:
                    print(f"- {entry['path']} ({entry['size']} bytes, {entry['blocks']} block(s))")
            return 0

        if args.command == "doctor":
            native_ok = False
            native_error = ""
            try:
                from . import native

                native_ok = native.available()
            except Exception as exc:
                native_error = str(exc)

            info = {
                "version": __version__,
                "python": sys.version.split()[0],
                "native_available": native_ok,
                "native_error": native_error,
            }
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print(
                    f"PAMM {info['version']} | Python {info['python']} | "
                    f"Native backend: {'OK' if info['native_available'] else 'MISSING'}"
                )
                if native_error:
                    print(f"Native error: {native_error}")
            return 0

        if args.command == "completion":
            print(_completion_script(args.shell))
            return 0

    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
