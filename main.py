#!/usr/bin/env python3
import os
import argparse
import subprocess
from huggingface_hub import HfApi, hf_hub_url


def parse_args():
    p = argparse.ArgumentParser(description="HF aria2 downloader (cache-compatible)")

    p.add_argument("repo", help="repo id (org/name)")
    p.add_argument("--revision", default="main")
    p.add_argument("--token", default=os.getenv("HF_TOKEN"))

    p.add_argument("--include", nargs="*")
    p.add_argument("--exclude", nargs="*")

    p.add_argument("-x", type=int, default=8)
    p.add_argument("-j", type=int, default=4)
    p.add_argument("-s", type=int, default=8)

    p.add_argument("--dry-run", action="store_true")

    return p.parse_args()


def get_cache_dir():
    hf_home = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    return os.path.join(hf_home, "hub")


def prepare_dirs(repo, revision, sha):
    cache_root = get_cache_dir()

    repo_safe = repo.replace("/", "--")
    base_dir = os.path.join(cache_root, f"models--{repo_safe}")

    snapshot_dir = os.path.join(base_dir, "snapshots", sha)
    refs_dir = os.path.join(base_dir, "refs")

    os.makedirs(snapshot_dir, exist_ok=True)
    os.makedirs(refs_dir, exist_ok=True)

    # write ref
    with open(os.path.join(refs_dir, revision), "w") as f:
        f.write(sha)

    return snapshot_dir


def filter_files(files, include, exclude):
    selected = []
    for f in files:
        name = f.rfilename

        if include and not any(name.endswith(ext) for ext in include):
            continue

        if exclude and any(name.endswith(ext) for ext in exclude):
            continue

        selected.append(name)

    return selected


def generate_urls(repo, revision, files):
    return [
        (hf_hub_url(repo, filename=f, revision=revision), f)
        for f in files
    ]


def write_aria2_file(urls, snapshot_dir, token):
    input_file = os.path.join(snapshot_dir, "aria2_input.txt")

    with open(input_file, "w") as f:
        for url, filename in urls:
            f.write(f"{url}\n")
            f.write(f"  out={filename}\n")
            if token:
                f.write(f"  header=Authorization: Bearer {token}\n")

    return input_file


def run_aria2(input_file, snapshot_dir, args):
    cmd = [
        "aria2c",
        "-i", input_file,
        "-d", snapshot_dir,
        "-x", str(args.x),
        "-j", str(args.j),
        "-s", str(args.s),
        "--continue=true",
        "--auto-file-renaming=false",
        "--summary-interval=5"
    ]

    subprocess.run(cmd)


def main():
    args = parse_args()

    api = HfApi(token=args.token)

    print("📡 Fetching metadata...")
    info = api.repo_info(args.repo, revision=args.revision)

    files = filter_files(info.siblings, args.include, args.exclude)
    print(f"📂 {len(files)} files selected")

    urls = generate_urls(args.repo, args.revision, files)

    if args.dry_run:
        for u, _ in urls:
            print(u)
        return

    snapshot_dir = prepare_dirs(args.repo, args.revision, info.sha)

    input_file = write_aria2_file(urls, snapshot_dir, args.token)

    print(f"🚀 Downloading into: {snapshot_dir}")
    run_aria2(input_file, snapshot_dir, args)


if __name__ == "__main__":
    main()