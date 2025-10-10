#!/usr/bin/env python3
"""
LLM-Ready MVP - Minimal Mdream launcher
Generates md/ + llms.txt from websites using Mdream via Docker or npx fallback
"""

import argparse
import subprocess
import json
import sys
import os
import shutil
import time
from pathlib import Path
from datetime import datetime
import zipfile


def check_docker_available():
    """Check if Docker is available and working."""
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def check_npx_available():
    """Check if npx (Node.js) is available."""
    try:
        result = subprocess.run(
            ['npx', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def run_docker_mdream(origin, out_dir, include=None, exclude=None, use_playwright=False, max_pages=500, timeout=300):
    """Run Mdream via Docker with real-time output streaming."""
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{os.path.abspath(out_dir)}:/out',
        'harlanzw/mdream', 'crawl',
        '--origin', origin,
        '--out', '/out'
    ]

    if include:
        cmd.extend(['--include', include])
    if exclude:
        cmd.extend(['--exclude', exclude])
    if use_playwright:
        cmd.append('--playwright')
    if max_pages:
        cmd.extend(['--max-pages', str(max_pages)])
    if timeout:
        cmd.extend(['--timeout', str(timeout)])

    print(f"Running Docker command: {' '.join(cmd)}", flush=True)

    start_time = time.time()
    try:
        # Use Popen for real-time output streaming
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output in real-time
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line_stripped = line.strip()
                if line_stripped:
                    print(f"  {line_stripped}", flush=True)
                    output_lines.append(line_stripped)
            
            # Check for timeout
            elapsed = time.time() - start_time
            if elapsed > timeout + 120:
                print(f"Timeout reached ({elapsed:.1f}s), terminating process...", flush=True)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return False, elapsed

        return_code = process.wait()
        duration = time.time() - start_time

        if return_code != 0:
            print(f"Docker command failed with exit code {return_code}", flush=True)
            if output_lines:
                print("Last few output lines:", flush=True)
                for line in output_lines[-10:]:
                    print(f"  {line}", flush=True)
            return False, duration

        print(f"Docker command completed successfully in {duration:.1f}s", flush=True)
        return True, duration

    except Exception as e:
        print(f"Docker command failed with exception: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False, time.time() - start_time


def run_npx_mdream(origin, out_dir, include=None, exclude=None, use_playwright=False, max_pages=500, timeout=300):
    """Run Mdream via npx fallback with real-time output streaming."""
    cmd = [
        'npx', '--yes', '@mdream/crawl',  # --yes flag auto-confirms package installation
        '--url', origin,
        '--output', str(out_dir)
    ]

    if max_pages:
        cmd.extend(['--max-pages', str(max_pages)])
    if use_playwright:
        cmd.extend(['--driver', 'playwright'])
    else:
        cmd.extend(['--driver', 'http'])

    print(f"Running npx command: {' '.join(cmd)}", flush=True)
    print(f"Note: First run may take time to download @mdream/crawl package", flush=True)

    start_time = time.time()
    try:
        # Use Popen for real-time output streaming
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output in real-time
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line_stripped = line.strip()
                if line_stripped:
                    print(f"  {line_stripped}", flush=True)
                    output_lines.append(line_stripped)
            
            # Check for timeout
            elapsed = time.time() - start_time
            if elapsed > timeout + 120:  # Extra buffer for package download
                print(f"Timeout reached ({elapsed:.1f}s), terminating process...", flush=True)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return False, elapsed

        return_code = process.wait()
        duration = time.time() - start_time

        if return_code != 0:
            print(f"npx command failed with exit code {return_code}", flush=True)
            if output_lines:
                print("Last few output lines:", flush=True)
                for line in output_lines[-10:]:
                    print(f"  {line}", flush=True)
            return False, duration

        print(f"npx command completed successfully in {duration:.1f}s", flush=True)
        return True, duration

    except Exception as e:
        print(f"npx command failed with exception: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False, time.time() - start_time


def validate_output(out_dir):
    """Validate that required output files exist."""
    out_path = Path(out_dir)

    # Check for required files
    llms_txt = out_path / 'llms.txt'
    llms_full_txt = out_path / 'llms-full.txt'

    # Look for markdown files (either in md/ directory or directly in output)
    md_dir = out_path / 'md'
    markdown_files = []

    if md_dir.exists() and md_dir.is_dir():
        # Check for files in md/ directory
        markdown_files.extend(list(md_dir.rglob('*.md')))
    else:
        # Check for .md files directly in output directory
        markdown_files.extend(list(out_path.glob('*.md')))

    missing_files = []

    if not llms_txt.exists():
        missing_files.append('llms.txt')
    if not markdown_files:
        missing_files.append('markdown files')
    if not llms_full_txt.exists():
        missing_files.append('llms-full.txt')

    return missing_files


def count_output_files(out_dir):
    """Count total files in output directory."""
    out_path = Path(out_dir)
    count = 0

    # Count markdown files (either in md/ directory or directly in output)
    md_dir = out_path / 'md'
    if md_dir.exists() and md_dir.is_dir():
        # Files in md/ directory
        count += sum(1 for _, _, files in os.walk(md_dir) for _ in files)
    else:
        # .md files directly in output directory
        count += sum(1 for file in out_path.glob('*.md'))

    # Add txt files if they exist
    llms_txt = out_path / 'llms.txt'
    llms_full_txt = out_path / 'llms-full.txt'
    if llms_txt.exists():
        count += 1
    if llms_full_txt.exists():
        count += 1

    return count


def create_manifest(out_dir, origin, started_at, ended_at, duration, total_files):
    """Create manifest.json file."""
    manifest = {
        "origin": origin,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_sec": round(duration, 2),
        "total_files": total_files
    }

    manifest_path = Path(out_dir) / 'manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Created manifest: {manifest_path}")


def create_zip(output_dir, zip_path=None):
    """Create zip file of output directory."""
    if zip_path is None:
        zip_path = f"{output_dir}.zip"

    output_path = Path(output_dir)
    zip_path = Path(zip_path)

    if not output_path.exists():
        print(f"Output directory {output_dir} does not exist, cannot create zip")
        return False

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_path)
                    zipf.write(file_path, arcname)

        print(f"Created zip archive: {zip_path}")
        return True

    except Exception as e:
        print(f"Failed to create zip archive: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate LLM-ready content from website using Mdream',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python llmready_min.py --origin https://example.com
  python llmready_min.py --origin https://example.com --out ./output --include "docs,faq" --max-pages 300 --zip
        """
    )

    parser.add_argument(
        '--origin',
        required=True,
        help='Root URL of the site to crawl (required)'
    )

    parser.add_argument(
        '--out',
        default='./output',
        help='Output directory (default: ./output)'
    )

    parser.add_argument(
        '--include',
        help='Comma-separated list of path patterns to include (e.g., "docs,faq,pricing")'
    )

    parser.add_argument(
        '--exclude',
        help='Comma-separated list of path patterns to exclude (e.g., "login,cart")'
    )

    parser.add_argument(
        '--use-playwright',
        action='store_true',
        help='Use Playwright for crawling (default: false)'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        default=500,
        help='Maximum number of pages to crawl (default: 500)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout in seconds (default: 300)'
    )

    parser.add_argument(
        '--zip',
        action='store_true',
        help='Create zip archive of output directory'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.origin.startswith(('http://', 'https://')):
        print("Error: --origin must be a valid HTTP/HTTPS URL")
        sys.exit(1)

    # Create output directory
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Starting LLM-Ready generation for: {args.origin}", flush=True)
    print(f"Output directory: {out_path.absolute()}", flush=True)

    # Track timing
    started_at = datetime.now()

    # Check environment and choose execution method
    docker_available = check_docker_available()
    npx_available = check_npx_available()

    if not docker_available and not npx_available:
        print("Error: Neither Docker nor npx is available.", flush=True)
        print("Please install Docker (preferred) or Node.js with npx.", flush=True)
        sys.exit(1)

    # Execute Mdream
    success = False
    if docker_available:
        print("Using Docker to run Mdream...", flush=True)
        success, duration = run_docker_mdream(
            args.origin, str(out_path), args.include, args.exclude,
            args.use_playwright, args.max_pages, args.timeout
        )
    else:
        print("Docker not available, using npx fallback...", flush=True)
        success, duration = run_npx_mdream(
            args.origin, out_path, args.include, args.exclude,
            args.use_playwright, args.max_pages, args.timeout
        )

    if not success:
        sys.exit(1)

    ended_at = datetime.now()

    # Validate output
    missing_files = validate_output(args.out)
    if missing_files:
        print(f"Error: Missing required output files: {', '.join(missing_files)}", flush=True)
        sys.exit(1)

    # Count files and create manifest
    total_files = count_output_files(args.out)
    create_manifest(args.out, args.origin, started_at, ended_at, duration, total_files)

    print("\n✅ LLM-Ready generation completed successfully!", flush=True)
    print(f"📁 Generated {total_files} files in {duration:.1f}s", flush=True)
    print(f"📂 Output directory: {out_path.absolute()}", flush=True)

    # Create zip if requested
    if args.zip:
        print("\n📦 Creating zip archive...", flush=True)
        zip_path = f"{args.out}.zip"
        if create_zip(args.out, zip_path):
            print(f"✅ Zip archive created: {zip_path}", flush=True)

    print("\n🎉 Ready to use with LLMs! Check llms.txt and md/ directory.", flush=True)


if __name__ == '__main__':
    main()