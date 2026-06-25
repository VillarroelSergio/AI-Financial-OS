from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import List

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from adapters.base import BaseAdapter
from models.base import AdapterResult


def run_adapters(
    adapters: List[BaseAdapter],
    max_workers: int = 5,
    timeout: int = 30,
) -> List[AdapterResult]:
    """
    Run all adapters concurrently using a ThreadPoolExecutor.

    Args:
        adapters: List of BaseAdapter instances to execute.
        max_workers: Maximum number of concurrent threads.
        timeout: Per-adapter timeout in seconds.

    Returns:
        List of AdapterResult objects (one per adapter).
    """
    results: List[AdapterResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Running adapters...", total=len(adapters))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_adapter = {
                executor.submit(_safe_fetch, adapter, timeout): adapter
                for adapter in adapters
            }

            for future in as_completed(future_to_adapter):
                adapter = future_to_adapter[future]
                try:
                    result = future.result(timeout=timeout)
                except TimeoutError:
                    result = AdapterResult(
                        provider=getattr(adapter, "name", str(adapter)),
                        success=False,
                        records=[],
                        error=f"Timeout after {timeout}s",
                        latency_ms=timeout * 1000.0,
                        raw_sample=None,
                        metadata=adapter._make_metadata(),
                    )
                except Exception as exc:
                    result = AdapterResult(
                        provider=getattr(adapter, "name", str(adapter)),
                        success=False,
                        records=[],
                        error=str(exc),
                        latency_ms=0.0,
                        raw_sample=None,
                        metadata=adapter._make_metadata(),
                    )

                results.append(result)
                progress.advance(task)

    return results


def _safe_fetch(adapter: BaseAdapter, timeout: int) -> AdapterResult:
    """Execute adapter.fetch(), catching all exceptions."""
    try:
        return adapter.fetch()
    except Exception as exc:
        return AdapterResult(
            provider=getattr(adapter, "name", str(adapter)),
            success=False,
            records=[],
            error=str(exc),
            latency_ms=0.0,
            raw_sample=None,
            metadata=adapter._make_metadata(),
        )
