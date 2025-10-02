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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .status-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    .status-success {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    .status-error {
        background-color: #f8d7da;
        border-color: #dc3545;
        color: #721c24;
    }
    .status-info {
        background-color: #d1ecf1;
        border-color: #17a2b8;
        color: #0c5460;
    }
    .file-preview {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
        font-family: monospace;
        white-space: pre-wrap;
        max-height: 300px;
        overflow-y: auto;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #495057;
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
                text-align: center;
                padding: 4rem 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 15px;
                margin-bottom: 3rem;
            }
            .hero-title {
                font-size: 3.5rem;
                font-weight: bold;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            .hero-subtitle {
                font-size: 1.5rem;
                margin-bottom: 2rem;
                opacity: 0.95;
            }
            .feature-card {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 1.5rem;
                border-left: 4px solid #667eea;
            }
            .feature-icon {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
            .feature-title {
                font-size: 1.4rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 0.5rem;
            }
            .feature-text {
                color: #666;
                font-size: 1.1rem;
                line-height: 1.6;
            }
            .cta-section {
                text-align: center;
                padding: 3rem 2rem;
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                border-radius: 15px;
                margin: 3rem 0;
            }
            .step-number {
                display: inline-block;
                width: 40px;
                height: 40px;
                background: #667eea;
                color: white;
                border-radius: 50%;
                text-align: center;
                line-height: 40px;
                font-weight: bold;
                margin-right: 1rem;
            }
        </style>
        
        <div class="hero-section">
            <div class="hero-title">🤖 LLM-Ready Generator</div>
            <div class="hero-subtitle">Make Your Website AI-Discoverable in Minutes</div>
            <p style="font-size: 1.2rem; margin-bottom: 2rem;">
                Transform your website into LLM-ready content and boost your visibility in AI search results
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # What is it section
    st.markdown("## 🎯 What is llms.txt?")
    st.markdown("""
    **llms.txt** is the new standard for making websites easily readable by AI assistants like ChatGPT, Claude, and Perplexity.
    When users ask AI about your business, having an llms.txt file ensures your content is accurately represented.
    """)
    
    st.markdown("---")
    
    # Features
    st.markdown("## ✨ Why Use Our Generator?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Lightning Fast</div>
            <div class="feature-text">
                Generate your llms.txt file in seconds. Just enter your URL and let us do the work.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎨</div>
            <div class="feature-title">Perfectly Formatted</div>
            <div class="feature-text">
                Get clean, optimized content that LLMs can easily understand and reference.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <div class="feature-title">100% Free</div>
            <div class="feature-text">
                No signup, no credit card, no limits. Generate as many llms.txt files as you need.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How it works
    st.markdown("## 🚀 How It Works")
    
    st.markdown("""
    <div style="padding: 2rem; background: #f8f9fa; color: #333; border-radius: 10px; margin: 2rem 0;">
        <p style="font-size: 1.2rem; margin-bottom: 2rem;">
            <span class="step-number">1</span> <strong>Enter your website URL</strong> - We'll crawl your site
        </p>
        <p style="font-size: 1.2rem; margin-bottom: 2rem;">
            <span class="step-number">2</span> <strong>Wait a few seconds</strong> - Our AI processes your content
        </p>
        <p style="font-size: 1.2rem; margin-bottom: 2rem;">
            <span class="step-number">3</span> <strong>Download your files</strong> - Get llms.txt and supporting files
        </p>
        <p style="font-size: 1.2rem;">
            <span class="step-number">4</span> <strong>Upload to your site</strong> - Add llms.txt to your website root
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Benefits
    st.markdown("## 💡 Benefits for Your Business")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔍 Increased Visibility**
        - Be discovered when people ask AI about your industry
        - Stand out in AI-powered search results
        - Get accurate representation of your business
        """)
        
        st.markdown("""
        **📈 Better SEO for AI Era**
        - Future-proof your online presence
        - Optimize for the next generation of search
        - Stay ahead of competitors
        """)
    
    with col2:
        st.markdown("""
        **⚡ Save Time & Resources**
        - No manual content formatting needed
        - Automated content extraction
        - Ready to deploy in minutes
        """)
        
        st.markdown("""
        **🤝 Better AI Integration**
        - Help AI assistants understand your content
        - Provide structured data for LLMs
        - Improve accuracy of AI responses about you
        """)
    
    # CTA Section
    st.markdown("""
    <div class="cta-section">
        <h2 style="font-size: 2.5rem; margin-bottom: 1rem;">Ready to Get Started?</h2>
        <p style="font-size: 1.3rem; margin-bottom: 2rem;">
            Generate your llms.txt file now and make your website AI-ready!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Large CTA button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Launch Generator", type="primary", use_container_width=True):
            st.session_state.page = 'generator'
            st.rerun()
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p>Made with ❤️ for the AI-first web • Powered by Mdream</p>
        <p style="font-size: 0.9rem; margin-top: 1rem;">
            Questions? Contact us or check out the <a href="https://llmstxt.org" target="_blank">llms.txt documentation</a>
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
            <h1>🤖 LLM-Ready Generator</h1>
            <p>Transform any website into LLM-ready content with Mdream</p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙️ Configuration</div>', unsafe_allow_html=True)

        # URL Input
        origin_url = st.text_input(
            "🌐 Website URL",
            placeholder="https://example.com",
            help="Enter the root URL of the website to crawl"
        )

        # Output directory
        output_dir = st.text_input(
            "📁 Output Directory",
            value="./output",
            help="Directory where generated files will be saved"
        )

        # Advanced options
        with st.expander("🔧 Advanced Options"):
            include_patterns = st.text_input(
                "✅ Include Patterns (CSV)",
                placeholder="docs,faq,pricing",
                help="Comma-separated list of path patterns to include"
            )

            exclude_patterns = st.text_input(
                "❌ Exclude Patterns (CSV)",
                placeholder="login,cart,admin",
                help="Comma-separated list of path patterns to exclude"
            )

            use_playwright = st.checkbox(
                "🎭 Use Playwright",
                value=False,
                help="Use Playwright for better JavaScript rendering"
            )

            max_pages = st.slider(
                "📄 Max Pages",
                min_value=10,
                max_value=1000,
                value=100,
                help="Maximum number of pages to crawl"
            )

            timeout = st.slider(
                "⏱️ Timeout (seconds)",
                min_value=60,
                max_value=600,
                value=300,
                help="Timeout for the crawling process"
            )

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🚀 Generate LLM-Ready Content")

        if st.button("🎯 Start Generation", type="primary", use_container_width=True):
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
        st.subheader("📥 Download Results")

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
        st.subheader("📖 How to Use")

        st.markdown("""
        **🎯 Quick Start:**
        1. Enter the website URL you want to crawl
        2. Configure options in the sidebar (optional)
        3. Click "Start Generation"
        4. Wait for completion (progress shown above)
        5. Download your LLM-ready files

        **📁 Generated Files:**
        - `llms.txt` - Concise summary for LLMs
        - `llms-full.txt` - Complete content with metadata
        - `manifest.json` - Generation metadata
        - `md/` - Individual markdown files

        **🤖 Ready for LLMs:**
        Feed the generated content to ChatGPT, Claude, or other LLMs for:
        - Company research
        - Content analysis
        - Q&A about the website
        - Documentation search
        """)

        # System status
        st.markdown("---")
        st.subheader("🔧 System Status")

        docker_available = check_docker_available()
        npx_available = check_npx_available()

        status_col1, status_col2 = st.columns(2)

        with status_col1:
            if docker_available:
                st.success("🐳 Docker: Available (Recommended)")
            else:
                st.warning("🐳 Docker: Not available")

        with status_col2:
            if npx_available:
                st.success("📦 npx: Available (Fallback)")
            else:
                st.warning("📦 npx: Not available")


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