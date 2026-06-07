import subprocess
import os
import tempfile
from pathlib import Path

_AIGER_DIR = Path(__file__).resolve().parent.parent / "aiger"


def _parse_header(first_line):
    parts = first_line.strip().split()
    fmt = parts[0]
    nums = [int(x) for x in parts[1:]]
    M, I, L, O, A = nums[0], nums[1], nums[2], nums[3], nums[4]
    B = nums[5] if len(nums) > 5 else 0
    C = nums[6] if len(nums) > 6 else 0
    J = nums[7] if len(nums) > 7 else 0
    F = nums[8] if len(nums) > 8 else 0
    return fmt, M, I, L, O, A, B, C, J, F


def _skip_binary_delta(f):
    while True:
        b = f.read(1)
        if not b or (b[0] & 0x80) == 0:
            break


def _strip_symbol_table(aig_path):
    suffix = Path(aig_path).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix,
                                      dir=Path(aig_path).parent)
    tmp_path = tmp.name
    tmp.close()
    try:
        and_start = 0
        and_end = 0
        with open(aig_path, "rb") as fin, open(tmp_path, "wb") as fout:
            header_line = fin.readline()
            fout.write(header_line)

            header_text = header_line.decode("ascii")
            fmt, M, I, L, O, A, B, C, J, F = _parse_header(header_text)

            if fmt == "aag":
                for _ in range(I):
                    fout.write(fin.readline())
                for _ in range(L):
                    fout.write(fin.readline())
                for _ in range(O + B + C):
                    fout.write(fin.readline())
                for _ in range(A):
                    fout.write(fin.readline())
            else:
                for _ in range(L):
                    fout.write(fin.readline())
                for _ in range(O + B + C):
                    fout.write(fin.readline())
                justice_sizes = []
                for _ in range(J):
                    size_line = fin.readline()
                    fout.write(size_line)
                    justice_sizes.append(int(size_line.strip()))
                for js in justice_sizes:
                    for _ in range(js):
                        fout.write(fin.readline())
                for _ in range(F):
                    fout.write(fin.readline())
                and_start = fin.tell()
                for _ in range(A):
                    _skip_binary_delta(fin)
                    _skip_binary_delta(fin)
                and_end = fin.tell()

        with open(aig_path, "rb") as fin:
            fin.seek(and_start)
            and_data = fin.read(and_end - and_start)

        with open(tmp_path, "ab") as f:
            f.write(and_data)
            f.write(b"c\n")

        return tmp_path
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _needs_strip(aig_path):
    try:
        with open(aig_path, "rb") as f:
            header_line = f.readline()
            fmt, M, I, L, O, A, B, C, J, F = _parse_header(
                header_line.decode("ascii")
            )
            if fmt == "aag":
                for _ in range(I + L + O + B + C + A):
                    f.readline()
            else:
                for _ in range(L):
                    f.readline()
                for _ in range(O + B + C + J + F):
                    f.readline()
                justice_sizes = []
                for _ in range(J):
                    justice_sizes.append(int(f.readline().strip()))
                for js in justice_sizes:
                    for _ in range(js):
                        f.readline()
                for _ in range(F):
                    f.readline()
                for _ in range(A):
                    _skip_binary_delta(f)
                    _skip_binary_delta(f)
            remaining = f.read()
            if not remaining:
                return False
            text = remaining.decode("ascii", errors="replace")
            lines = text.split("\n")
            for line in lines:
                if not line.strip():
                    continue
                if line.strip() == "c":
                    return False
                if line[0] == "i" and len(line) > 1 and line[1] == " ":
                    return False
                if line[0] == "l" and len(line) > 1 and line[1] == " ":
                    return False
                if line[0] == "o" and len(line) > 1 and line[1] == " ":
                    return False
                return True
            return False
    except Exception:
        return True


class AigerWrapper:
    def __init__(self, aiger_dir=None):
        self.aiger_dir = Path(aiger_dir) if aiger_dir else _AIGER_DIR

    def _run(self, tool, args, input_data=None):
        tool_path = self.aiger_dir / tool
        if not tool_path.exists():
            raise FileNotFoundError(f"Tool not found: {tool_path}")
        cmd = [str(tool_path)] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=input_data,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"{tool} failed (exit {result.returncode}): {result.stderr}"
            )
        return result.stdout

    def _prepare_path(self, aig_path):
        aig_path = str(aig_path)
        if _needs_strip(aig_path):
            return _strip_symbol_table(aig_path), True
        return aig_path, False

    def to_dot(self, aig_path, strip=False, integer_lits=False):
        args = []
        if strip:
            args.append("-s")
        if integer_lits:
            args.append("-i")
        path, cleanup = self._prepare_path(aig_path)
        try:
            args.append(str(path))
            return self._run("aigtodot", args)
        finally:
            if cleanup:
                os.unlink(path)

    def ascii_to_binary(self, input_path, output_path=None):
        path, cleanup = self._prepare_path(input_path)
        try:
            args = [str(path)]
            if output_path:
                args.append(str(output_path))
            return self._run("aigtoaig", args)
        finally:
            if cleanup:
                os.unlink(path)

    def strip_symbols(self, input_path, output_path=None):
        path, cleanup = self._prepare_path(input_path)
        try:
            result = self._run("aigstrip", [str(path)])
        finally:
            if cleanup:
                os.unlink(path)
        if output_path:
            Path(output_path).write_text(result)
        return result

    def show_symbols(self, input_path):
        path, cleanup = self._prepare_path(input_path)
        try:
            return self._run("aignm", [str(path)])
        finally:
            if cleanup:
                os.unlink(path)

    def simulate(self, input_path, stimulus=None):
        path, cleanup = self._prepare_path(input_path)
        try:
            args = [str(path)]
            input_data = stimulus if stimulus else None
            return self._run("aigsim", args, input_data=input_data)
        finally:
            if cleanup:
                os.unlink(path)
