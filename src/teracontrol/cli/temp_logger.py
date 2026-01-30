import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

from teracontrol.utils.logging import setup_logging, get_logger
from teracontrol.hal.mercury_itc import MercuryITCController
from teracontrol.hal.mercury_ips import MercuryIPSController

log = get_logger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PACKAGE_ROOT / "logs"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Log temperature and pressure to a file"
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Logging interval in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--logfile",
        type=Path,
        default=LOG_DIR / "temperature.log",
        help="Log file path (default: <package_root>/logs/temperature.log)",
    )

    parser.add_argument(
        "--itc",
        type=str,
        default="192.168.1.2",
        help="IP address of the ITC controller (default: 192.168.1.2)",
    )

    parser.add_argument(
        "--ips",
        type=str,
        default="192.168.1.3",
        help="IP address of the IPS controller (default: 192.168.1.3)",
    )

    parser.add_argument(
        "--level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )

    return parser.parse_args()


def format_values(values: dict[str, float]) -> str:
    """
    Format merged intrument values as:
    key1=value1 | key2=value2 | ...
    """
    return " | ".join(f"{k}={v:.6g}" for k, v in values.items())


def main():
    args = parse_args()

    # Timestamped csv per run
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = Path(args.logfile).parent / f"temperature/temperature_{run_ts}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    setup_logging(
        level=getattr(logging, args.level),
        logfile=args.logfile,
    )

    log.info("=== Temperature logging started ===")
    log.info(
        "interval: %.1fs | logfile: %s | itc: %s | ips: %s | level: %s | csv=%s",
        args.interval,
        args.logfile,
        args.itc,
        args.ips,
        args.level,
        csv_path,
    )

    itc = ips = None

    try:
        itc = MercuryITCController()
        ips = MercuryIPSController()

        itc.connect(args.itc)
        ips.connect(args.ips)

        with csv_path.open("w", encoding="utf-8") as f:
            t0 = time.monotonic()
            next_t = t0

            header_written = False
            keys: list[str] = []

            while True:
                elapsed = time.monotonic() - t0
                now_iso = datetime.now().isoformat(timespec="seconds")

                itc_temps = itc.export_temperatures()
                itc_press = itc.export_pressures()
                itc_nvalves = itc.export_nvalves()
                ips_temps = ips.export_temperatures()

                values = itc_nvalves | itc_press | itc_temps | ips_temps

                # Freeze column order on first iteration
                if not header_written:
                    keys = sorted(values.keys())
                    header = ["timestamp_iso", "elapsed_s", *keys]
                    f.write(",".join(header) + "\n")
                    f.flush()
                    header_written = True

                # CSV output
                row = [now_iso, f"{elapsed:.3f}"]
                for k in keys:
                    v = values.get(k)
                    row.append("" if v is None else f"{v:.6f}")

                f.write(",".join(row) + "\n")
                f.flush()

                # Rotating log
                log.info(format_values(values))
                
                next_t += args.interval
                sleep_time = next_t - time.monotonic()
                if sleep_time > 0:
                    time.sleep(sleep_time)

    except KeyboardInterrupt:
        log.info("Temperature logging interrupted by user")

    except Exception:
        log.error("Temperature logging failed", exc_info=True)
        raise

    finally:
        if itc is not None:
            try:
                itc.disconnect()
            except Exception:
                pass
        
        if ips is not None:
            try:
                ips.disconnect()
            except Exception:    
                pass

        log.info("=== temperature logging stopped ===")


if __name__ == "__main__":
    main()