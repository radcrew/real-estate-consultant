from datetime import timedelta

# 3 years ≈ 3 * 365 * 24 * 3600 seconds
delta_seconds = 23 * 24 * 3600

def shift_commit_date(commit):
    # decode bytes to string
    author_date = commit.author_date.decode()
    committer_date = commit.committer_date.decode()

    # split timestamp and timezone
    author_ts, author_tz = author_date.split()
    committer_ts, committer_tz = committer_date.split()

    # subtract delta
    new_author_ts = str(int(author_ts) - delta_seconds)
    new_committer_ts = str(int(committer_ts) - delta_seconds)

    # reassign (encode back to bytes)
    commit.author_date = f"{new_author_ts} {author_tz}".encode()
    commit.committer_date = f"{new_committer_ts} {committer_tz}".encode()

# apply to all commits
shift_commit_date(commit)