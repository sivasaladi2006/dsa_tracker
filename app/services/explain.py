from app.algorithms.sorting import merge_sort

SMALL_SAMPLE = 5       # fewer attempted problems than this: warn that the signal is rough
MIN_POINTS = 0.03      # ignore signals that contribute less than this to the score
SIGNAL_ORDER = ["low_solve", "struggle", "staleness", "coverage_gap"]


def _plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _signal_phrase(signal, stats):
    """Phrase for one signal. Only called for topics with at least one attempt."""
    attempted = stats.get("attempted") or 0
    solved = stats.get("solved") or 0
    if signal == "low_solve":
        pct = round(100 * solved / attempted)
        return f"you solved {solved} of {attempted} problems tried ({pct}%)"
    if signal == "struggle":
        return f"it takes about {stats['avg_attempts']} attempts per problem"
    if signal == "staleness":
        return f"you haven't practiced it in {stats['days_since_last']} days"
    total = stats.get("total_problems") or 0
    return f"{total - attempted} of its {total} problems are untouched"


def explain_focus(focus, stats):
    """Why a topic was picked. focus: one entry from rank_focus_topics();
    stats: that topic's row from topic_stats()."""
    topic = focus["topic"]
    attempted = stats.get("attempted") or 0
    components = focus.get("components", {})

    if attempted == 0:
        reasons = ["you haven't started it yet"]
    else:
        ranked = merge_sort(
            SIGNAL_ORDER,
            key=lambda s: (-components.get(s, 0), SIGNAL_ORDER.index(s)),
        )
        reasons = []
        for signal in ranked:
            if components.get(signal, 0) < MIN_POINTS:
                break
            reasons.append(_signal_phrase(signal, stats))
            if len(reasons) == 2:
                break
        if not reasons:
            reasons = ["it is the next best option by score"]

    text = f"{topic} (score {focus['score']}): " + " and ".join(reasons) + "."
    if 0 < attempted < SMALL_SAMPLE:
        text += f" Only {attempted} problems tried so far, so treat this as a rough signal."
    if focus.get("requested_by"):
        chain = " -> ".join(focus["path"])
        text = (f"{focus['requested_by']} ranks higher, but it depends on {topic} "
                f"(path: {chain}), so start here. " + text)
    return text


def explain_new_problem(problem, target, focus):
    text = f"{problem['title']}: new {problem['difficulty']} problem in {focus['topic']}; "
    if problem["difficulty"] == target:
        text += f"matches your target level ({target})."
    else:
        text += f"closest untouched match to your target level ({target})."
    requested_by = focus.get("requested_by")
    if requested_by and requested_by in problem["topics"].split("|"):
        text += f" It also covers {requested_by}, so it advances both."
    return text


def explain_review(review):
    return (f"{review['title']}: last result was {review['status']} after "
            f"{_plural(review['attempts'], 'attempt')}, {review['days_ago']} days ago; "
            f"due after {review['interval_days']} days, so {review['overdue_days']} days overdue.")
