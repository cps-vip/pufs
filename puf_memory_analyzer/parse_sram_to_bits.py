#!/usr/bin/env python3
import re
from pathlib import Path

def is_text_log(file_path):
    try:
        with open(file_path, 'rb') as f:
            # Check for UTF-16 BOM
            bom = f.read(2)
            if bom == b'\xff\xfe':
                # UTF-16 LE - definitely text
                return True
            # If no BOM, try reading as UTF-8
            f.seek(0)
            data = f.read(1024)
            try:
                # Try UTF-8 first
                text = data.decode('utf-8')
                if re.search(r'\[INFO\s+\]\s+[0-9a-f]{8}:', text):
                    return True
            except UnicodeDecodeError:
                # Not UTF-8, try UTF-16
                try:
                    text = data.decode('utf-16')
                    if re.search(r'\[INFO\s+\]\s+[0-9a-f]{8}:', text):
                        return True
                except:
                    pass
        return False
    except:
        return False

def parse_text_log(input_path, output_path):
    encodings = ['utf-16', 'utf-8']
    for enc in encodings:
        try:
            with open(input_path, 'r', encoding=enc) as f_in, open(output_path, 'w') as f_out:
                for line in f_in:
                    match = re.search(r'\[INFO\s+\]\s+[0-9a-f]{8}:\s+((?:[0-9A-Fa-f]{2}\s*)+)', line, re.IGNORECASE)
                    if match:
                        hex_part = match.group(1)
                        hex_bytes = re.findall(r'[0-9A-Fa-f]{2}', hex_part)
                        for hb in hex_bytes:
                            bits = format(int(hb, 16), '08b')
                            f_out.write(bits)
                f_out.write('\n')
            return  # success
        except (UnicodeDecodeError, OSError):
            continue
    # If both fail, fall back to binary parsing
    parse_binary_file(input_path, output_path)

def parse_binary_file(input_path, output_path):
    with open(input_path, 'rb') as f_in, open(output_path, 'w') as f_out:
        data = f_in.read()
        for byte in data:
            bits = format(byte, '08b')
            f_out.write(bits)
        f_out.write('\n')

def parse_file(input_path, output_path):
    if is_text_log(input_path):
        print(f"  (text) {input_path.name}")
        parse_text_log(input_path, output_path)
    else:
        print(f"  (binary) {input_path.name}")
        parse_binary_file(input_path, output_path)

def main():
    base_dirs = ["1724_SRAM4_data", "5223_SRAM4_data"]
    output_base = Path(__file__).parent / "bits_output"
    output_base.mkdir(exist_ok=True)

    for board_dir in base_dirs:
        board_path = Path(board_dir)
        if not board_path.is_dir():
            print(f"Warning: {board_dir} not found, skipping.")
            continue

        output_subdir = output_base / board_dir
        output_subdir.mkdir(exist_ok=True)

        for txt_file in board_path.glob("*.txt"):
            output_file = output_subdir / (txt_file.stem + ".bits")
            print(f"Processing {txt_file} -> {output_file}")
            parse_file(txt_file, output_file)

    print("Done!")

if __name__ == "__main__":
    main()