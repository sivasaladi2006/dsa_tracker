from scripts.import_problems import import_problems
from scripts.import_submissions import import_submissions
from scripts.seed_prerequisites import seed_prerequisites
from scripts.seed_topics import seed_topics

if __name__ == "__main__":
    seed_topics()
    seed_prerequisites()
    import_problems()
    import_submissions()
