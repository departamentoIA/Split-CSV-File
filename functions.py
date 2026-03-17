# Functions.py
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import polars as pl


def ensure_output_dir(output_dir: str | Path) -> Path:
    """
    Crea el directorio de salida si no existe y lo devuelve como Path.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def build_part_path(output_dir: Path, stem: str, part_number: int) -> Path:
    """
    Construye la ruta del archivo de salida para una parte.
    """
    return output_dir / f"{stem}_part_{part_number:06d}.csv"


def get_file_stem(input_csv: str | Path) -> str:
    """
    Obtiene el nombre base del archivo sin extensión.
    """
    return Path(input_csv).stem


def create_batched_reader(
    input_csv: str | Path,
    batch_size: int,
    separator: str = ",",
    encoding: str = "utf8",
    has_header: bool = True,
    quote_char: str = '"',
    infer_schema_length: int = 10000,
    ignore_errors: bool = False,
    null_values: Optional[str | List[str] | dict[str, str]] = None,
) -> pl.io.csv.batched_reader.BatchedCsvReader:
    """
    Crea un lector batched de Polars para archivos CSV grandes.
    """
    return pl.read_csv_batched(
        source=str(input_csv),
        batch_size=batch_size,
        separator=separator,
        encoding=encoding,
        has_header=has_header,
        quote_char=quote_char,
        infer_schema_length=infer_schema_length,
        ignore_errors=ignore_errors,
        null_values=null_values,
        low_memory=True,
        rechunk=False,
    )


def write_chunk(df: pl.DataFrame, output_path: Path, include_header: bool = True) -> None:
    """
    Escribe un DataFrame a CSV.
    """
    df.write_csv(file=output_path, include_header=include_header)


def concat_frames(frames: List[pl.DataFrame]) -> pl.DataFrame:
    """
    Concatena múltiples DataFrames en uno solo.
    """
    if not frames:
        return pl.DataFrame()

    if len(frames) == 1:
        return frames[0]

    return pl.concat(frames, how="vertical", rechunk=True)


def split_dataframe(
    df: pl.DataFrame,
    max_rows: int,
) -> tuple[List[pl.DataFrame], pl.DataFrame]:
    """
    Divide un DataFrame en:
    - una lista de DataFrames completos de tamaño max_rows
    - un remanente final con menos de max_rows filas
    """
    total_rows = df.height
    full_parts: List[pl.DataFrame] = []

    start = 0
    while start + max_rows <= total_rows:
        full_parts.append(df.slice(start, max_rows))
        start += max_rows

    remainder = df.slice(start, total_rows - start)
    return full_parts, remainder


def emit_full_chunks_from_buffer(
    buffer_frames: List[pl.DataFrame],
    rows_in_buffer: int,
    chunk_size: int,
    output_dir: Path,
    output_stem: str,
    part_number: int,
) -> tuple[List[pl.DataFrame], int, int, int]:
    """
    Toma los DataFrames acumulados en buffer, genera y escribe todas las partes
    completas posibles de chunk_size filas, y devuelve:

    - nuevo buffer_frames
    - nuevas filas en buffer
    - siguiente part_number
    - total de filas escritas
    """
    written_rows = 0

    if rows_in_buffer < chunk_size:
        return buffer_frames, rows_in_buffer, part_number, written_rows

    combined = concat_frames(buffer_frames)
    full_chunks, remainder = split_dataframe(combined, chunk_size)

    for chunk_df in full_chunks:
        output_path = build_part_path(output_dir, output_stem, part_number)
        write_chunk(chunk_df, output_path)
        written_rows += chunk_df.height
        part_number += 1

    new_buffer_frames = [remainder] if remainder.height > 0 else []
    new_rows_in_buffer = remainder.height

    return new_buffer_frames, new_rows_in_buffer, part_number, written_rows


def process_batches_and_split(
    reader: pl.io.csv.batched_reader.BatchedCsvReader,
    output_dir: Path,
    output_stem: str,
    chunk_size: int,
    batches_per_fetch: int = 10,
    write_remainder: bool = True,
) -> dict[str, int]:
    """
    Lee el CSV por lotes usando un BatchedCsvReader, acumula filas y escribe
    archivos CSV de chunk_size filas.

    Devuelve métricas del proceso.
    """
    buffer_frames: List[pl.DataFrame] = []
    rows_in_buffer = 0
    part_number = 1
    total_input_rows = 0
    total_written_rows = 0

    while True:
        batches = reader.next_batches(batches_per_fetch)
        if not batches:
            break

        for batch_df in batches:
            if batch_df is None or batch_df.height == 0:
                continue

            buffer_frames.append(batch_df)
            rows_in_buffer += batch_df.height
            total_input_rows += batch_df.height

            (
                buffer_frames,
                rows_in_buffer,
                part_number,
                written_now,
            ) = emit_full_chunks_from_buffer(
                buffer_frames=buffer_frames,
                rows_in_buffer=rows_in_buffer,
                chunk_size=chunk_size,
                output_dir=output_dir,
                output_stem=output_stem,
                part_number=part_number,
            )
            total_written_rows += written_now

    if write_remainder and rows_in_buffer > 0:
        remainder_df = concat_frames(buffer_frames)
        output_path = build_part_path(output_dir, output_stem, part_number)
        write_chunk(remainder_df, output_path)
        total_written_rows += remainder_df.height
        part_number += 1

    return {
        "total_input_rows": total_input_rows,
        "total_written_rows": total_written_rows,
        "total_output_files": part_number - 1,
    }
