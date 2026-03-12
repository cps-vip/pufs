# PUF Memory Analyzer

A tool for analyzing SRAM4 data from STM32 microcontrollers.

## Usage

### Build
```bash
cargo build
```
This generates the binary in the `target/` directory.

### Run
```bash
cargo run > file_name
```
Reads the bottom half of SRAM4 from the STM32 and outputs the data to a file.

## Requirements
- Rust toolchain
- STM32 device with SRAM4 memory
