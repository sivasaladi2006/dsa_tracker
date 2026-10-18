import argparse

from app.services.plan import recommend, render_plan


def main():
    parser = argparse.ArgumentParser(description="Print today's practice plan.")
    parser.add_argument("--focus", type=int, default=3, help="number of focus topics")
    parser.add_argument("--problems", type=int, default=3, help="new problems per topic")
    parser.add_argument("--reviews", type=int, default=3, help="number of reviews")
    args = parser.parse_args()
    print(render_plan(recommend(args.focus, args.problems, args.reviews)))


if __name__ == "__main__":
    main()
