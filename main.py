#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project:        Split-CSV-File
File:           main.py
Author:         Antonio Arteaga
Last Updated:   2026-03-17
Version:        1.0
Description:    A big CSV file is divided into many parts.
Dependencies:   polars==1.38.1
Usage:          
python main.py Emisor_PME380607P35.csv -o partes_csv -c 1000000
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from functions import (
    create_batched_reader,
    ensure_output_dir,
    get_file_stem,
    process_batches_and_split,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Divide un CSV grande en partes de 1,000,000 de filas usando Polars."
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="Ruta del archivo CSV de entrada.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="output_parts",
        help="Directorio donde se guardarán las partes.",
    )
    parser.add_argument(
        "-c",
        "--chunk-size",
        type=int,
        default=1_000_000,
        help="Número de filas por archivo de salida. Por defecto: 1,000,000.",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=250_000,
        help="Tamaño del lote de lectura de Polars. Ajusta según tu RAM.",
    )
    parser.add_argument(
        "--batches-per-fetch",
        type=int,
        default=8,
        help="Número de batches a pedir por iteración.",
    )
    parser.add_argument(
        "--separator",
        type=str,
        default=",",
        help="Separador del CSV. Por defecto: ','.",
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default="utf8",
        help="Encoding del archivo CSV. Por defecto: utf8.",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Indica que el CSV no tiene encabezado.",
    )
    parser.add_argument(
        "--ignore-errors",
        action="store_true",
        help="Ignora errores de parseo de filas.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(
            f"No existe el archivo de entrada: {input_csv}")

    output_dir = ensure_output_dir(args.output_dir)
    output_stem = get_file_stem(input_csv)

    start_time = time.perf_counter()

    reader = create_batched_reader(
        input_csv=input_csv,
        batch_size=args.batch_size,
        separator=args.separator,
        encoding=args.encoding,
        has_header=not args.no_header,
        ignore_errors=args.ignore_errors,
    )

    metrics = process_batches_and_split(
        reader=reader,
        output_dir=output_dir,
        output_stem=output_stem,
        chunk_size=args.chunk_size,
        batches_per_fetch=args.batches_per_fetch,
        write_remainder=True,
    )

    elapsed = time.perf_counter() - start_time

    print("Proceso finalizado.")
    print(f"Archivo de entrada: {input_csv}")
    print(f"Directorio de salida: {output_dir.resolve()}")
    print(f"Filas leídas: {metrics['total_input_rows']:,}")
    print(f"Filas escritas: {metrics['total_written_rows']:,}")
    print(f"Archivos generados: {metrics['total_output_files']:,}")
    print(f"Tiempo total: {elapsed:,.2f} segundos")


if __name__ == "__main__":
    main()
