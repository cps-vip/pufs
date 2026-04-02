import csv
from pathlib import Path
from collections import defaultdict

def load_bits(filepath):
    with open(filepath, 'r') as f:
        content = f.read().strip()
    # Remove any newlines or spaces – keep only 0/1
    return ''.join(ch for ch in content if ch in '01')

def analyze_board(board_folder, output_csv):
   # board_folder: Path to folder containing .bits files for a single board.
   # output_csv: Path where the per-bit statistics will be saved.

    bit_files = sorted(board_folder.glob("*.bits"))
    if not bit_files:
        print(f"No .bits files found in {board_folder}")
        return

    # Load all trials' bitstrings
    all_bits = [load_bits(f) for f in bit_files]
    if not all_bits:
        print(f"No valid bit data in {board_folder}")
        return

    # Check lengths
    num_bits = len(all_bits[0])
    for i, bits in enumerate(all_bits):
        if len(bits) != num_bits:
            print(f"Warning: {bit_files[i].name} has {len(bits)} bits, expected {num_bits}. Truncating to minimum length.")
            num_bits = min(num_bits, len(bits))
            all_bits = [bits[:num_bits] for bits in all_bits]
            break

    num_trials = len(all_bits)

    # Count zeros and ones per bit position
    zeros = [0] * num_bits
    ones = [0] * num_bits

    for bits in all_bits:
        for pos, ch in enumerate(bits):
            if ch == '0':
                zeros[pos] += 1
            else:
                ones[pos] += 1

    # Write CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['bit_position', 'zeros_count', 'ones_count', 'majority', 'stability'])
        for pos in range(num_bits):
            z = zeros[pos]
            o = ones[pos]
            if z > o:
                majority = '0'
                stability = z / num_trials
            elif o > z:
                majority = '1'
                stability = o / num_trials
            else:
                majority = 'equal'
                stability = 0.5  # can be considered unstable
            writer.writerow([pos, z, o, majority, stability])

    print(f"Saved {output_csv} with {num_bits} positions, {num_trials} trials.")
    return zeros, ones, majority, stability

def compare_boards(stability_csv1, stability_csv2, output_csv):

   # Read two stability CSVs (output from analyze_board) and compare majority per bit.

    # Read first CSV
    with open(stability_csv1, 'r') as f:
        reader = csv.DictReader(f)
        rows1 = list(reader)
    with open(stability_csv2, 'r') as f:
        reader = csv.DictReader(f)
        rows2 = list(reader)

    num_bits = min(len(rows1), len(rows2))
    mismatches = 0
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['bit_position', 'majority_board1', 'majority_board2', 'match'])
        for pos in range(num_bits):
            m1 = rows1[pos]['majority']
            m2 = rows2[pos]['majority']
            match = 'yes' if m1 == m2 else 'no'
            if match == 'no':
                mismatches += 1
            writer.writerow([pos, m1, m2, match])

    # Additional metric: Hamming distance (number of mismatched bits) between majority patterns
    print(f"Hamming distance between majority bits: {mismatches} out of {num_bits} bits ({mismatches/num_bits*100:.2f}% different)")

def main():
    # Base directory: assume bits_output is in the same folder as this script
    base_dir = Path(__file__).parent / "bits_output"
    if not base_dir.exists():
        print("bits_output folder not found. Make sure you have run the parsing script first.")
        return

    # Analyze each board
    board_folders = ["1724_SRAM4_data", "5223_SRAM4_data"]
    csv_files = []
    for board in board_folders:
        board_path = base_dir / board
        if not board_path.is_dir():
            print(f"Warning: {board_path} not found, skipping.")
            continue
        csv_out = base_dir / f"{board}_stability.csv"
        analyze_board(board_path, csv_out)
        csv_files.append(csv_out)

    # Compare the two boards
    if len(csv_files) == 2:
        compare_boards(csv_files[0], csv_files[1], base_dir / "board_comparison.csv")
    else:
        print("Could not, failed")

if __name__ == "__main__":
    main()