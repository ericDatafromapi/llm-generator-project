#!/usr/bin/env python3
"""
LLM-Ready Web Interface - Streamlit App
Provides a user-friendly web interface for the LLM-Ready tool
"""

import streamlit as st
import subprocess
import threading
import time
import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import json
import base64
from io import BytesIO

# Import our existing functions by copying them here to avoid import issues
import argparse
import subprocess
import json
import sys
import os
import shutil
import time
import zipfile
import threading
from pathlib import Path
from datetime import datetime
from io import BytesIO

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
    """Run Mdream via Docker."""
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

    print(f"Running Docker command: {' '.join(cmd)}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 60  # Add buffer for Docker startup
        )

        duration = time.time() - start_time

        if result.returncode != 0:
            print(f"Docker command failed with exit code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False, duration

        print(f"Docker command completed successfully in {duration:.1f}s")
        return True, duration

    except subprocess.TimeoutExpired:
        print(f"Docker command timed out after {timeout + 60}s")
        return False, timeout + 60
    except Exception as e:
        print(f"Docker command failed with exception: {e}")
        return False, time.time() - start_time

def run_npx_mdream(origin, out_dir, include=None, exclude=None, use_playwright=False, max_pages=500, timeout=300):
    """Run Mdream via npx fallback."""
    cmd = [
        'npx', '@mdream/crawl',
        '--url', origin,
        '--output', str(out_dir)
    ]

    if max_pages:
        cmd.extend(['--max-pages', str(max_pages)])
    if use_playwright:
        cmd.extend(['--driver', 'playwright'])
    else:
        cmd.extend(['--driver', 'http'])

    print(f"Running npx command: {' '.join(cmd)}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 60  # Increased buffer for npx startup and processing
        )

        duration = time.time() - start_time

        if result.returncode != 0:
            print(f"npx command failed with exit code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False, duration

        print(f"npx command completed successfully in {duration:.1f}s")
        return True, duration

    except subprocess.TimeoutExpired:
        print(f"npx command timed out after {timeout + 60}s")
        return False, timeout + 60
    except Exception as e:
        print(f"npx command failed with exception: {e}")
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


# Page configuration
st.set_page_config(
    page_title="LLM-Ready Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark theme styling
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* CSS Variables - Dark Theme */
    :root {
        --background: hsl(240, 20%, 8%);
        --foreground: hsl(240, 10%, 98%);
        --card: hsl(240, 18%, 12%);
        --card-foreground: hsl(240, 10%, 98%);
        --primary: hsl(260, 60%, 55%);
        --primary-glow: hsl(280, 70%, 65%);
        --accent: hsl(280, 70%, 60%);
        --muted: hsl(240, 15%, 20%);
        --muted-foreground: hsl(240, 10%, 65%);
        --border: hsl(240, 15%, 20%);
    }
    
    /* Global styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Streamlit overrides for dark theme */
    .stApp {
        background: var(--background);
        color: var(--foreground);
    }
    
    /* Gradient animations */
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes glow {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    @keyframes fade-in {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    /* Main header with gradient and glow */
    .main-header {
        position: relative;
        text-align: center;
        background: linear-gradient(135deg, hsl(260, 60%, 25%) 0%, hsl(240, 50%, 20%) 100%);
        color: var(--foreground);
        padding: 3rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        overflow: hidden;
        border: 1px solid var(--border);
        animation: fade-in 0.6s ease-out;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, hsl(260, 60%, 55%, 0.3) 0%, transparent 70%);
        animation: glow 3s ease-in-out infinite;
        pointer-events: none;
    }
    
    .main-header h1 {
        position: relative;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(to right, hsl(260, 60%, 70%), hsl(280, 70%, 75%), hsl(280, 70%, 60%));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        z-index: 1;
    }
    
    .main-header p {
        position: relative;
        opacity: 0.95;
        font-weight: 400;
        color: hsl(240, 10%, 85%);
        z-index: 1;
    }
    
    /* Status cards with glassmorphism */
    .status-card {
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 3px solid;
        backdrop-filter: blur(10px);
        animation: fade-in 0.4s ease-out;
    }
    
    .status-success {
        background: linear-gradient(135deg, hsla(142, 76%, 36%, 0.15), hsla(142, 76%, 36%, 0.05));
        border-color: hsl(142, 76%, 46%);
        color: hsl(142, 76%, 76%);
    }
    
    .status-error {
        background: linear-gradient(135deg, hsla(0, 72%, 51%, 0.15), hsla(0, 72%, 51%, 0.05));
        border-color: hsl(0, 72%, 61%);
        color: hsl(0, 72%, 76%);
    }
    
    .status-info {
        background: linear-gradient(135deg, hsla(260, 60%, 55%, 0.15), hsla(260, 60%, 55%, 0.05));
        border-color: var(--primary);
        color: hsl(260, 60%, 75%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: var(--card);
        border-right: 1px solid var(--border);
    }
    
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1.25rem;
        color: var(--foreground);
        letter-spacing: -0.01em;
    }
    
    /* Input fields */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background: var(--muted) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--foreground) !important;
        transition: all 0.2s ease;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }
    
    /* Buttons with gradient */
    .stButton > button {
        background: linear-gradient(135deg, hsl(260, 60%, 55%), hsl(280, 70%, 60%)) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px hsla(260, 60%, 55%, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px hsla(260, 60%, 55%, 0.4) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: var(--muted) !important;
        border: 1px solid var(--border) !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--foreground) !important;
        font-weight: 700 !important;
    }
    
    /* Cards and containers */
    .element-container {
        animation: fade-in 0.5s ease-out;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--foreground) !important;
    }
    
    /* Text areas */
    .stTextArea textarea {
        background: var(--muted) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--foreground) !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--card);
        padding: 4px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: var(--muted-foreground);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--muted) !important;
        color: var(--foreground) !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: var(--muted) !important;
        border: 1px solid var(--border) !important;
        color: var(--foreground) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stDownloadButton > button:hover {
        border-color: var(--primary) !important;
        background: var(--card) !important;
    }
    
    /* Checkbox and radio */
    .stCheckbox, .stRadio {
        color: var(--foreground) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--primary) !important;
    }
    
    /* Slider */
    .stSlider [data-baseweb="slider"] {
        background: var(--muted);
    }
    
    .stSlider [role="slider"] {
        background: var(--primary) !important;
    }
</style>
""", unsafe_allow_html=True)

def run_crawl_subprocess(origin, out_dir, include, exclude, use_playwright, max_pages, timeout):
    """Run the crawl using subprocess (non-blocking for Streamlit)"""
    # Build command - use the virtual environment's Python
    venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python3')
    python_cmd = venv_python if os.path.exists(venv_python) else 'python3'
    
    cmd = [
        python_cmd, '-u', 'llmready_min.py',  # -u for unbuffered output
        '--origin', origin,
        '--out', out_dir,
        '--max-pages', str(max_pages),
        '--timeout', str(timeout)
    ]
    
    if include:
        cmd.extend(['--include', include])
    if exclude:
        cmd.extend(['--exclude', exclude])
    if use_playwright:
        cmd.append('--use-playwright')
    
    # Set environment to ensure unbuffered output
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,  # Unbuffered
        universal_newlines=True,
        env=env
    )


def cleanup_output_directory(output_dir):
    """Clean up output directory before new generation"""
    output_path = Path(output_dir)
    
    if output_path.exists():
        try:
            # Remove all contents
            shutil.rmtree(output_path)
            print(f"Cleaned up existing output directory: {output_path}")
        except Exception as e:
            print(f"Warning: Could not clean up output directory: {e}")
    
    # Recreate the directory
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Created fresh output directory: {output_path}")


def create_download_zip(output_dir):
    """Create a zip file of the output directory"""
    import zipfile

    zip_buffer = BytesIO()
    output_path = Path(output_dir)

    if not output_path.exists():
        return None

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in output_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(output_path)
                zipf.write(file_path, arcname)

    zip_buffer.seek(0)
    return zip_buffer


def show_landing_page():
    """Display the landing page"""
    st.markdown("""
        <style>
            .hero-section {
                position: relative;
                text-align: center;
                padding: 5rem 2rem;
                background: linear-gradient(135deg, hsl(260, 60%, 15%) 0%, hsl(240, 50%, 12%) 100%);
                color: var(--foreground);
                border-radius: 16px;
                margin-bottom: 4rem;
                overflow: hidden;
                border: 1px solid var(--border);
                animation: fade-in 0.8s ease-out;
            }
            
            .hero-section::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 600px;
                height: 600px;
                background: radial-gradient(circle, hsl(260, 60%, 55%, 0.3) 0%, transparent 70%);
                animation: glow 3s ease-in-out infinite;
                pointer-events: none;
            }
            
            .hero-section::after {
                content: '';
                position: absolute;
                inset: 0;
                background: linear-gradient(135deg,
                    hsla(260, 60%, 55%, 0.1) 0%,
                    transparent 50%,
                    hsla(280, 70%, 60%, 0.1) 100%);
                animation: gradient-shift 8s ease infinite;
                background-size: 400% 400%;
                pointer-events: none;
            }
            
            .hero-content {
                position: relative;
                z-index: 1;
            }
            
            .hero-title {
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 1.25rem;
                line-height: 1.1;
                letter-spacing: -0.03em;
            }
            
            .gradient-text {
                background: linear-gradient(to right,
                    hsl(260, 60%, 70%),
                    hsl(280, 70%, 75%),
                    hsl(280, 70%, 60%));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                display: inline-block;
            }
            
            .hero-subtitle {
                font-size: 1.5rem;
                margin-bottom: 2rem;
                opacity: 0.95;
                font-weight: 400;
                color: hsl(240, 10%, 85%);
            }
            
            .hero-description {
                font-size: 1.125rem;
                margin-bottom: 2rem;
                color: hsl(240, 10%, 75%);
                font-weight: 400;
                line-height: 1.7;
                max-width: 700px;
                margin-left: auto;
                margin-right: auto;
            }
            
            .feature-card {
                background: var(--card);
                padding: 2rem;
                border-radius: 12px;
                border: 1px solid var(--border);
                margin-bottom: 1.5rem;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                backdrop-filter: blur(10px);
            }
            
            .feature-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, var(--primary), var(--accent));
            }
            
            .feature-card:hover {
                border-color: hsl(260, 60%, 45%);
                transform: translateY(-4px);
                box-shadow: 0 12px 28px hsla(260, 60%, 55%, 0.2);
            }
            
            .feature-icon {
                font-size: 2.25rem;
                margin-bottom: 1rem;
                display: inline-block;
                background: linear-gradient(135deg, var(--primary), var(--accent));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .feature-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--foreground);
                margin-bottom: 0.75rem;
                letter-spacing: -0.01em;
            }
            
            .feature-text {
                color: var(--muted-foreground);
                font-size: 1rem;
                line-height: 1.6;
            }
            
            .cta-section {
                position: relative;
                text-align: center;
                padding: 4rem 2rem;
                background: linear-gradient(135deg, hsl(260, 60%, 18%) 0%, hsl(280, 60%, 20%) 100%);
                color: var(--foreground);
                border-radius: 16px;
                margin: 4rem 0;
                overflow: hidden;
                border: 1px solid var(--border);
            }
            
            .cta-section::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 500px;
                height: 500px;
                background: radial-gradient(circle, hsl(280, 70%, 60%, 0.2) 0%, transparent 70%);
                animation: glow 3s ease-in-out infinite;
                pointer-events: none;
            }
            
            .cta-content {
                position: relative;
                z-index: 1;
            }
            
            .cta-section h2 {
                font-weight: 700;
                letter-spacing: -0.02em;
                color: var(--foreground);
            }
            
            .cta-section p {
                opacity: 0.9;
                color: hsl(240, 10%, 80%);
            }
            
            .step-number {
                display: inline-block;
                width: 36px;
                height: 36px;
                background: linear-gradient(135deg, var(--primary), var(--accent));
                color: white;
                border-radius: 50%;
                text-align: center;
                line-height: 36px;
                font-weight: 600;
                margin-right: 1rem;
                font-size: 0.9rem;
                box-shadow: 0 4px 12px hsla(260, 60%, 55%, 0.3);
            }
            
            .trust-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                background: hsla(260, 60%, 55%, 0.15);
                border: 1px solid hsla(260, 60%, 55%, 0.3);
                border-radius: 8px;
                color: hsl(260, 60%, 75%);
                font-size: 0.875rem;
                font-weight: 500;
                margin: 0.5rem;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
            }
            
            .trust-badge:hover {
                background: hsla(260, 60%, 55%, 0.25);
                border-color: hsla(260, 60%, 55%, 0.5);
            }
            
            .info-box {
                background: var(--card);
                border: 1px solid var(--border);
                border-left: 3px solid var(--primary);
                padding: 1.5rem;
                border-radius: 12px;
                margin: 2rem 0;
                backdrop-filter: blur(10px);
            }
            
            .benefit-card {
                background: var(--card);
                border: 1px solid var(--border);
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            }
            
            .benefit-card:hover {
                border-color: hsl(260, 60%, 45%);
                box-shadow: 0 8px 20px hsla(260, 60%, 55%, 0.15);
            }
            
            .benefit-card h4 {
                color: var(--foreground);
                margin-bottom: 0.75rem;
                font-weight: 600;
            }
            
            .benefit-card ul {
                color: var(--muted-foreground);
                margin: 0;
                padding-left: 1.25rem;
            }
            
            .benefit-card li {
                margin-bottom: 0.5rem;
                line-height: 1.6;
            }
        </style>
        
        <div class="hero-section">
            <div class="hero-content">
                <div class="hero-title">
                    Make Your Site <span class="gradient-text">AI-Ready</span>
                </div>
                <div class="hero-subtitle">Professional LLM Content Optimization Platform</div>
                <p class="hero-description">
                    Enable AI assistants to accurately understand and represent your business.
                    Generate standardized <strong>llms.txt</strong> files that ensure your content is properly indexed
                    and referenced by ChatGPT, Claude, and other AI platforms.
                </p>
                <div style="margin-top: 2rem;">
                    <span class="trust-badge">✓ Lightning Fast</span>
                    <span class="trust-badge">✓ Standards Compliant</span>
                    <span class="trust-badge">✓ 100% Secure</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # What is it section
    st.markdown("## What is llms.txt?")
    st.markdown("""
    <div class="info-box">
        <p style="color: var(--muted-foreground); font-size: 1.1rem; line-height: 1.8; margin: 0;">
            <strong style="color: var(--foreground);">llms.txt</strong> is the emerging industry standard for making websites machine-readable
            by AI language models. As businesses increasingly rely on AI assistants for research and decision-making,
            having a properly formatted llms.txt file ensures your organization's information is accurately represented
            in AI-generated responses.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Features
    st.markdown("## Why Choose Our Enterprise Solution?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Rapid Processing</div>
            <div class="feature-text">
                Advanced crawling technology delivers comprehensive results in minutes, not hours. Optimized for enterprise-scale websites.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Standards Compliant</div>
            <div class="feature-text">
                Generates properly structured llms.txt files following the latest specifications for maximum AI compatibility.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <div class="feature-title">Secure & Private</div>
            <div class="feature-text">
                No data storage, no tracking, no account required. Your content remains completely private and secure.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How it works
    st.markdown("## Implementation Process")
    
    st.markdown("""
    <div class="info-box" style="padding: 2.5rem;">
        <p style="font-size: 1.125rem; margin-bottom: 2rem; color: var(--muted-foreground);">
            <span class="step-number">1</span> <strong style="color: var(--foreground);">Submit Website URL</strong> - Provide your domain for comprehensive analysis
        </p>
        <p style="font-size: 1.125rem; margin-bottom: 2rem; color: var(--muted-foreground);">
            <span class="step-number">2</span> <strong style="color: var(--foreground);">Automated Processing</strong> - Our system crawls and structures your content
        </p>
        <p style="font-size: 1.125rem; margin-bottom: 2rem; color: var(--muted-foreground);">
            <span class="step-number">3</span> <strong style="color: var(--foreground);">Download Package</strong> - Receive complete llms.txt and metadata files
        </p>
        <p style="font-size: 1.125rem; color: var(--muted-foreground);">
            <span class="step-number">4</span> <strong style="color: var(--foreground);">Deploy to Production</strong> - Upload llms.txt to your website root directory
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Benefits
    st.markdown("## Key Business Benefits")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="benefit-card">
            <h4>📊 Enhanced AI Visibility</h4>
            <ul>
                <li>Ensure accurate representation in AI-generated responses</li>
                <li>Improve discoverability in AI-powered searches</li>
                <li>Control your narrative in AI conversations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="benefit-card">
            <h4>🚀 Competitive Advantage</h4>
            <ul>
                <li>Stay ahead of industry trends</li>
                <li>Future-proof your digital presence</li>
                <li>Lead in AI-first market positioning</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="benefit-card">
            <h4>⚙️ Operational Efficiency</h4>
            <ul>
                <li>Eliminate manual content preparation</li>
                <li>Automated updates and maintenance</li>
                <li>Seamless integration with existing infrastructure</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="benefit-card">
            <h4>📈 ROI & Growth</h4>
            <ul>
                <li>Increase qualified traffic from AI platforms</li>
                <li>Improve conversion through accurate AI representation</li>
                <li>Measurable impact on digital engagement</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # CTA Section
    st.markdown("""
    <div class="cta-section">
        <div class="cta-content">
            <h2 style="font-size: 2.25rem; margin-bottom: 1.25rem; font-weight: 700;">Ready to Optimize for AI?</h2>
            <p style="font-size: 1.125rem; margin-bottom: 2.5rem;">
                Start generating professional llms.txt files for your organization today.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Large CTA button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Get Started Now →", type="primary", use_container_width=True, help="Launch the LLM-Ready Generator"):
            st.session_state.page = 'generator'
            st.rerun()
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 3rem 2rem 2rem; color: var(--muted-foreground); border-top: 1px solid var(--border); margin-top: 4rem;">
        <p style="font-weight: 500; color: var(--foreground);">Powered by Advanced Web Crawling Technology</p>
        <p style="font-size: 0.875rem; margin-top: 1rem;">
            © 2024 LLM-Ready Generator • <a href="https://llmstxt.org" target="_blank" style="color: var(--primary); text-decoration: none;">Documentation</a> • Professional Support Available
        </p>
    </div>
    """, unsafe_allow_html=True)


def show_generator():
    """Display the generator page"""
    # Initialize session state for tracking completed crawls
    if 'crawl_completed' not in st.session_state:
        st.session_state.crawl_completed = False
    if 'last_output_dir' not in st.session_state:
        st.session_state.last_output_dir = None
    
    # Back button
    if st.button("← Back to Home"):
        st.session_state.page = 'landing'
        st.rerun()
    
    # Header
    st.markdown("""
        <div class="main-header">
            <h1 style="font-size: 2.5rem; margin-bottom: 0.75rem;">LLM-Ready Generator</h1>
            <p style="font-size: 1.125rem;">Professional AI Content Optimization Platform</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.markdown('<div class="sidebar-header">Configuration Settings</div>', unsafe_allow_html=True)

        # URL Input
        origin_url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the complete URL of your website"
        )

        # Output directory
        output_dir = st.text_input(
            "Output Directory",
            value="./output",
            help="Specify the directory for generated files"
        )

        # Advanced options
        with st.expander("Advanced Options"):
            include_patterns = st.text_input(
                "Include Patterns (CSV)",
                placeholder="docs,faq,pricing",
                help="Specify path patterns to include"
            )

            exclude_patterns = st.text_input(
                "Exclude Patterns (CSV)",
                placeholder="login,cart,admin",
                help="Specify path patterns to exclude"
            )

            use_playwright = st.checkbox(
                "Enable JavaScript Rendering",
                value=False,
                help="Use Playwright for dynamic content"
            )

            max_pages = st.slider(
                "Maximum Pages",
                min_value=10,
                max_value=1000,
                value=100,
                help="Limit the number of pages to process"
            )

            timeout = st.slider(
                "Timeout (seconds)",
                min_value=60,
                max_value=600,
                value=300,
                help="Maximum processing time"
            )

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Generate LLM-Ready Content")

        if st.button("Start Generation →", type="primary", use_container_width=True):
            if not origin_url:
                st.error("❌ Please enter a website URL")
                return

            if not origin_url.startswith(('http://', 'https://')):
                st.error("❌ URL must start with http:// or https://")
                return

            # Progress tracking
            progress_bar = st.progress(0)
            status_container = st.container()

            # Status tracking variables
            current_progress = 0
            current_status = ""

            def update_progress(value):
                nonlocal current_progress
                current_progress = value
                progress_bar.progress(value / 100)

            def update_status(message):
                nonlocal current_status
                current_status = message
                with status_container:
                    st.markdown(f"**{message}**")

            # Reset session state at start of new crawl
            st.session_state.crawl_completed = False
            st.session_state.last_output_dir = None
            
            # Clean up output directory before starting
            with st.spinner("🧹 Preparing output directory..."):
                cleanup_output_directory(output_dir)
            
            # Start the crawl process
            with st.spinner("Generating LLM-ready content..."):
                update_status("🚀 Starting crawl process...")
                update_progress(10)
                
                try:
                    process = run_crawl_subprocess(
                        origin_url, output_dir, include_patterns, exclude_patterns,
                        use_playwright, max_pages, timeout
                    )
                    
                    update_progress(20)
                    update_status("⏳ Crawling in progress... This may take a few minutes.")
                    
                    # Monitor process output
                    output_lines = []
                    last_status = ""
                    
                    while True:
                        line = process.stdout.readline()
                        
                        if not line and process.poll() is not None:
                            break
                        
                        if line:
                            line_stripped = line.strip()
                            output_lines.append(line_stripped)
                            
                            # Update status with important lines only
                            if line_stripped and not line_stripped.startswith(('◐', '◓', '◑', '◒')):
                                # Skip spinner characters, only show meaningful updates
                                if 'Crawling' in line_stripped or 'Complete' in line_stripped or 'Discovery' in line_stripped:
                                    # Avoid spamming with same status
                                    if line_stripped != last_status:
                                        update_status(f"📝 {line_stripped[:80]}")
                                        last_status = line_stripped
                            
                            # Increment progress gradually
                            if current_progress < 80:
                                update_progress(min(current_progress + 1, 80))
                    
                    # Wait for process to complete
                    return_code = process.wait()
                    success = return_code == 0
                    
                    if success:
                        update_progress(90)
                        update_status("✅ Crawl completed! Processing results...")
                        # Mark session as completed
                        st.session_state.crawl_completed = True
                        st.session_state.last_output_dir = output_dir
                    else:
                        update_status(f"❌ Process exited with code {return_code}")
                        st.error(f"Process failed with return code {return_code}")
                        
                        # Show error output in an expander
                        if output_lines:
                            with st.expander("Show error details"):
                                for line in output_lines[-20:]:  # Last 20 lines
                                    st.text(line)
                    
                    update_progress(100)
                    
                except Exception as e:
                    st.error(f"❌ Exception occurred: {type(e).__name__}: {str(e)}")
                    with st.expander("Show full traceback"):
                        import traceback
                        st.code(traceback.format_exc())
                    success = False

            # Final status
            if success:
                st.success("✅ Generation completed successfully!")

                # Show results
                st.subheader("📋 Generated Files")

                output_path = Path(output_dir)
                if output_path.exists():
                    files = list(output_path.rglob('*'))
                    files = [f for f in files if f.is_file()]

                    # Group files by type
                    md_files = [f for f in files if f.suffix == '.md']
                    txt_files = [f for f in files if f.suffix == '.txt']
                    json_files = [f for f in files if f.suffix == '.json']

                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.metric("Markdown Files", len(md_files))
                    with col_b:
                        st.metric("Text Files", len(txt_files))
                    with col_c:
                        st.metric("Total Files", len(files))

                    # File preview tabs
                    tab1, tab2, tab3 = st.tabs(["📄 llms.txt", "📝 llms-full.txt", "📋 manifest.json"])

                    with tab1:
                        llms_file = output_path / 'llms.txt'
                        if llms_file.exists():
                            with open(llms_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            st.text_area("LLM Summary", content, height=200)

                    with tab2:
                        llms_full_file = output_path / 'llms-full.txt'
                        if llms_full_file.exists():
                            with open(llms_full_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            # Show first 2000 characters as preview
                            preview = content[:2000] + ("..." if len(content) > 2000 else "")
                            st.text_area("Full Content Preview", preview, height=200)

                    with tab3:
                        manifest_file = output_path / 'manifest.json'
                        if manifest_file.exists():
                            with open(manifest_file, 'r', encoding='utf-8') as f:
                                manifest_data = json.load(f)
                            st.json(manifest_data)
                else:
                    st.error("❌ Output directory not found")

            else:
                st.error("❌ Generation failed. Check the logs above for details.")

    with col2:
        st.subheader("Download Package")

        # Only show downloads if a crawl was just completed in this session
        if st.session_state.crawl_completed and st.session_state.last_output_dir:
            output_path = Path(st.session_state.last_output_dir)
            
            if output_path.exists():
                # Download all files as zip
                zip_buffer = create_download_zip(st.session_state.last_output_dir)
                if zip_buffer:
                    st.download_button(
                        label="📦 Download All Files (ZIP)",
                        data=zip_buffer,
                        file_name=f"llm-ready-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )

                st.markdown("---")

                # Individual file downloads
                st.markdown("**Individual Files:**")

                txt_files = list(output_path.glob('*.txt'))
                json_files = list(output_path.glob('*.json'))

                for txt_file in txt_files:
                    if txt_file.exists():
                        with open(txt_file, 'rb') as f:
                            file_data = f.read()
                        st.download_button(
                            label=f"📄 {txt_file.name}",
                            data=file_data,
                            file_name=txt_file.name,
                            mime="text/plain",
                            key=f"download_{txt_file.name}",
                            use_container_width=True
                        )

                for json_file in json_files:
                    if json_file.exists():
                        with open(json_file, 'rb') as f:
                            file_data = f.read()
                        st.download_button(
                            label=f"📋 {json_file.name}",
                            data=file_data,
                            file_name=json_file.name,
                            mime="application/json",
                            key=f"download_{json_file.name}",
                            use_container_width=True
                        )
            else:
                st.warning("⚠️ Output directory not found")
        else:
            st.info("👆 Generate content first to enable downloads")

        # Instructions
        st.markdown("---")
        st.subheader("Implementation Guide")

        st.markdown("""
        <div style="background: var(--card); border: 1px solid var(--border); border-left: 3px solid var(--primary); padding: 1.5rem; border-radius: 8px; backdrop-filter: blur(10px);">
            <h4 style="color: var(--foreground); margin-bottom: 1rem;">Quick Start Process:</h4>
            <ol style="color: #475569; margin: 0; padding-left: 1.25rem;">
                <li style="margin-bottom: 0.5rem;">Enter your website URL in the configuration panel</li>
                <li style="margin-bottom: 0.5rem;">Adjust advanced settings if needed</li>
                <li style="margin-bottom: 0.5rem;">Click "Start Generation" to begin processing</li>
                <li style="margin-bottom: 0.5rem;">Monitor progress in real-time</li>
                <li style="margin-bottom: 0.5rem;">Download the complete package when ready</li>
            </ol>
        </div>
        
        <div style="margin-top: 1.5rem;">
            <h4 style="color: var(--foreground); margin-bottom: 0.75rem;">Generated Package Contents:</h4>
            <ul style="color: var(--muted-foreground); padding-left: 1.25rem;">
                <li><strong>llms.txt</strong> - Optimized summary for AI consumption</li>
                <li><strong>llms-full.txt</strong> - Comprehensive content with metadata</li>
                <li><strong>manifest.json</strong> - Processing metadata and statistics</li>
                <li><strong>markdown files</strong> - Individual page content</li>
            </ul>
        </div>
        
        <div style="margin-top: 1.5rem;">
            <h4 style="color: var(--foreground); margin-bottom: 0.75rem;">Use Cases:</h4>
            <ul style="color: var(--muted-foreground); padding-left: 1.25rem;">
                <li>Enterprise knowledge management</li>
                <li>AI-powered customer support</li>
                <li>Competitive intelligence gathering</li>
                <li>Content optimization and analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # System status
        st.markdown("---")
        st.subheader("System Status")

        docker_available = check_docker_available()
        npx_available = check_npx_available()

        status_col1, status_col2 = st.columns(2)

        with status_col1:
            if docker_available:
                st.success("✓ Docker: Available")
            else:
                st.warning("⚠ Docker: Not Available")

        with status_col2:
            if npx_available:
                st.success("✓ Node.js: Available")
            else:
                st.warning("⚠ Node.js: Not Available")


def main():
    # Initialize page state
    if 'page' not in st.session_state:
        st.session_state.page = 'landing'
    
    # Route to appropriate page
    if st.session_state.page == 'landing':
        show_landing_page()
    else:
        show_generator()


if __name__ == "__main__":
    main()