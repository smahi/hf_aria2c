#!/usr/bin/env python3
import os
import argparse
import subprocess
from huggingface_hub import HfApi, hf_hub_url


def parse_args():
    p = argparse.ArgumentParser(
        description="HF repo downloader using aria2 (multi-threaded)"
    )

    # Core
    p.add_argument("repo", help="repo id (e.g. gpt2 or org/model)")
    p.add_argument("--revision", default="main", help="branch/tag/commit")
    p.add_argument("-o", "--output", default="./models", help="output directory")

    # Auth
    p.add_argument("--token", default=os.getenv("HF_TOKEN"), help="HF token")

    # Filters
    p.add_argument("--include", nargs="*", help="include extensions (.json .safetensors)")
    p.add_argument("--exclude", nargs="*", help="exclude extensions (.bin .pt)")

    # aria2 tuning
    p.add_argument("-x", type=int, default=8, help="connections per file")
    p.add_argument("-j", type=int, default=4, help="parallel downloads")
    p.add_argument("-s", type=int, default=8, help="split per file")

    # Modes
    p.add_argument("--dry-run", action="store_true", help="only print URLs")
    p.add_argument("--no-aria2", action="store_true", help="print URLs only")
    p.add_argument("--input-file", default="aria2_input.txt", help="aria2 input file")

    return p.parse_args()


def fetch_metadata(api, repo, revision):
    print("📡 Fetching metadata...")
    return api.repo_info(repo, revision=revision)


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
    urls = []
    for f in files:
        url = hf_hub_url(repo, filename=f, revision=revision)
        urls.append((url, f))
    return urls


def write_aria2_file(urls, output_dir, input_file, token):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, input_file)

    with open(path, "w") as f:
        for url, filename in urls:
            f.write(f"{url}\n")
            f.write(f"  out={filename}\n")
            if token:
                f.write(f"  header=Authorization: Bearer {token}\n")

    return path


def run_aria2(input_path, output_dir, args):
    cmd = [
        "aria2c",
        "-i", input_path,
        "-d", output_dir,
        "-x", str(args.x),
        "-j", str(args.j),
        "-s", str(args.s),
        "--continue=true",
        "--auto-file-renaming=false",
        "--summary-interval=5",
        "--file-allocation=trunc"
    ]

    print("🚀 Running:", " ".join(cmd))
    subprocess.run(cmd)


def main():
    args = parse_args()

    api = HfApi(token=args.token)

    info = fetch_metadata(api, args.repo, args.revision)

    files = filter_files(info.siblings, args.include, args.exclude)
    print(f"📂 Selected {len(files)} files")

    urls = generate_urls(args.repo, args.revision, files)

    if args.dry_run or args.no_aria2:
        print("\n".join([u for u, _ in urls]))
        return

    input_path = write_aria2_file(
        urls, args.output, args.input_file, args.token
    )

    run_aria2(input_path, args.output, args)


if __name__ == "__main__":
    main()