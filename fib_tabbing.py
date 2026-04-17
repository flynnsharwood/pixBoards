# ignore this file if you're just checking how the pixBoards lib functions. not adding this in .gitignore cause i thought this was cool.


import os
import argparse


def fib_seq(n):
    seq = [1, 2]
    for _ in range(2, n):
        seq.append(seq[-1] + seq[-2])
    return seq


FIB = fib_seq(128)


def has_fib_indentation(lines):
    # Check if all leading indents are Fibonacci numbers. I had too many unfortunate incidents without this.
    for line in lines:
        if not line.strip():  # skip empty lines
            continue
        leading = len(line) - len(line.lstrip(" "))
        if leading and leading not in FIB:
            return False
    return True


def convert_line(line, indent_size):
    leading = len(line) - len(line.lstrip(" "))
    if leading == 0:
        return line

    level = leading // indent_size
    if level == 0:
        return line

    # Map to Fibonacci spacing
    spaces = FIB[level - 1] if level - 1 < len(FIB) else FIB[-1]
    return " " * spaces + line.lstrip(" ")


def process_file(path, indent_size, dry_run=False, backup_ext=".bak", bak=False):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if has_fib_indentation(lines):
        print(f"Already Fibonacci: {path}")
        return

    new_lines = [convert_line(line, indent_size) for line in lines]

    if lines == new_lines:
        print(f"No change: {path}")
        return

    if dry_run:
        print(f"[DRY] Would convert {path}")
        return

    if bak:
        backup = path + backup_ext
        os.replace(path, backup)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Converted: {path}")


def main():
    ap = argparse.ArgumentParser(
        description="Convert space indentation to Fibonacci spacing."
    )
    ap.add_argument(
        "--indent-size",
        type=int,
        default=4,
        help="Number of spaces per indent level (default: 4)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change but don’t modify files",
    )
    ap.add_argument(
        "-r", "--recursive", action="store_true", help="Recurse into subdirectories"
    )
    ap.add_argument("--bak", action="store_true", help="Keep backup of modified files")
    args = ap.parse_args()

    if args.recursive:
        for root, _, files in os.walk("."):
            for f in files:
                if f.endswith(".py"):
                    process_file(
                        os.path.join(root, f),
                        args.indent_size,
                        args.dry_run,
                        bak=args.bak,
                    )
    else:
        for f in os.listdir("."):
            if os.path.isfile(f) and f.endswith(".py"):
                process_file(f, args.indent_size, args.dry_run, bak=args.bak)


if __name__ == "__main__":
    main()
