import argparse
import psycopg2
import matplotlib.pyplot as plt

# PostgreSQL connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "oilgas",
    "user": "oilgas",
    "password": "oilgas",
}


def get_prices(benchmark_id):
    query = """
        SELECT
            m.series_id,
            m.unit,
            p.date,
            p.price
        FROM prices p
        JOIN metadata m ON p.metadata_id = m.id
        WHERE m.benchmark_id = %s
        ORDER BY m.series_id, p.date
    """

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (benchmark_id,))
            return cursor.fetchall()


def plot_benchmark(benchmark_id):
    rows = get_prices(benchmark_id)

    if not rows:
        print(f"No prices found for benchmark_id={benchmark_id}")
        return

    series = {}

    for series_id, unit, date, price in rows:
        if series_id not in series:
            series[series_id] = {
                "dates": [],
                "prices": [],
                "unit": unit,
            }

        series[series_id]["dates"].append(date)
        series[series_id]["prices"].append(float(price))

    plt.figure(figsize=(12, 6))

    for series_id, data in series.items():
        plt.plot(
            data["dates"],
            data["prices"],
            label=series_id,
            linewidth=1.5,
        )

    units = {data["unit"] for data in series.values()}

    plt.title(f"Benchmark: {benchmark_id}")
    plt.xlabel("Date")
    plt.ylabel(next(iter(units)) if len(units) == 1 else "Price")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{benchmark_id}.png", dpi=150)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark_id", help="Benchmark ID to plot")
    args = parser.parse_args()

    plot_benchmark(args.benchmark_id)